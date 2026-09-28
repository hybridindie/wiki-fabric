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
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
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
    parser.add_argument("--verify-locators", action="store_true",
                        help="Re-check every claim's locator against its raw source (#109): rewrite drifted locators, strip the verification stamp + contest claims whose quote vanished (0 tokens)")
    parser.add_argument("--limit", type=int, default=None, help="Limit claims processed (verify-locators)")
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

    if args.verify_locators:
        r = verify_locators(dry_run=False, project=args.project, limit=args.limit)
        print(f"Locator re-verification: {r['checked']} checked")
        print(f"  kept:      {r['kept']} (quote found at locator)")
        print(f"  fixed:     {r['fixed']} (locator rewritten to the true span)")
        print(f"  contested: {r['contested']} (quote NOT in source — stamp stripped, status contested)")
        if r.get("restored"):
            print(f"  restored:  {r['restored']} (previously-contested quote now verifies)")
            for name in r["restored_files"][:10]:
                print(f"    ✓ {name}")
        for name in r["contested_files"][:10]:
            print(f"    ⚠ {name}")
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



# === Locator re-verification (#109) =======================================

from wf_common import normalize_match as _norm


def repair_backtick_elision(quote, source_segment):
    """#109 acceptance: repair the backtick-elision hallucination class — the
    extraction model empties inline-code spans (source '`L1:`, `L2:`' becomes
    quote '`, `'). Substitutes the source's backticked contents into the
    quote's empty spans. Conservative: fires only when EVERY quote span is
    empty and the source segment has non-empty spans to fill from."""
    if "`" not in quote or "`" not in source_segment:
        return quote, False
    q_spans = re.findall(r"`([^`]*)`", quote)
    if not q_spans or not all(not s.strip() for s in q_spans):
        return quote, False
    s_spans = re.findall(r"`([^`]*)`", source_segment)
    filled = [s for s in s_spans if s.strip()]
    if len(filled) < len(q_spans):
        return quote, False
    it = iter(filled)

    def sub(m):
        return f"`{next(it).strip()}`"

    return re.sub(r"`[^`]*`", sub, quote), True


