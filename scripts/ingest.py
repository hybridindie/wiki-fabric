#!/usr/bin/env python3
# ingest.py — Ingest a raw source into the evidence fabric
#
# Usage: python3 scripts/ingest.py <source-path> [--project PROJECT] [--dry-run] [--extract-claims]
#
# LLM configuration (env vars):
#   WIKI_LLM_BASE_URL   — OpenAI-compatible base URL (default: http://localhost:11434/v1 for Ollama)
#   WIKI_LLM_API_KEY    — API key (default: "ollama"; Ollama ignores it)
#   WIKI_LLM_MODEL      — model name (default: qwen2.5-coder:7b)

import sys
import os
import time
import re
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import get_config, FABRIC_ROOT, get_llm_config, actor

VAULT_ROOT = FABRIC_ROOT

import threading as _threading
_LOG_LOCK = _threading.Lock()


def _dt_iso():
    """ISO-8601 instant with UTC offset (OKF §5: every timestamp has explicit offset)."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


args_dry_run = False


def sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def find_project_namespace(vault_root):
    overlay_path = vault_root / ".wiki-overlay.md"
    if not overlay_path.exists():
        return "default-project"
    text = overlay_path.read_text()
    m = re.search(r"namespace:\s*(\S+)", text)
    return m.group(1) if m else "default-project"


def llm_config(compiler=False):
    """Read LLM config from fabric.yaml + env overrides. compiler=True routes to
    the policy-designated compiler model (claim extraction = compiler work)."""
    from fabric_config import get_llm_config
    return get_llm_config(get_config(), compiler=compiler)


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


def verify_and_fix_locators(claims, source_text):
    """Post-extraction: verify each claim's locator against the source and fix if off.
    Works on the flat claim structure (locator, quote at top level)."""
    source_lines = source_text.split('\n')
    fixed = 0
    for claim in claims:
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

        # Try to find the first 30 chars of the quote in consecutive lines
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

        # Find end by searching for the tail
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


def _json_repair_load(cand):
    """Tolerant fallback: fix the common model artifact of unescaped quotes inside
    string values (code fragments like `{"msg": "x"}`) by escaping stray quotes
    per-string. No new dependencies."""
    fixed = []
    # scan top-level objects with brace matching, ignoring strings
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
                # escape unescaped inner quotes that break parsing: naive pass —
                # quote any '"' not already preceded by backslash and not a
                # structural quote (keys/values boundaries). Heuristic: escape
                # quotes that appear inside `{...}` or `...` spans of values.
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
    # Normalize compact keys -> full keys
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        claim = {}
        for k, v in item.items():
            claim[CLAIM_KEY_MAP.get(k, k)] = v
        out.append(claim)
    return out


def extract_claims_mlx(source_text, source_path, model=None):
    """Direct mlx-lm backend (Apple Silicon, no server). Bypasses Ollama
    entirely - no per-request model eviction, no serialization queue.

    Activated by WIKI_LLM_BACKEND=mlx (or model containing '/' pointing at a
    local/HF mlx model dir). Default model: mlx-community/Qwen3.8-27B-4bit.
    """
    import os
    try:
        from mlx_lm import load, generate
    except ImportError:
        print("mlx-lm not installed; skipping (pip install mlx-lm)", file=sys.stderr)
        return []

    mlx_model = model or os.environ.get("WIKI_MLX_MODEL", "mlx-community/Qwen3.8-27B-4bit")
    global _MLX_MODEL_CACHE
    try:
        if _MLX_MODEL_CACHE[0] != mlx_model:
            t0 = time.time()
            _MLX_MODEL_CACHE = (mlx_model, *load(mlx_model))
            print(f"mlx: loaded {mlx_model} in {time.time()-t0:.0f}s", file=sys.stderr)
    except NameError:
        t0 = time.time()
        _MLX_MODEL_CACHE = (mlx_model, *load(mlx_model))
        print(f"mlx: loaded {mlx_model} in {time.time()-t0:.0f}s", file=sys.stderr)

    _, _m, _tok = _MLX_MODEL_CACHE
    raw = build_prompt(source_text, source_path)
    # qwen3_5 chat template hardcodes xhigh reasoning when no system message is
    # present; the reasoning_effort kwarg is the supported knob (xhigh|medium|low).
    try:
        prompt = _tok.apply_chat_template(
            [{"role": "user", "content": raw}],
            tokenize=False, add_generation_prompt=True,
            reasoning_effort=os.environ.get("WIKI_MLX_REASONING", "low"),
        )
    except Exception:
        prompt = raw
    for budget in (4096, 6144):
        try:
            out = generate(_m, _tok, prompt=prompt, max_tokens=budget, verbose=False)
            claims = parse_json_array(out)
            if claims:
                return claims
            print(f"No JSON array in mlx output (max_tokens={budget})", file=sys.stderr)
        except Exception as e:
            print(f"mlx extraction failed (max_tokens={budget}): {e}", file=sys.stderr)
    return []

def extract_claims_openai_compatible(source_text, source_path, model=None):
    """Primary: OpenAI-compatible endpoint (Ollama, OpenAI, vLLM, LM Studio, etc.)."""
    import os
    try:
        import openai
    except ImportError:
        print("openai package not installed; skipping", file=sys.stderr)
        return []

    cfg = llm_config(compiler=True)
    # Map generic names to local models only when using the Ollama default
    if model is None and "11434" in cfg["base_url"]:
        model = cfg["model"]
    model_name = model or cfg["model"]
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
    import os
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
      default          -> compiler_model from fabric.yaml (cloud: fast, ~20s/doc)
      WIKI_LLM_BACKEND=mlx -> local mlx-lm (offline, privacy, no GPU-server wedge)
      model contains / -> explicit mlx model path
    """
    import os as _os
    if not model:
        model = _os.environ.get("WIKI_LLM_MODEL")
    if _os.environ.get("WIKI_LLM_BACKEND", "").lower() == "mlx" or (model and "/" in model and not model.startswith("http")):
        claims = extract_claims_mlx(source_text, source_path, model)
        if claims:
            claims = verify_and_fix_locators(claims, source_text)
            return claims
        print("mlx backend returned nothing; falling back to OpenAI-compatible...", file=sys.stderr)
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


