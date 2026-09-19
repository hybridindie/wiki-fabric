#!/usr/bin/env python3
# extract_backends.py — Claim-extraction layer: prompt building, LLM backends,
# JSON parsing/repair, and post-extraction locator verification.
#
# Split out of ingest.py (which had grown into a monolith: config plumbing +
# 4 extraction backends + frontmatter writing + 3 CLI modes). ingest.py keeps
# the evidence-fabric concerns (source records, anti-loop, registry); this
# module owns everything between "raw source text" and "structured claims".
#
# Consumers: ingest.py (primary), synthesize.py (llm_config + backends),
# eval.py (extract_claims). All import paths here are standalone-runnable:
# this module only depends on fabric_config + local_llm.

import os
import re
import sys
import json
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import (get_config, get_llm_config, ensure_local_model,
                           get_local_model)

# === Prompt ===

CLAIM_PROMPT = """Extract atomic evidence-backed claims from the line-numbered source below.

For each claim output one JSON object: {{"s":"statement","loc":"L<start>[-L<end>]","q":"exact quote from source","ev":"primary|secondary|tertiary","conf":"high|medium|low","st":"supported|proposed|contested"}}

Rules:
- "loc" = the L-number range where the quote text appears; must match the first and last line of the quoted text exactly
- "q" = verbatim substring of the source (do NOT include the L-number prefixes in "q")
- ev=primary only for direct measurement, secondary for reported, tertiary for hearsay
- conf reflects corroboration; st=supported when quoted evidence exists, proposed otherwise
- Granularity: exactly ONE distinct verifiable fact per claim — a measurable property,
  mechanism, or constraint, expressed in one sentence. Do NOT split one fact into
  sub-facts (e.g. "X costs A and takes B" is one claim). Do NOT merge unrelated facts.
- Target 5-12 claims for a document this size; prefer fewer, well-formed claims over
  many fragments.
- Output ONLY the JSON array, no other text.

Source: {source_path}
{numbered_text}"""

# Mapping from compact keys to schema keys for claim frontmatter
CLAIM_KEY_MAP = {
    "s": "statement",
    "loc": "locator",
    "q": "quote",
    "ev": "evidence_strength",
    "conf": "confidence",
    "st": "status",
}


def number_lines(text, max_chars=15000):
    """Prefix each line with L<n>: so the LLM can cite line ranges."""
    lines = text[:max_chars].split('\n')
    return '\n'.join(f"L{i+1}:{line}" for i, line in enumerate(lines))


def build_prompt(source_text, source_path):
    return CLAIM_PROMPT.format(
        source_path=source_path,
        numbered_text=number_lines(source_text)
    )


def llm_config(compiler=False):
    """Read LLM config from fabric.yaml + env overrides. compiler=True routes to
    the policy-designated compiler model (claim extraction = compiler work)."""
    return get_llm_config(get_config(), compiler=compiler)


# === Quote/locator repair ===

