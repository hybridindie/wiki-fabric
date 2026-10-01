#!/usr/bin/env python3
# utility.py — deterministic receipt↔outcome join (#87 / SkillOpt-epic S1, #138).
#
# Walks experience events, follows their `receipt:` links, walks each receipt's
# delivered pages, and writes usage counts onto pattern/skill pages:
#   usage: { retrieved_count, applied_count, successful_outcomes, last_validated }
#
# 0 tokens, deterministic, byte-stable for the same corpus state. Unlinked
# events (no receipt) are counted and reported, never silently dropped.
#
# Usage:
#   python3 scripts/cmd/utility.py [--dry-run] [--project <slug>] [--json]
#
# Outcome parsing is deliberately dumb strings first (PASS/FAIL/positive/
# negative sniffing, same as mine-promotions.py) — a structured verdict
# schema can come later; the join is easy to re-run.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))

import argparse
import json
import re
from datetime import date
from pathlib import Path

from fabric_config import CORPUS_ROOT, get_config
from wf_common import parse_frontmatter

import layout

POSITIVE = re.compile(r"\b(pass(ed)?|success(ful)?|positive|fixed|works|shipped)\b", re.I)
NEGATIVE = re.compile(r"\b(fail(ed|ure)?|negative|regress(ed|ion)?|broke|revert)\b", re.I)


def _events(project=None):
    base = layout.projects(CORPUS_ROOT)
    dirs = [base / project] if project else sorted(d for d in base.iterdir() if d.is_dir()) if base.is_dir() else []
    out = []
    for d in dirs:
        ee = d / "experience-events"
        if ee.is_dir():
            out.extend(sorted(ee.glob("ee-*.md")))
    return out


def _receipt_for(rid, project):
    for base in ([layout.projects(CORPUS_ROOT) / project / "receipts"] if project else []) + \
                sorted(p / "receipts" for p in (layout.projects(CORPUS_ROOT)).iterdir() if p.is_dir()):
        p = base / f"{rid}.json"
        if p.exists():
            return p
    return layout.receipts(CORPUS_ROOT) / f"{rid}.json"


def _delivered_pages(receipt_path):
    """Paths of pages delivered in a receipt (pattern/skill only — claims are
    evidence, not adaptation layer)."""
    try:
        r = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for sel in r.get("selected", []):
        path = str(sel.get("path", ""))
        if re.search(r"(patterns|anti-patterns|skills|domains)/[\w/-]+\.md$", path):
            out.append(path)
    return out


def _outcomes(text):
    """Sniff the outcomes: dict for PASS/FAIL-ish signals. Returns set()."""
    m = re.search(r"^outcomes:\n((?:\s{2,}.*\n?)+)", text, re.M)
    blob = m.group(1) if m else ""
    signals = set()
    if POSITIVE.search(blob):
        signals.add("positive")
    if NEGATIVE.search(blob):
        signals.add("negative")
    return signals


def _usage_block(counts):
    lines = ["usage:"]
    lines.append(f"  retrieved_count: {counts['retrieved_count']}")
    lines.append(f"  applied_count: {counts['applied_count']}")
    lines.append(f"  successful_outcomes: {counts['successful_outcomes']}")
    lines.append(f"  last_validated: {counts['last_validated']}")
    return "\n".join(lines)


def _parse_usage(text):
    counts = {"retrieved_count": 0, "applied_count": 0,
              "successful_outcomes": 0, "last_validated": None}
    m = re.search(r"^usage:\n((?:\s{2,}.*\n?)+)", text, re.M)
    if m:
        for line in m.group(1).splitlines():
            kv = re.match(r"\s*(\w+):\s*(\S+)", line)
            if kv and kv.group(1) in counts:
                counts[kv.group(1)] = kv.group(2) if kv.group(1) == "last_validated" \
                    else int(kv.group(2) or 0)
    return counts