def verify_locators(dry_run=False, project=None, limit=None):
    """Deterministic locator re-verification for every claim (#109).

    The `process:locator-verification` stamp was applied at extract time and
    never re-checked: the audit found 14% of claims carry drifted locators
    while stamped verified. This pass re-checks every claim with a source_ref:

      quote found AT the locator        → stamp stays
      quote found in the source NEARBY  → locator rewritten, stamp stays
      quote NOT in the source at all    → stamp STRIPPED, status → contested

    0 tokens, deterministic. Returns dict of counts."""
    from wf_common import parse_frontmatter, sha256_file
    claims_dir = CORPUS_ROOT / "evidence" / "claims"
    checked = fixed = kept = contested = skipped = restored = 0
    contested_files = []
    restored_files = []
    for cp in sorted(claims_dir.glob("claim-*.md")):
        if project and project not in cp.name:
            continue
        if limit and checked >= limit:
            break
        fm, _ = parse_frontmatter(cp)
        refs = fm.get("source_refs")
        if not refs or not isinstance(refs, list) or not isinstance(refs[0], dict):
            skipped += 1
            continue
        ref = refs[0]
        loc = str(ref.get("locator", "")).strip()
        quote = str(ref.get("quote", "")).strip()
        m = re.match(r"L(\d+)(?:-L?(\d+))?$", loc)
        if not m or not quote:
            skipped += 1
            continue
        src_page = CORPUS_ROOT / "evidence" / "sources" / (str(ref.get("source", "")).strip('"[]').lower() + ".md")
        if not src_page.exists():
            skipped += 1
            continue
        sfm, _ = parse_frontmatter(src_page)
        raw_rel = str(sfm.get("source_path") or "").strip()
        raw = (CORPUS_ROOT / raw_rel) if raw_rel else None
        if not raw or not raw.exists():
            skipped += 1
            continue
        checked += 1
        lines = raw.read_text(encoding="utf-8", errors="replace").splitlines()
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        q_norm = _norm(quote)
        head = q_norm[:60]  # search heuristic only
        # the quote's own line span in the raw source (windows must be able to
        # hold it — a 3-line window misses quotes spanning more lines)
        q_span = max(1, len(str(quote).split("\n")) + 2)

        def span_text(x, y):
            return _norm("\n".join(lines[max(0, x - 1):min(y, len(lines))]))

        # kept = the FULL quote sits inside the RECORDED span (exact locator);
        # the q_span extension is only a search-phase allowance, never a pass
        if q_norm and q_norm in span_text(a, b):
            kept += 1
            # a previously-contested claim whose quote now verifies at its
            # locator restores status + stamp (session audit finding: the
            # backtick repair updated the quote but the status stayed
            # contested, demoting the claim forever)
            if not dry_run and str(fm.get("status")) == "contested":
                s = cp.read_text(encoding="utf-8", errors="replace")
                s = re.sub(r"^status: contested$", "status: supported",
                           s, count=1, flags=re.MULTILINE)
                if "process:locator-verification" not in s:
                    s = s.replace("status: supported",
                                  "verified:\n  - by: \"process:locator-verification\"\n"
                                  f"    at: \"{date.today().isoformat()}\"\nstatus: supported", 1)
                cp.write_text(s, encoding="utf-8")
                restored += 1
                restored_files.append(cp.name)
            continue
        # locator drifted — find the true span: head locates the start line,
        # then grow from ONE line upward until the full quote fits (the tightest
        # containing span — a wide default window once wrote L1-L3 for a
        # quote that lives entirely on L2)
        found = None
        if head:
            for i in range(len(lines)):
                if head in span_text(i + 1, i + max(1, q_span)):
                    # the quote's true start line: the first line whose own
                    # text contains the quote's first 2 words (the head window
                    # may start before the quote's actual first line)
                    qwords = q_norm.split()[:2]
                    start_line = i + 1
                    for fwd in range(i, min(i + max(3, q_span), len(lines))):
                        own = _norm(lines[fwd])
                        if own and all(w in own for w in qwords):
                            start_line = fwd + 1
                            break
                    for ext in range(1, q_span + 10):
                        if q_norm in span_text(start_line, start_line + ext - 1):
                            found = (start_line, start_line + ext - 1)
                            break
                    if found:
                        break
        if found:
            fixed += 1
            if not dry_run:
                new_loc = f"L{found[0]}-L{found[1]}" if found[1] > found[0] else f"L{found[0]}"
                s = cp.read_text(encoding="utf-8", errors="replace")
                if f'locator: "{loc}"' in s:
                    s = s.replace(f'locator: "{loc}"', f'locator: "{new_loc}"', 1)
                else:  # unquoted form
                    s = re.sub(rf"locator: {re.escape(loc)}\b", f"locator: {new_loc}", s, count=1)
                cp.write_text(s, encoding="utf-8")
        else:
            # last chance: the backtick-elision class — the model emptied
            # inline-code spans. Repair the quote from the recorded span's
            # source text; a repaired quote is re-checked against the span.
            seg_raw = "\n".join(lines[max(0, a - 1):min(b + q_span, len(lines))])
            repaired, did = repair_backtick_elision(str(quote), seg_raw)
            if did and _norm(repaired) in _norm(seg_raw):
                if not dry_run:
                    s = cp.read_text(encoding="utf-8", errors="replace")
                    s = s.replace(f'quote: "{quote}"', f'quote: "{repaired}"', 1)
                    if f'quote: "{repaired}"' not in s:
                        print(f"  warn: could not rewrite quote (escaping mismatch): {cp.name}", file=sys.stderr)
                    else:
                        # a previously-contested claim whose quote now verifies
                        # restores its status + verification stamp (session audit
                        # finding: repair updated the quote but left status
                        # contested, so the claim stayed demoted forever)
                        s = re.sub(r"^status: contested$", "status: supported",
                                   s, count=1, flags=re.MULTILINE)
                        if "process:locator-verification" not in s:
                            s = s.replace("status: supported",
                                          "verified:\n  - by: \"process:locator-verification\"\n"
                                          f"    at: \"{date.today().isoformat()}\"\nstatus: supported",
                                          1)
                        cp.write_text(s, encoding="utf-8")
                fixed += 1
                continue
            # quote no longer in the source: the stamp lies — strip it
            contested += 1
            contested_files.append(cp.name)
            if not dry_run:
                s = cp.read_text(encoding="utf-8", errors="replace")
                # edit ONLY the status field — a quote can legitimately contain
                # 'status: supported' (sim audit false-positive lesson)
                s = re.sub(r"^status: supported$", "status: contested", s, count=1, flags=re.MULTILINE)
                s = s.replace('  - by: "process:locator-verification"\n', "", 1)
                cp.write_text(s, encoding="utf-8")
    return {"checked": checked, "kept": kept, "fixed": fixed,
            "contested": contested, "skipped": skipped,
            "contested_files": contested_files,
            "restored": restored, "restored_files": restored_files}


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