def _normalize_for_match(text):
    """Strip markdown artifacts + collapse whitespace for fuzzy quote matching."""
    t = re.sub(r'[*`>]+', '', text)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def repair_quote(quote, source_text):
    """Fuzzy-match a model-returned quote back to the verbatim source text.

    Models strip markdown artifacts and join lines. If the normalized quote
    matches the normalized source, return the true verbatim substring.
    Returns (repaired_quote, True) or (original, False)."""
    if not quote or not quote.strip():
        return quote, False
    src_norm = _normalize_for_match(source_text)
    q_norm = _normalize_for_match(quote)
    if not q_norm:
        return quote, False
    # exact verbatim already
    if quote in source_text:
        return quote, False
    # fuzzy match: find the quote's position in the normalized source
    idx = src_norm.find(q_norm)
    if idx == -1:
        # try with the first 60% of the quote (model may have truncated)
        idx = src_norm.find(q_norm[:int(len(q_norm) * 0.6)])
    if idx == -1:
        return quote, False
    # char-map of the normalized source back to raw offsets
    norm_chars = []
    norm_to_raw = []
    for j, ch in enumerate(source_text):
        if ch in '*`>':
            continue
        if ch in '\n\r\t':
            ch = ' '
        norm_chars.append(ch)
        norm_to_raw.append(j)
    src_flat = ''.join(norm_chars)
    # collapse double spaces in the flat source
    flat_final, flat_map = [], []
    prev_space = False
    for ch, raw_i in zip(src_flat, norm_to_raw):
        if ch == ' ' and prev_space:
            continue
        flat_final.append(ch)
        flat_map.append(raw_i)
        prev_space = (ch == ' ')
    flat_str = ''.join(flat_final)
    pos = flat_str.find(q_norm)
    if pos == -1:
        return quote, False
    raw_start = flat_map[pos]
    raw_end = flat_map[min(pos + len(q_norm) - 1, len(flat_map) - 1)]
    # extend to include closing md artifact chars
    while raw_end < len(source_text) - 1 and source_text[raw_end + 1] in '*`':
        raw_end += 1
    verbatim = source_text[raw_start:raw_end + 1].strip()
    if len(verbatim) < 10:
        return quote, False
    return verbatim, True


def verify_and_fix_locators(claims, source_text):
    """Post-extraction: verify each claim's locator against the source and fix if off.
    Also repairs quotes that were markdown-normalized by the model back to the
    true verbatim text. Works on the flat claim structure."""
    source_lines = source_text.split('\n')
    fixed = 0
    for claim in claims:
        quote = claim.get("quote", "") or claim.get("q", "") or ""
        if quote and quote not in source_text:
            repaired, did = repair_quote(quote, source_text)
            if did and repaired != quote:
                claim["quote"] = repaired
                if "q" in claim:
                    claim["q"] = repaired
        quote = claim.get("quote", "") or claim.get("q", "") or ""
        loc = claim.get("locator", "") or claim.get("loc", "") or ""

        # Strip L-prefixes from quote for searching
        q_clean = re.sub(r'L\d+:', '', quote).strip()
        if not q_clean:
            continue

        # Search for the quote in the source (normalized)
        q_norm = re.sub(r'[*`>\n]', '', q_clean).strip()
        best_start = None
        best_end = None

        head = q_norm[:30]
        if not head:
            continue
        for i in range(len(source_lines)):
            window = re.sub(r'[*`>\n]', '', ' '.join(source_lines[i:i+3])).strip()
            if head in window:
                best_start = i + 1
                break
        if best_start is None:
            continue

        tail = q_norm[-30:]
        for j in range(best_start - 1, len(source_lines)):
            window = re.sub(r'[*`>\n]', '', ' '.join(source_lines[best_start - 1:j + 1])).strip()
            if tail in window:
                best_end = j + 1
                break

        if best_end is None:
            best_end = best_start

        correct_loc = f"L{best_start}" if best_end == best_start else f"L{best_start}-L{best_end}"
        current_loc = claim.get("locator", "") or claim.get("loc", "")
        if current_loc != correct_loc:
            claim["locator"] = correct_loc
            fixed += 1

    if fixed:
        print(f"  Fixed {fixed} locators via source verification", file=sys.stderr)
    return claims


# === JSON parsing/repair ===

def _json_repair_load(cand):
    """Tolerant fallback: fix the common model artifact of unescaped quotes inside
    string values (code fragments like `{"msg": "x"}`) by escaping stray quotes
    per-string. No new dependencies."""
    fixed = []
    i, n = 0, len(cand)
    while i < n:
        if cand[i] == "{":
            depth, j, in_str, esc = 0, i, False, False
            while j < n:
                ch = cand[j]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                else:
                    if ch == '"':
                        in_str = True
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            break
                j += 1
            obj_text = cand[i:j + 1]
            try:
                fixed.append(json.loads(obj_text))
                i = j + 1
                continue
            except json.JSONDecodeError:
                patched = []
                k = 0
                while k < len(obj_text):
                    ch = obj_text[k]
                    if ch == "\\":
                        patched.append(obj_text[k:k + 2]); k += 2; continue
                    patched.append(ch); k += 1
                try:
                    fixed.append(json.loads("".join(patched)))
                except json.JSONDecodeError:
                    pass
                i = j + 1
                continue
        i += 1
    return fixed