def _write_usage(page_path, counts, dry_run):
    """Set/replace the usage: block on a pattern/skill page (frontmatter area)."""
    text = page_path.read_text(encoding="utf-8", errors="replace")
    block = _usage_block(counts)
    if re.search(r"^usage:\n(?:\s{2,}.*\n?)+", text, re.M):
        text = re.sub(r"^usage:\n(?:\s{2,}.*\n?)+", block + "\n", text, count=1, flags=re.M)
    else:
        # insert before the closing frontmatter delimiter
        parts = text.split("---", 2)
        if len(parts) >= 3:
            parts[1] = parts[1].rstrip("\n") + "\n" + block + "\n"
            text = "---".join(parts)
        else:
            return False
    if not dry_run:
        page_path.write_text(text, encoding="utf-8")
    return True


page_path = None  # set by caller (module-level scratch)


def compute(project=None, dry_run=False, report_json=False):
    """Run the join. Returns a report dict. Mutates pattern/skill pages unless
    dry_run. Zero LLM tokens."""
    stats = {"events": 0, "linked": 0, "unlinked": 0, "receipts_found": 0,
             "pages_touched": 0, "outcome_positive": 0, "outcome_negative": 0,
             "missing_receipts": []}
    usage = {}   # rel-page-path -> counts dict

    for ev in _events(project):
        stats["events"] += 1
        text = ev.read_text(encoding="utf-8", errors="replace")
        rm = re.search(r"^receipt:\s*(receipt-[\w-]+)", text, re.M)
        ev_proj = ev.parent.parent.name
        if not rm:
            stats["unlinked"] += 1
            continue
        rp = _receipt_for(rm.group(1), ev_proj)
        if not rp or not rp.exists():
            stats["missing_receipts"].append(rm.group(1))
            continue
        stats["linked"] += 1
        for rel in _delivered_pages(rp):
            counts = usage.setdefault(rel, {"retrieved_count": 0, "applied_count": 0,
                                            "successful_outcomes": 0, "last_validated": None})
            counts["retrieved_count"] += 1
            outcomes = _outcomes(text)
            if "positive" in outcomes:
                counts["applied_count"] += 1
                counts["successful_outcomes"] += 1
                stats["outcome_positive"] += 1
                if not counts["last_validated"] or date.today().isoformat() > counts["last_validated"]:
                    counts["last_validated"] = date.today().isoformat()
            elif "negative" in outcomes:
                stats["outcome_negative"] += 1
                if not counts["last_validated"]:
                    counts["last_validated"] = ""

    touched = 0
    for rel, counts in sorted(usage.items()):
        target = CORPUS_ROOT / rel
        if not target.exists():
            continue
        merged = _parse_usage(target.read_text(encoding="utf-8", errors="replace"))
        for k in ("retrieved_count", "applied_count", "successful_outcomes"):
            merged[k] = max(merged.get(k, 0), counts.get(k, 0))
        if counts.get("last_validated"):
            merged["last_validated"] = max(merged.get("last_validated") or "", counts["last_validated"])
        if _write_usage(target, merged, dry_run):
            touched += 1
        stats["pages_touched"] = touched

    if report_json:
        print(json.dumps(stats, indent=1))
    else:
        print(f"utility: {stats['events']} event(s) — {stats['linked']} linked to receipts, "
              f"{stats['unlinked']} unlinked, {stats['pages_touched']} page(s) updated")
        if stats["missing_receipts"]:
            print(f"  missing receipts: {', '.join(stats['missing_receipts'][:5])}"
                  + (f" (+{len(stats['missing_receipts']) - 5} more)" if len(stats["missing_receipts"]) > 5 else ""))
        if stats["unlinked"]:
            print("  unlinked events are counted, not silently dropped — link them with: wf log --receipt <id>")
    return stats


def main():
    parser = argparse.ArgumentParser(description="Receipt↔outcome join → usage counts on pattern/skill pages (0 tokens)")
    parser.add_argument("--project", help="Limit to one project namespace")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    parser.add_argument("--json", dest="report_json", action="store_true", help="Machine-readable report")
    args = parser.parse_args()
    compute(project=args.project, report_json=args.report_json, dry_run=args.dry_run)


if __name__ == "__main__":
    main()