# Alias: the ingest_source() parameter `extract_claims` (bool) shadows this
# function within that scope, so the function is referenced via the alias.
extract_claims_fn = extract_claims


def clean_quote(quote):
    """Strip L<n>: line-number prefixes that the LLM may have copied from the numbered source."""
    if not quote:
        return ""
    # Remove leading L<n>: from the start and any mid-quote L<n>: artifacts
    cleaned = re.sub(r'L\d+:', '', quote)
    # Collapse whitespace artifacts from removed prefixes
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned


def _yaml_scalar(value):
    """Emit a YAML-safe inline double-quoted scalar for LLM-derived free text.

    Hand-escaping breaks on model artifacts (literal backslash-escaped quotes
    inside already-decoded JSON strings land as `\\"` and break the block
    mapping). Build the double-quoted form explicitly: backslash, double
    quote, and control chars are the only characters that need escaping in
    YAML double-quoted style; everything else passes through literally.
    """
    s = str(value or "")
    out = s.replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\n", "\\n").replace("\r", "").replace("\t", "\\t")
    return f'"{out}"'


def claim_frontmatter(claim, source_slug, idx):
    quote = clean_quote(claim.get('quote', ''))
    statement = claim.get('statement', '')
    return f"""---
type: claim
id: claim-{source_slug}-{idx:03d}
statement: {_yaml_scalar(statement)}
description: {_yaml_scalar(statement[:140])}
resource: "[[src-{source_slug}]]"
generated: {{ by: "{actor(get_config(), 'agent')}", at: "{_dt_iso()}" }}
verified:
  - by: "{actor(get_config(), 'process', model='locator-verification')}"
    at: "{_dt_iso()}"
status: {claim.get('st', claim.get('status', 'proposed'))}
confidence: {claim.get('conf', claim.get('confidence', 'medium'))}
evidence_strength: {claim.get('ev', claim.get('evidence_strength', 'primary'))}
source_refs:
  - source: "[[src-{source_slug}]]"
    locator: {_yaml_scalar(claim.get('loc', claim.get('locator', 'N/A')))}
    quote: {_yaml_scalar(quote)}
    supports: true
last_verified: {date.today().isoformat()}
relations: []
---

# claim-{source_slug}-{idx:03d}

{statement}
"""


def is_already_ingested(source_path, file_hash):
    """Check if a source record with this sha256 already exists (anti-loop)."""
    sources_dir = VAULT_ROOT / "evidence" / "sources"
    if not sources_dir.exists():
        return False
    for rec in sources_dir.glob("src-*.md"):
        if re.search(rf"sha256:\s*{re.escape(file_hash)}", rec.read_text(encoding="utf-8", errors="replace")):
            return rec
    return None


