#!/usr/bin/env python3
# mine-chats.py — Distill captured chat transcripts into durable knowledge:
# patterns, anti-patterns, workflows, constraints, decisions — with explicit
# transient filtering (CI states, PR counts, "as of today" snapshots are LOW
# value and skipped).
#
# Modes:
#   --llm     : LLM distillation per session (compiler model, 1 call/session)
#   default   : heuristic classification only, 0 tokens
#
# Output (both modes): a chat-insights page per session under
#   evidence/insights/ — takeaways classified durable|maybe|transient
#   with rationale. NOTHING is auto-promoted: patterns/anti-patterns still go
#   through the normal human-gated pipeline (these proposals are inputs).
#
# Usage:
#   python3 scripts/cmd/mine-chats.py <project> [--since 90d] [--llm] [--dry-run]

import json
import re
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
from pathlib import Path

from wf_common import yaml_scalar
from fabric_config import FABRIC_ROOT, CORPUS_ROOT, get_config

import layout

# Transient signals: low durable value
_TRANSIENT = [
    (r"\b\d+\s+open PRs?\b", "PR-count snapshot"),
    (r"\bPR #\d+ (?:failed|passed|is (?:green|red))\b", "per-PR CI state"),
    (r"\b(?:CI|tests?) (?:fail(?:ed|ing)?|pass(?:ed|ing)?|green|red)\b(?![^.]*\b(?:because|rule|always|invariant)\b)", "CI state snapshot"),
    (r"\b(?:currently|right now|as of (?:today|now))\b", "present-state snapshot"),
    (r"\breviews? have landed\b", "review-queue snapshot"),
    (r"\bthe (?:file|source) is \d+ lines\b", "file trivia"),
]
# Durable signals: mechanism, constraint, rationale
_DURABLE_SIGNALS = [
    "because", "reason", "rationale", "constraint", "limitation",
    "does not", "cannot", "always", "never", "must", "instead",
    "fails open", "idempotent", "anti-loop", "invariant", "the rule",
    "chose", "decided", "tradeoff", "trade-off", "prefer", "rather than",
    "no method to", "provides no", "only method", "rejects", "requires",
]


def classify(text):
    low = (text or "").lower()
    for pat, label in _TRANSIENT:
        if re.search(pat, low):
            return "transient", label
    score = sum(1 for s in _DURABLE_SIGNALS if s in low)
    if score >= 2:
        return "durable", f"{score} durable signals"
    if score == 1:
        return "maybe", "weak signal"
    return "transient", "no durable signals"


def _sentences(text):
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s*", "", text, flags=re.MULTILINE)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z`])", text)
    return [p.strip().strip("`") for p in parts if len(p.strip()) > 30]


def heuristic_takeaways(transcript_path):
    """0-token pass: sentence-level classification."""
    text = transcript_path.read_text(encoding="utf-8", errors="replace")
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "##", "###", "```", "~~~", "- Harness", "- Session",
                                        "- Directory", "- Date", "- User turns", "- Project", "### Tool")):
            continue
        if len(line) < 40:  # too thin to be knowledge
            continue
        for sent in _sentences(line):
            kind, why = classify(sent)
            if kind in ("durable", "maybe"):
                results.append({"kind": kind, "statement": sent,
                                "rationale": why, "source": transcript_path.name})
    return results


LLM_PROMPT = """You are distilling an agent-harness chat session into durable
engineering knowledge. Extract SESSION TAKEAWAYS in these categories ONLY:

1. PATTERN — a way of working that succeeded and generalizes (mechanism + why + when)
2. ANTI-PATTERN — an approach that failed or was rejected, with the observed failure
3. WORKFLOW — a repeatable procedure that worked and would be reused
4. CONSTRAINT — a hard limitation discovered (API, platform, environment)
5. DECISION — a choice made, with rationale and the rejected alternative

STRICTLY EXCLUDE (transient, low-value): CI/PR counts, review-queue states,
"as of today" snapshots, anything that goes stale when a PR merges, restatements
of task instructions, tool-call logs without interpretation.

Each takeaway: {"kind": "...", "statement": "<one atomic sentence>",
"rationale": "<why / outcome / rejected alternative>", "confidence": "high|medium|low"}
Return ONLY a JSON array. Empty session → [].

### SESSION
"""