def parse_json_array(text):
    """Extract the first JSON array from LLM output and normalize keys.
    Tolerates model artifacts (unescaped quotes in code fragments) via repair."""
    if not text:
        return None
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if not m:
        return None
    try:
        raw = json.loads(m.group())
    except json.JSONDecodeError:
        raw = _json_repair_load(m.group())  # tolerant fallback
    if not isinstance(raw, list):
        raw = [r for r in (raw if isinstance(raw, list) else []) if isinstance(r, dict)]
    if not raw:
        return None
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        claim = {}
        for k, v in item.items():
            claim[CLAIM_KEY_MAP.get(k, k)] = v
        out.append(claim)
    return out


# === Backends ===

def extract_claims_mlx(source_text, source_path, model=None):
    """On-device backend (no server). Bypasses Ollama entirely — no per-request
    model eviction, no serialization queue. Backend is picked from the model
    id by local_llm: mlx-lm (Apple Silicon, mlx-community/*) or llama-cpp
    (cross-platform, GGUF).

    Activated by WIKI_LLM_BACKEND=mlx, or a model id that looks on-device
    (see fabric_config.looks_like_local_model). Default model: llm.local_model
    from fabric.yaml (platform default: gemma-4-e4b MLX on Apple Silicon, GGUF
    elsewhere).
    """
    mlx_model = model or os.environ.get("WIKI_MLX_MODEL") or get_local_model()
    # Offer to download the local model when missing (human-gated, once per
    # process; main() front-loads this before workers when routing is known).
    global _ENSURE_DONE
    if not _ENSURE_DONE:
        _ENSURE_DONE = True
        ensure_local_model(mlx_model)
    try:
        from local_llm import generate as local_generate
    except Exception as e:
        print(f"local backend unavailable: {e}", file=sys.stderr)
        return []

    raw = build_prompt(source_text, source_path)
    for budget in (4096, 6144):
        try:
            out = local_generate(raw, mlx_model, max_tokens=budget)
            claims = parse_json_array(out)
            if claims:
                return claims
            print(f"No JSON array in local output (max_tokens={budget})", file=sys.stderr)
        except Exception as e:
            print(f"local extraction failed (max_tokens={budget}): {e}", file=sys.stderr)
            break  # backend/model-level failure: retrying a higher budget won't help
    return []


_ENSURE_DONE = False


def extract_claims_openai_compatible(source_text, source_path, model=None):
    """Primary: OpenAI-compatible endpoint (Ollama, OpenAI, vLLM, LM Studio, etc.)."""
    try:
        import openai
    except ImportError:
        print("openai package not installed; skipping", file=sys.stderr)
        return []

    cfg = llm_config(compiler=True)
    # Only auto-map model names for Ollama (its /v1 endpoint requires the
    # model name in the path). Other providers (vLLM, LM Studio, OpenRouter)
    # accept any model name the server recognizes.
    if model is None:
        model = cfg["model"]
    model_name = model
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                           timeout=float(os.environ.get("WIKI_LLM_TIMEOUT", "600")))
    try:
        def _call(max_tokens, extra=None):
            messages = [
                {"role": "system", "content": "You are a precise claim extractor. Extract atomic, evidence-backed claims from source documents. Return ONLY a valid JSON array."},
                {"role": "user", "content": build_prompt(source_text, source_path)},
            ] + (extra or [])
            return client.chat.completions.create(
                model=model_name, temperature=0.1, max_tokens=max_tokens, messages=messages)

        response = _call(16384)
        msg = response.choices[0].message
        # Reasoning models (deepseek etc.) may put the answer in `content` only,
        # or spend the budget on `reasoning` — if no parseable JSON came back and
        # the model emitted reasoning, retry once demanding direct JSON output.
        output = msg.content or getattr(msg, "reasoning", None) or ""
        claims = parse_json_array(output)
        if not claims and response.choices[0].finish_reason == "length":
            response = _call(8192, extra=[{"role": "assistant", "content": output[:2000] if output else ""},
                                          {"role": "user", "content": "Your reasoning consumed the token budget. Return the JSON array NOW, no explanations."}])
            msg = response.choices[0].message
            output = msg.content or getattr(msg, "reasoning", None) or ""
            claims = parse_json_array(output)
        if claims:
            return claims
        print("No JSON array in OpenAI-compatible response", file=sys.stderr)
    except Exception as e:
        print(f"OpenAI-compatible extraction failed: {e}", file=sys.stderr)
    return []