def find_pending_sources(project_slug):
    """Return raw files whose source record is status: pending (recorded but
    never claim-extracted). Complements find_changed_sources: --changed handles
    NEW/CHANGED files, --pending handles recorded-but-unextracted ones without
    tripping the anti-loop."""
    raw_dir = VAULT_ROOT / "evidence" / "raw" / project_slug
    if not raw_dir.exists():
        return []
    pending_paths = set()
    sources_dir = VAULT_ROOT / "evidence" / "sources"
    if sources_dir.exists():
        for rec in sources_dir.glob("src-*.md"):
            text = rec.read_text(encoding="utf-8", errors="replace")
            if "status: pending" not in text:
                continue
            m = re.search(r"source_path:\s*(.+)", text)
            if not m:
                continue
            sp = m.group(1).strip()
            # Scope to this project's raw subtree
            if f"evidence/raw/{project_slug}/" in sp or f"evidence/raw/{project_slug}/" in sp.replace("_", "-"):
                pending_paths.add(sp)
    pending = []
    for rel in sorted(pending_paths):
        f = VAULT_ROOT / rel
        if f.exists():
            pending.append(f)
    return pending


def find_changed_sources(project_slug):
    """Return raw files that are NEW or CHANGED vs. their source records.

    Compares each file under evidence/raw/<slug>/ against every sha256 recorded
    in evidence/sources/. A file with no matching hash is new or changed.
    """
    raw_dir = VAULT_ROOT / "evidence" / "raw" / project_slug
    if not raw_dir.exists():
        return []
    known_hashes = set()
    sources_dir = VAULT_ROOT / "evidence" / "sources"
    if sources_dir.exists():
        for rec in sources_dir.glob("src-*.md"):
            m = re.search(r"sha256:\s*([a-f0-9]{64})", rec.read_text(encoding="utf-8", errors="replace"))
            if m:
                known_hashes.add(m.group(1))
    changed = []
    for f in sorted(raw_dir.rglob("*.md")):
        if sha256(f) not in known_hashes:
            changed.append(f)
    return changed