def llm_takeaways(transcript_path):
    from extract_backends import parse_json_array, llm_config, LLM_TEMPERATURE, ARTICLE_MAX_TOKENS
    import openai, os
    cfg = llm_config(compiler=True)
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                           timeout=float(os.environ.get("WIKI_LLM_TIMEOUT", "600")))
    text = transcript_path.read_text(encoding="utf-8", errors="replace")
    if len(text) > 120_000:
        text = text[:120_000] + "\n... [truncated]"
    resp = client.chat.completions.create(
        model=cfg["model"], temperature=LLM_TEMPERATURE, max_tokens=ARTICLE_MAX_TOKENS,
        messages=[
            {"role": "system", "content": "You extract durable engineering knowledge from engineering chat transcripts. Return ONLY valid JSON."},
            {"role": "user", "content": LLM_PROMPT + "\n\n" + text},
        ])
    return parse_json_array(resp.choices[0].message.content or "") or []


def write_insight_page(transcript_path, takeaways, dry_run=False, project=None):
    """One chat-insights page per transcript, grouped by classification."""
    out_dir = layout.insights(CORPUS_ROOT)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = transcript_path.stem.replace("chat-", "insight-", 1)
    out = out_dir / f"{stem}.md"
    _durable_kinds = {"pattern", "anti-pattern", "workflow", "constraint", "decision", "durable"}
    durable = [t for t in takeaways if str(t.get("kind", "")).lower() in _durable_kinds]
    maybe = [t for t in takeaways if str(t.get("kind", "")).lower() in ("maybe",)]
    transient = [t for t in takeaways if t.get("kind") == "transient"]
    lines = [f"---",
             f"type: synthesis",
             f"title: \"Chat insights: {transcript_path.stem.replace('chat-', '', 1)}\"",
             f"description: \"Session-level durable takeaways (transients filtered)\"",
             f"source: {transcript_path}",
             f"project: {project}",
             f"created: 2026-09-20",
             f"---",
             f"",
             f"# Chat insights — {transcript_path.name}",
             f"",
             f"Source: `{transcript_path.name}` · distilled takeaways only; transients (CI states, PR counts, snapshots) excluded."]
    if durable:
        lines += ["", "## Durable takeaways"]
        for t in durable:
            lines.append(f"- **[{t.get('kind', 'takeaway')}]** {t.get('statement', '')}"
                         + (f" — {t['rationale']}" if t.get("rationale") and t.get("rationale") != t.get("statement") else ""))
    if maybe:
        lines += ["", "## Maybe (weak signal — human review)"]
        for t in maybe:
            lines.append(f"- {t.get('statement', '')}")
    if transient:
        lines += ["", "## Filtered as transient"]
        for t in transient[:8]:
            lines.append(f"- {t.get('statement', '')[:140]}")
    if not dry_run:
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out, len(durable), len(maybe), len(transient)


_KW_RE = re.compile(r"\b[a-z]{3,}\b")
# the near-miss band mirrors mine-promotions' philosophy: EXACT-dup (== id)
# handled by hash; zero-overlap pairs can't be the same take — only pairs in
# 0 < sim < NEAR_MISS_MAX do the judgment make sense for (similarity near 1.0
# is already near-identical text; leave to the human).
NEAR_MISS_MIN = 0.15
NEAR_MISS_MAX = 0.75


def _kw_set(text):
    return set(_KW_RE.findall(text.lower()))


def _jaccard(a, b):
    i, u = len(a & b), len(a | b)
    return (i / u) if u else 0.0


