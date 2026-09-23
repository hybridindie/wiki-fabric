#!/usr/bin/env python3
# review.py — Staleness review: check what's due, re-verify claims.
#
# Usage:
#   python3 scripts/cmd/review.py --check                     # full staleness report
#   python3 scripts/cmd/review.py --check --project <slug>    # scoped
#   python3 scripts/cmd/review.py --verify <claim-id>         # re-verify one claim
#   python3 scripts/cmd/review.py --verify-all --project <slug>  # bulk re-verify

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
import re
from pathlib import Path
from datetime import date, timedelta

from fabric_config import FABRIC_ROOT, CORPUS_ROOT

TODAY = date.today()

def _parse_date(s):
    try:
        from datetime import datetime
        return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
    except Exception:
        return None

def scan():
    """Scan claims, concepts, insights for staleness. Returns report dict."""
    report = {"due": [], "overdue": [], "stale": [], "current": 0}
    for pattern, label in [("evidence/claims/claim-*.md", "claim"),
                           ("concepts/concept-*.md", "concept"),
                           ("evidence/insights/*.md", "insight")]:
        for f in Path(CORPUS_ROOT).glob(pattern):
            s = f.read_text(encoding="utf-8", errors="replace")
            review = _parse_date(re.search(r"review_after: (\S+)", s).group(1)) if re.search(r"review_after:", s) else None
            stale = _parse_date(re.search(r"stale_after: (\S+)", s).group(1)) if re.search(r"stale_after:", s) else None
            lv = _parse_date(re.search(r"last_verified: (\S+)", s).group(1)) if re.search(r"last_verified:", s) else None
            due_date = review or stale
            if not due_date:
                report["current"] += 1
                continue
            overdue_days = (TODAY - due_date).days
            if overdue_days > 90 or (stale and stale <= TODAY):
                report["stale"].append({"file": str(f), "type": label, "due": str(due_date), "overdue_days": overdue_days, "last_verified": str(lv) if lv else None})
            elif overdue_days > 0:
                report["overdue"].append({"file": str(f), "type": label, "due": str(due_date), "overdue_days": overdue_days, "last_verified": str(lv)})
            else:
                report["due"].append({"file": str(f), "type": label, "due": str(due_date), "days_until": -overdue_days, "last_verified": str(lv)})
    return report


def print_report(report, project=None):
    print(f"=== Staleness Report ({TODAY.isoformat()}) ===")
    print()
    if project:
        print(f"  Scope: {project}")
        print()
    print(f"  Current:  {report['current']}")
    print(f"  Due soon: {len(report['due'])}")
    print(f"  Overdue:  {len(report['overdue'])}")
    print(f"  Stale:    {len(report['stale'])}")
    print()
    if report["overdue"]:
        print("  Overdue for review:")
        for item in sorted(report["overdue"], key=lambda x: -x["overdue_days"])[:10]:
            print(f"    ⚠ {item['overdue_days']:3}d  {Path(item['file']).name[:60]}")
    if report["stale"]:
        print("  Stale (moved to archive):")
        for item in sorted(report["stale"], key=lambda x: -x["overdue_days"])[:10]:
            print(f"    ✗ {Path(item['file']).name[:60]}")


