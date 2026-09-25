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
#   evidence/insights/<project>/ — takeaways classified durable|maybe|transient
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

from fabric_config import FABRIC_ROOT, CORPUS_ROOT, get_config

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
    from extract_backends import parse_json_array, llm_config
    import openai, os
    cfg = llm_config(compiler=True)
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                           timeout=float(os.environ.get("WIKI_LLM_TIMEOUT", "600")))
    text = transcript_path.read_text(encoding="utf-8", errors="replace")
    if len(text) > 120_000:
        text = text[:120_000] + "\n... [truncated]"
    resp = client.chat.completions.create(
        model=cfg["model"], temperature=0.1, max_tokens=4096,
        messages=[
            {"role": "system", "content": "You extract durable engineering knowledge from engineering chat transcripts. Return ONLY valid JSON."},
            {"role": "user", "content": LLM_PROMPT + "\n\n" + text},
        ])
    return parse_json_array(resp.choices[0].message.content or "") or []


def write_insight_page(transcript_path, takeaways, dry_run=False, project=None):
    """One chat-insights page per transcript, grouped by classification."""
    out_dir = CORPUS_ROOT / "evidence" / "insights"
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


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Distill chat transcripts into durable knowledge (transients filtered)")
    parser.add_argument("project", help="Project slug")
    parser.add_argument("--since", default="90d", help="Window for finding transcripts by date prefix")
    parser.add_argument("--llm", action="store_true", help="LLM distillation (1 call/session); default is heuristic, 0 tokens")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    chats_dir = CORPUS_ROOT / "evidence" / "raw" / args.project / "chats"
    if not chats_dir.is_dir():
        print(f"No chats captured for {args.project} — run: wf capture chat {args.project}", file=sys.stderr)
        return 2
    transcripts = sorted(chats_dir.glob("*.md"))[: args.limit]
    if not transcripts:
        print("No transcripts found.", file=sys.stderr)
        return 0

    print(f"=== Mining {len(transcripts)} chat transcript(s) for {args.project} "
          f"({'LLM' if args.llm else 'heuristic, 0 tokens'}) ===")
    total_durable = 0
    for tp in transcripts:
        if args.llm:
            raw = llm_takeaways(tp)
        else:
            raw = heuristic_takeaways(tp)
        out, nd, nm, nt = write_insight_page(tp, raw, dry_run=args.dry_run, project=args.project)
        total_durable += nd
        print(f"  {tp.name}: {nd} durable, {nm} maybe, {nt} transient-filtered"
              + ("  [DRY]" if args.dry_run else ""))
    print(f"\n{total_durable} durable takeaway(s) across {len(transcripts)} session(s)")
    if not args.dry_run and total_durable:
        print(f"Insight pages: {CORPUS_ROOT / 'evidence' / 'insights'}/ — "
              f"review before feeding experience events or promotion.")
    return 0


if __name__ == "__main__":
    sys.exit(main())