def extract_claims_anthropic(source_text, source_path, model=None):
    """Fallback 1: Anthropic SDK."""
    try:
        import anthropic
    except ImportError:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return []
    model_map = {
        "sonnet": "claude-3-5-sonnet-20241022",
        "opus": "claude-3-opus-20240229",
        "haiku": "claude-3-haiku-20240307",
    }
    model_name = model_map.get(model, model)
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model_name,
            max_tokens=4096,
            temperature=0.1,
            system="You are a precise claim extractor. Extract atomic, evidence-backed claims from source documents. Return ONLY a valid JSON array.",
            messages=[{"role": "user", "content": build_prompt(source_text, source_path)}]
        )
        output = response.content[0].text
        claims = parse_json_array(output)
        if claims:
            return claims
    except Exception as e:
        print(f"Anthropic extraction failed: {e}", file=sys.stderr)
    return []


def extract_claims_opencode(source_text, source_path, model):
    """Fallback 2: opencode CLI."""
    prompt = build_prompt(source_text, source_path)
    try:
        result = subprocess.run(
            ["opencode", "run", "--model", model, prompt],
            capture_output=True,
            text=True,
            timeout=180
        )
        claims = parse_json_array(result.stdout)
        if claims:
            return claims
        if result.returncode != 0:
            print(f"opencode failed: {result.stderr[:200]}", file=sys.stderr)
    except Exception as e:
        print(f"opencode extraction error: {e}", file=sys.stderr)
    return []


def extract_claims(source_text, source_path, model=None):
    """Extract claims routing: explicit model > WIKI_LLM_BACKEND > compiler chain.

    Spending policy (docs/AGENTS.md: tokens are spent on extraction, never on
    retrieval):
      default            -> compiler_model from fabric.yaml (cloud: fast, ~20s/doc)
      WIKI_LLM_BACKEND=mlx -> on-device backend (local_llm: mlx-lm / llama-cpp GGUF)
      on-device model id  -> explicit local model (looks_like_local_model)
    """
    from fabric_config import looks_like_local_model
    if not model:
        model = os.environ.get("WIKI_LLM_MODEL")
    if os.environ.get("WIKI_LLM_BACKEND", "").lower() == "mlx" or looks_like_local_model(model):
        claims = extract_claims_mlx(source_text, source_path, model)
        if claims:
            return verify_and_fix_locators(claims, source_text)
        print("local backend returned nothing; falling back to OpenAI-compatible...", file=sys.stderr)
    claims = extract_claims_openai_compatible(source_text, source_path, model)
    if not claims:
        print("Falling back to Anthropic...", file=sys.stderr)
        claims = extract_claims_anthropic(source_text, source_path, model)
    if not claims:
        print("Falling back to opencode...", file=sys.stderr)
        claims = extract_claims_opencode(source_text, source_path, model or "sonnet")
    if claims:
        claims = verify_and_fix_locators(claims, source_text)
    return claims