def verify_claim(claim_path):
    """Stamp last_verified=today, roll review_after forward by the tier interval."""
    f = Path(claim_path)
    s = f.read_text(encoding="utf-8", errors="replace")
    tier = 90
    if "chats-" in f.name:
        tier = 45
    elif "concept-" in f.name:
        tier = 120
    new_review = (TODAY + __import__("datetime").timedelta(days=tier)).isoformat()
    if "review_after:" in s:
        s = re.sub(r"review_after: \S+", f"review_after: {new_review}", s)
    else:
        s = s.replace("last_verified:", f"review_after: {new_review}\nlast_verified:", 1)
    if "last_verified:" in s:
        s = re.sub(r"last_verified: \S+", f"last_verified: {TODAY.isoformat()}", s)
    else:
        s = s.replace("review_after:", f"last_verified: {TODAY.isoformat()}\nreview_after:", 1)
    f.write_text(s, encoding="utf-8")
    return tier, new_review


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Staleness review: check + re-verify")
    parser.add_argument("--check", action="store_true", help="Full staleness report")
    parser.add_argument("--project", help="Limit to a project slug")
    parser.add_argument("--verify", metavar="CLAIM", help="Re-verify a claim (path or id)")
    parser.add_argument("--verify-all", action="store_true", help="Re-verify all overdue claims")
    parser.add_argument("--auto-reverify", action="store_true",
                        help="Mechanically re-verify claims whose source hasn't drifted (sha256 + quote check, 0 tokens)")
    args = parser.parse_args()

    if args.verify:
        # find the file
        target = Path(args.verify)
        if not target.exists():
            candidates = list(Path("evidence/claims").glob(f"*{args.verify}*"))
            if candidates:
                target = candidates[0]
            else:
                print(f"Claim not found: {args.verify}", file=sys.stderr)
                return 1
        tier, new_review = verify_claim(target)
        print(f"✓ re-verified {target.name}")
        print(f"  last_verified: {TODAY.isoformat()}")
        print(f"  review_after:  {new_review} ({tier}d tier)")
        return 0

    if args.auto_reverify:
        verified, skipped, _ = auto_reverify(dry_run=False, project=args.project)
        print(f"Auto-reverified: {verified} (source unchanged, quote verified)")
        print(f"Skipped: {skipped} (source drifted, no source, or quote not found — needs human review)")
        return 0

    if args.verify_all:
        report = scan()
        n = 0
        for item in report["overdue"] + report["stale"]:
            if item["type"] == "claim":
                verify_claim(item["file"])
                n += 1
        print(f"Re-verified {n} claim(s)")
        return 0

    # default: report
    report = scan()
    print_report(report, args.project)
    return 0



def auto_reverify(dry_run=False, project=None):
    """Mechanically re-verify claims whose source hasn't drifted:
    1. source sha256 matches recorded value → source is unchanged
    2. claim's quote still appears in the source text → claim holds
    Stamps last_verified + review_after. 0 tokens. Returns (verified, skipped, failed)."""
    import hashlib
    from wf_common import parse_frontmatter
    report = scan()
    candidates = report["overdue"] + report["stale"]
    # also due-soon if they're doc-sourced (sha256-verified, mechanical)
    if not dry_run and not project:
        pass
    verified, skipped, failed = 0, 0, 0
    for item in candidates:
        if item["type"] != "claim":
            continue
        f = Path(item["file"])
        if project and project not in f.name:
            continue
        # parse frontmatter for source_ref
        fm_text = f.read_text(encoding="utf-8", errors="replace")
        src_match = re.search(r'source: "\[\[(src-[^\]]+)\]\]"', fm_text)
        quote_match = re.search(r'quote: "?(.*?)"?\s*$', fm_text, re.MULTILINE)
        locator_match = re.search(r'locator: "?([^\n]+?)"?\s*$', fm_text, re.MULTILINE)
        if not src_match or not quote_match:
            skipped += 1
            continue
        # find the source record
        src_stem = src_match.group(1).strip("[]")
        src_file = CORPUS_ROOT / "evidence" / "sources" / f"{src_stem}.md"
        if not src_file.exists():
            skipped += 1
            continue
        src_fm, src_body = parse_frontmatter(src_file)
        src_path = FABRIC_ROOT / (src_fm.get("source_path") or "")
        if not src_path.exists():
            skipped += 1
            continue
        # check sha256 drift
        from wf_common import sha256_file
        recorded = str(src_fm.get("sha256", ""))
        actual = sha256_file(src_path)
        if recorded[:12] != actual[:12]:
            skipped += 1  # source drifted — needs human review, can't auto-verify
            continue
        # check quote still in source
        quote = quote_match.group(1).strip()
        quote_clean = re.sub(r"L\d+:", "", quote).strip()
        src_text = src_path.read_text(encoding="utf-8", errors="replace")
        if quote_clean and quote_clean not in src_text:
            # fuzzy: try normalized
            from extract_backends import _normalize_for_match
            norm_src = _normalize_for_match(src_text)
            norm_q = _normalize_for_match(quote_clean)
            if norm_q and norm_q not in norm_src and norm_q[:int(len(norm_q)*0.6)] not in norm_src:
                skipped += 1
                continue
        # verified: source unchanged, quote present
        if not dry_run:
            verify_claim(f)
        verified += 1
    return verified, skipped, failed


if __name__ == "__main__":
    sys.exit(main())