def _refine_near_miss(statement, kind, out_dir, dry_run=False, project=None, transcript_stem=None):
    """Judge a new takeaway against the EXISTING same-kind inbox candidates
    whose keyword Jaccard lands in the near-miss band (#173).

    Judged-SAME → merge into the existing candidate: provenance gains this
    transcript's source line, the body keeps the original statement (the
    candidate is the unit of review) and the merged takeaways note records
    the second phrasing. Returns the merged dest path.
    Judged-DIFFERENT → None (caller stages separately — normal flow).
    Tier unavailable / G-J refused → None + a loud print (keyword behavior
    byte-identical to the pre-#173 flow).

    Routing: the pair's repo (project) threads the per-repo judgment seam;
    the G-J gate is checked for that repo's judge identity."""
    try:
        from judgment import (same_recurrence, judgment_eval_recorded,
                              JudgmentUnavailable)
    except ImportError:
        return None
    from wf_common import norm as _norm
    new_kw = _kw_set(_norm(statement))
    try:
        existing = sorted(out_dir.glob(f"{kind}-chat-*.md"))
    except OSError:
        return None
    for ex in existing:
        ex_text = ex.read_text(encoding="utf-8", errors="replace")
        # the comparison surface is the CANDIDATE STATEMENT (title + body head
        # before the mined-from boilerplate) — comparing against the whole
        # file diluted the keyword set with template prose and pushed real
        # paraphrases under the band (found in test, #173)
        body = ex_text.split("---", 2)[-1]
        cand_stmt = body.split("**Mined from:**")[0].strip()
        cand_stmt = re.sub(r"^#\s+\S+.*$", "", cand_stmt, flags=re.M).strip()
        sim = _jaccard(new_kw, _kw_set(_norm(cand_stmt)))
        if not (NEAR_MISS_MIN <= sim <= NEAR_MISS_MAX):
            continue
        try:
            ok, why = judgment_eval_recorded()
        except Exception as e:
            ok, why = False, f"gate check failed: {e}"
        if not ok:
            print(f"  judgment gate (G-J) not satisfied — near-miss merge skipped: {why}")
            return None
        try:
            same, p = same_recurrence(statement, cand_stmt,
                                      repo=project, context="both are chat-mined takeaways from sessions in the same project")
        except JudgmentUnavailable as e:
            print(f"  judgment tier unavailable — near-miss merge skipped: {str(e)[:80]}")
            return None
        if not same:
            print(f"  judged near-miss p={p:.2f} -> keep separate ({ex.stem})")
            continue
        if dry_run:
            print(f"  [DRY] judged near-miss p={p:.2f} -> merge into {ex.stem}")
            return ex
        _merge_into(ex, statement, source_stem_for(project, transcript_stem), p)
        print(f"  judged near-miss p={p:.2f} -> MERGED into {ex.stem} (provenance +1)")
        return ex
    return None


def source_stem_for(project, transcript_stem):
    from wf_common import slugify as _slugify
    return _slugify(f"{project}/chats/{transcript_stem or 'session'}")


def _merge_into(dest, statement, source_stem, prob):
    """Merge a judged-same paraphrase into an existing candidate: provenance
    gains the new source line + judgment record; the body notes the second
    phrasing (deterministic frontmatter edit, 0 tokens)."""
    text = dest.read_text(encoding="utf-8", errors="replace")
    fm_end = text.index("\n---", 4)
    fm = text[4:fm_end]
    lines = fm.splitlines()
    # the provenance block: 'provenance:' through the last 2-space-indented
    # entry (or blank); insert the new source BEFORE the next top-level key
    pstart = next((i for i, l in enumerate(lines) if l.startswith("provenance:")), None)
    prov_line = (f'  - source: "[[{source_stem}]]"\n'
                 f'    locator: "session transcript"\n'
                 f'    quote: {yaml_scalar(statement[:120])}\n'
                 f'    judged: "near-miss merged p={prob:.2f}"')
    if pstart is None:
        lines += ["provenance:", prov_line]
    else:
        pend = pstart + 1
        while pend < len(lines) and (lines[pend].startswith("  ") or not lines[pend].strip()):
            pend += 1
        lines = lines[:pend] + [prov_line] + lines[pend:]
    new_fm = "\n".join(lines)
    text = f"---{new_fm}---\n" + text[fm_end + 4:]
    # body note
    text = text.rstrip() + (f"\n\n**Merged (judged) phrasing** (p={prob:.2f}, "
                            f"[[{source_stem}]]): {statement}\n")
    dest.write_text(text, encoding="utf-8")