def ingest_source(source_path, extract_claims=False, model=None, dry_run=False, namespace=None):
    """Ingest one source file. `extract_claims` is a bool flag (shadows the module
    function of the same name inside this scope, hence the alias below)."""
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}", file=sys.stderr)
        return False

    file_hash = sha256(source_path)
    print(f"Source: {source_path}")
    print(f"SHA256: {file_hash}")

    # Anti-loop: skip sources already ingested with the same hash — except
    # sources recorded with status: pending (never claim-extracted). Those are
    # completed by --pending mode: claims extracted, record flipped to ingested.
    existing = is_already_ingested(source_path, file_hash)
    resuming = False
    if existing:
        rec_text = existing.read_text(encoding="utf-8", errors="replace")
        if "status: pending" in rec_text:
            resuming = True
            print(f"Resuming pending source {existing.name}")
        else:
            print(f"Skipped — already ingested as {existing.name} (matching sha256)")
            return False

    namespace = namespace or find_project_namespace(Path.cwd())
    print(f"Project namespace: {namespace}")

    try:
        rel_path = source_path.relative_to(VAULT_ROOT / "evidence" / "raw")
        source_slug = slugify(rel_path.as_posix())
    except ValueError:
        source_slug = slugify(source_path.name)
    source_slug = source_slug[:80]

    source_record_path = VAULT_ROOT / "evidence" / "sources" / f"src-{source_slug}.md"
    summary_path = VAULT_ROOT / "evidence" / "source-summaries" / f"sum-{source_slug}.md"
    change_dir = VAULT_ROOT / "evidence" / "traces" / "change-sets" / f"{date.today().isoformat()}-{source_slug}"

    print(f"\nSource record: {source_record_path}")
    print(f"Source summary: {summary_path}")
    print(f"Change-set: {change_dir}/")

    if args_dry_run:
        print("  (dry run — no files written)")
        return True

    # 1. Source record (skipped when resuming a pending source — it exists)
    title = source_path.stem.replace('-', ' ').replace('_', ' ').title()
    (VAULT_ROOT / "evidence" / "sources").mkdir(parents=True, exist_ok=True)
    if resuming:
        print("  (resuming — source record exists)")
    else:
        _actor = actor(get_config(), "agent")
        source_record_path.write_text(f"""---
type: source
title: {title}
description: "Captured upstream source: {title.lower()}"
generated: {{ by: "{_actor}", at: "{_dt_iso()}" }}
tags: []
resource: "evidence/raw/{source_path.relative_to(VAULT_ROOT / 'evidence' / 'raw').as_posix() if 'evidence/raw' in str(source_path) else source_path.name}"
source_path: evidence/raw/{source_path.relative_to(VAULT_ROOT / 'evidence' / 'raw').as_posix() if 'evidence/raw' in str(source_path) else source_path.name}
sha256: {file_hash}
captured: {date.today().isoformat()}
summary: "[[sum-{source_slug}]]"
status: pending
---

# {title}

Captured from `{source_path}` on {date.today().isoformat()}.

Faithful summary: [[sum-{source_slug}]].
""")

    # 2. Extract claims (optional)
    claims = []
    if extract_claims:
        print("Extracting claims via LLM...")
        source_text = source_path.read_text(encoding="utf-8", errors="replace")
        claims = extract_claims_fn(source_text, str(source_path), model)
        if claims:
            print(f"Extracted {len(claims)} claims")
        else:
            print("No claims extracted", file=sys.stderr)

    # 3. Write claim files
    (VAULT_ROOT / "evidence" / "claims").mkdir(parents=True, exist_ok=True)
    for i, claim in enumerate(claims):
        claim_path = VAULT_ROOT / "evidence" / "claims" / f"claim-{source_slug}-{i:03d}.md"
        claim_path.write_text(claim_frontmatter(claim, source_slug, i))
        print(f"  Claim {i+1}: {claim_path}")

    # 4. Summary
    (VAULT_ROOT / "evidence" / "source-summaries").mkdir(parents=True, exist_ok=True)
    claim_lines = "\n".join(
        f"- {c.get('statement', c.get('s', ''))[:80]} (locator: {c.get('locator', c.get('loc', 'N/A'))})"
        for c in claims
    ) if claims else "- claim 1 (locator)"

    if not resuming:
        _actor = actor(get_config(), "agent")
        summary_path.write_text(f"""---
type: source-summary
title: {title} — Summary
description: "Faithful summary of {source_path.name} with line locators"
generated: {{ by: "{_actor}", at: "{_dt_iso()}" }}
tags: []
source: "[[src-{source_slug}]]"
status: pending
created: {date.today().isoformat()}
---

# Summary

Faithful summary of {source_path.name}.

## Key claims

{claim_lines or '- claim 1 (locator)'}
""")

    # 4b. Resume: flip the source record to ingested once claims exist
    if resuming:
        rec = source_record_path.read_text(encoding="utf-8", errors="replace")
        rec = rec.replace("status: pending", "status: ingested")
        source_record_path.write_text(rec)

    # 5. Change-set
    Path(change_dir).mkdir(parents=True, exist_ok=True)
    change_set_id = f"change-set-{date.today().isoformat()}-{source_slug}"
    created_files = [f"evidence/sources/src-{source_slug}.md",
                     f"evidence/source-summaries/sum-{source_slug}.md"]
    created_files += [f"evidence/claims/claim-{source_slug}-{i:03d}.md" for i in range(len(claims))]

    change_dir.joinpath("manifest.md").write_text(f"""---
type: change-set
id: {change_set_id}
title: "Ingest {source_path.name}"
date: {date.today().isoformat()}
status: open
scope: staging
---

# Change-Set: {source_path.name}

## Sources processed

| Source | raw file | sha256 | record |
|---|---|---|---|
| {source_path.name} | `evidence/raw/{source_path.relative_to(VAULT_ROOT / 'evidence' / 'raw').as_posix() if 'evidence/raw' in str(source_path) else source_path.name}` | `{file_hash[:12]}...` | `src-{source_slug}` |

## Pages created (staging)

""" + "\n".join(f"- `{f}`" for f in created_files) + f"""

## New claims

""" + ("\n".join(f"- {c.get('statement', c.get('s', ''))[:80]}" for c in claims) if claims else "_(none extracted)_") + f"""

## Lint

- Run: `python3 scripts/lint.py .`

## Log

`registry/log.md` → `## {date} / **ingest | <slug>**`
""")

    change_dir.joinpath("diff.md").write_text(f"""---
type: change-set-diff
title: "Diff for {source_path.name}"
date: {date.today().isoformat()}
parent: "[[{change_set_id}]]"
---

# Diff: {source_path.name}

## + created (staging)
```
""" + "\n".join(f"+ {f}" for f in created_files) + "\n```\n")

    print("Created source record, summary, change-set manifest and diff")

    # 6. Log
    log_path = VAULT_ROOT / "registry" / "log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(
            "---\ntype: log\ntitle: Log\ncreated: {d}\nupdated: {d}\n---\n\n# Log\n\nAppend-only timeline.\n".replace("{d}", date.today().isoformat())
        )
    with _LOG_LOCK, open(log_path, "a") as f:
        f.write(f"\n## {date.today().isoformat()}\n* **ingest | {source_slug}**\n")
        f.write(f"- Ingested {source_path.name} (sha256 {file_hash[:12]}...)\n")
        f.write(f"- Extracted {len(claims)} claims\n")
        f.write(f"- Change-set: {change_dir}\n")

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest a raw source into the evidence fabric")
    parser.add_argument("source", nargs="?", help="Path to source file under evidence/raw/")
    parser.add_argument("--changed", metavar="PROJECT", help="Ingest all NEW/CHANGED raw files for a project slug (vs. recorded sha256s)")
    parser.add_argument("--pending", metavar="PROJECT", help="Claim-extract all recorded-but-pending sources for a project slug (anti-loop safe)")
    parser.add_argument("--project", help="Project namespace (from .wiki-overlay.md)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing")
    parser.add_argument("--extract-claims", action="store_true", help="Extract claims using LLM")
    parser.add_argument("--model", default=None, help="LLM model (default: $WIKI_LLM_MODEL or qwen2.5-coder:7b)")
    parser.add_argument("--workers", type=int, default=int(os.environ.get("WIKI_INGEST_WORKERS", "1")),
                        help="Concurrent extraction threads (default 1; cloud tiers tolerate 6-12)")
    args = parser.parse_args()

    global args_dry_run
    args_dry_run = args.dry_run

    if args.pending:
        project = args.pending
        pending = find_pending_sources(project)
        if not pending:
            print(f"No pending sources for {project} — nothing to extract")
            return
        print(f"=== Claim-extracting {len(pending)} pending sources for {project} "
              f"(workers: {args.workers}) ===\n")
        if args.workers <= 1 or args.dry_run:
            results = []
            for f in pending:
                print(f"--- {f.name} ---")
                results.append(ingest_source(f, args.extract_claims, args.model, args.dry_run, args.project or project))
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            results = []
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                futs = {ex.submit(ingest_source, f, args.extract_claims, args.model,
                                  args.dry_run, args.project or project): f
                        for f in pending}
                for fut in as_completed(futs):
                    print(f"--- done: {futs[fut].name} ---", flush=True)
                    results.append(fut.result())
        ingested = sum(1 for r in results if r)
        print(f"\nIngest summary: {ingested} ingested, {len(results) - ingested} skipped")
        return

    if args.changed:
        project = args.changed
        changed = find_changed_sources(project)
        if not changed:
            print(f"No new or changed sources under evidence/raw/{project}/ — nothing to ingest")
            return
        print(f"=== Ingesting {len(changed)} new/changed sources for {project} "
              f"(workers: {args.workers}) ===\n")
        if args.workers <= 1 or args.dry_run:
            results = []
            for f in changed:
                print(f"--- {f.name} ---")
                results.append(ingest_source(f, args.extract_claims, args.model, args.dry_run, args.project or project))
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            results = []
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                futs = {ex.submit(ingest_source, f, args.extract_claims, args.model,
                                  args.dry_run, args.project or project): f
                        for f in changed}
                for fut in as_completed(futs):
                    print(f"--- done: {futs[fut].name} ---", flush=True)
                    results.append(fut.result())
        ingested = sum(1 for r in results if r)
        print(f"\nIngest summary: {ingested} ingested, {len(results) - ingested} skipped")
        return

    if not args.source:
        parser.error("provide a source path, or use --changed <project-slug>")

    source_path = Path(args.source)
    if not source_path.is_absolute():
        if "evidence/raw" in str(source_path):
            source_path = VAULT_ROOT / source_path
        else:
            source_path = VAULT_ROOT / "evidence" / "raw" / source_path

    ok = ingest_source(source_path, args.extract_claims, args.model, args.dry_run, args.project)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()