def propose_candidates(transcript_path, takeaways, dry_run=False, project=None):
    """#89: durable pattern/anti-pattern takeaways → staged candidates in
    patterns/_inbox/ with provenance (source chat, session) in frontmatter.
    NOTHING is auto-promoted: candidates wait for the human gate (surfaced
    by wf gate via promote-patterns.list_pending).
    Judgement refines BEFORE staging (#173): near-miss takeaways (this
    transcript vs PRIOR staged candidates) get a same_recurrence verdict —
    judged-same merges into the existing candidate (provenance gains the
    second source), judged-different stages separately. The G-J gate
    (judgment_eval_recorded) routes the seam per project; an uncalibrated
    judge = keyword behavior unchanged (loud)."""
    import hashlib
    from datetime import date
    out_dir = layout.patterns_inbox(CORPUS_ROOT)
    out_dir.mkdir(parents=True, exist_ok=True)
    proposed = 0
    for t in takeaways:
        kind = str(t.get("kind", "")).lower()
        if kind not in ("pattern", "anti-pattern"):
            continue
        statement = str(t.get("statement", "")).strip()
        if not statement:
            continue
        chash = hashlib.sha256(statement.encode("utf-8")).hexdigest()[:10]
        cid = f"{kind}-chat-{chash}"
        dest = out_dir / f"{cid}.md"
        if dest.exists():
            continue  # idempotent: same statement never duplicated

        # --- judged near-miss refinement (#173) -------------------------
        # keyword near-miss vs the EXISTING inbox (same kind): an exact-hash
        # match never reaches here, but paraphrases did — those are the class
        # the judgment tier exists to merge. G-J gated; per-repo seam.
        merged = _refine_near_miss(statement, kind, out_dir, dry_run=dry_run,
                                   project=project, transcript_stem=transcript_path.stem)
        if merged is not None:
            proposed += 1
            continue

        if dry_run:
            print(f"  [DRY] would propose {cid}")
            proposed += 1
            continue
        # src-stem join: ingest slugifies the raw rel path (kebab — underscores
        # fold), so 'comfyui_mcp/chats/x' ingests as src-comfyui-mcp-chats-x-md.
        # The old raw f"{project}-chats-{stem}" broken the link on underscore
        # projects; slugify(project + path) reproduces the real stem exactly.
        from wf_common import slugify as _slugify
        source_stem = _slugify(f"{project}/chats/{transcript_path.stem}")
        dest.write_text(f"""---
type: pattern
id: {cid}
title: {yaml_scalar(statement[:140])}
status: candidate
maturity: 1
origin: chat-mined
source_chat: "[[{source_stem}]]"
project: {project}
provenance:
  - source: "[[{source_stem}]]"
    locator: "session transcript"
    quote: {yaml_scalar(statement[:120])}
tags: [chat-mined, inbox]
created: {date.today().isoformat()}
---

# {cid}

{statement}

**Mined from:** [[{source_stem}]] — session-level durable takeaway
(kind: {kind}). Review against the promotion checklist: independence,
evidence, applicability. Apply via promote-patterns --apply.""")
        proposed += 1
    return proposed


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Distill chat transcripts into durable knowledge (transients filtered)")
    parser.add_argument("project", help="Project slug")
    parser.add_argument("--since", default="90d", help="Window for finding transcripts by date prefix")
    parser.add_argument("--llm", action="store_true", help="LLM distillation (1 call/session); default is heuristic, 0 tokens")
    parser.add_argument("--propose", action="store_true", help="Also stage durable pattern/anti-pattern takeaways as gated candidates (patterns/_inbox/, #89)")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    chats_dir = layout.evidence_raw(CORPUS_ROOT) / args.project / "chats"
    if not chats_dir.is_dir():
        print(f"No chats captured for {args.project} — run: wf capture chat {args.project}", file=sys.stderr)
        return 2
    transcripts = sorted(chats_dir.glob("*.md"))[: args.limit]
    if not transcripts:
        print("No transcripts found.", file=sys.stderr)
        return 0

    total_proposed = 0


    print(f"=== Mining {len(transcripts)} chat transcript(s) for {args.project} "
          f"({'LLM' if args.llm else 'heuristic, 0 tokens'}) ===")
    total_durable = 0
    for tp in transcripts:
        if args.llm:
            raw = llm_takeaways(tp)
        else:
            raw = heuristic_takeaways(tp)
        out, nd, nm, nt = write_insight_page(tp, raw, dry_run=args.dry_run, project=args.project)
        if args.propose:
            proposed = propose_candidates(tp, raw, dry_run=args.dry_run, project=args.project)
            total_proposed += proposed
        total_durable += nd
        print(f"  {tp.name}: {nd} durable, {nm} maybe, {nt} transient-filtered"
              + ("  [DRY]" if args.dry_run else ""))
    print(f"\n{total_durable} durable takeaway(s) across {len(transcripts)} session(s)")
    if not args.dry_run and total_durable:
        print(f"Insight pages: {layout.evidence(CORPUS_ROOT) / 'insights'}/ — "
              f"review before feeding experience events or promotion.")
    if args.propose:
        print(f"Pattern candidates staged: {total_proposed} → "
              f"{layout.patterns(CORPUS_ROOT) / '_inbox'}/ (wf gate lists them)")
    return 0
    if total_proposed and not args.dry_run:
        try:
            import gate
            sections = {"pattern-candidates": (total_proposed,
                                               [f"chat:{args.project}"], None)}
            gate._notify(None, sections,
                         summary={"pattern-candidates": total_proposed})
        except Exception as e:
            print(f"[notify] non-fatal: {e}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())