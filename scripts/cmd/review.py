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

import layout

TODAY = date.today()

def _parse_date(s):
    try:
        from datetime import datetime
        return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
    except Exception:
        return None

def scan():
    """Scan claims, concepts, insights, AND source records for staleness.
    Sources carry their own review_after (ingest stamps a capture-kind tier
    at record creation, #160 S1; records predating the tiers scan as current
    — the SOURCE-STALE migration advisory comes from lint, not scan).
    Returns report dict."""
    report = {"due": [], "overdue": [], "stale": [], "current": 0}
    for pattern, label in [("evidence/claims/claim-*.md", "claim"),
                           ("concepts/concept-*.md", "concept"),
                           ("evidence/insights/*.md", "insight"),
                           ("evidence/sources/src-*.md", "source")]:
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
    """Stamp last_verified=today, roll review_after forward by the tier interval.
    A mechanical stale_after stamp (ingest's sha256-drift trigger) is CLEARED
    here and a contested status demoted by it flips back: the stamp meant
    "this claim cited a revision that no longer exists" — a passed mechanical
    re-verify (sha + quote + locator) is exactly the proof it has re-grounded,
    so keeping the stamp made successful verification report stale forever."""
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
    # clear the mechanical drift stamp + restore the status it demoted
    if "stale_after:" in s and str(TODAY) >= s.split("stale_after:")[1].split("\n")[0].strip()[:10]:
        s = re.sub(r"^stale_after: \S+\n", "", s, count=1, flags=re.MULTILINE)
        s = re.sub(r"^status: contested$", "status: supported", s, count=1, flags=re.MULTILINE)
    f.write_text(s, encoding="utf-8")
    return tier, new_review


def _reverify_source(src_path):
    """#160 S1/S2: mechanical source re-verification (0 tokens): recompute the
    raw sha256. Returns (state, detail):
      'fresh'    — recorded == actual (roll review_after)
      'drifted'  — raw changed upstream since capture (SOURCE-DRIFT at lint
                   already flags claims; the record gains stale_after today)
      'gone'     — raw file deleted (upstream vanished) → the source EXPIRES:
                   status: expired, claims get stale_after (no re-ground)
    Records predating the tier stamps gain review_after here (migration)."""
    from wf_common import parse_frontmatter, sha256_file
    import re as _re
    f = Path(src_path)
    fm, _ = parse_frontmatter(f)
    raw = CORPUS_ROOT / str(fm.get("source_path") or "")
    recorded = str(fm.get("sha256") or "")
    if not recorded:
        return "none", "no sha256 on record"
    if not raw.exists():
        return "gone", f"{fm.get('source_path')} missing (upstream vanished)"
    actual = sha256_file(raw)
    if actual[:12] != recorded[:12]:
        return "drifted", f"sha256 {recorded[:12]} != {actual[:12]}"
    return "fresh", actual[:12]


def expire_or_reverify_source(src_path, dry_run=False):
    """Apply the S1/S2 lifecycle to one source record. Fresh → roll
    review_after by the capture-kind tier + clear today-stamped stale_after;
    drifted → stamp stale_after (claims already handled by ingest's drift
    trigger); gone → status: expired (raw is immutable/deleted, never
    re-captured). Deterministic; returns (outcome, detail)."""
    from datetime import timedelta
    import re as _re
    f = Path(src_path)
    s = f.read_text(encoding="utf-8", errors="replace")
    kind = "pr-record" if "/git/pr-" in str(f) or "/git/issue-" in str(f) else (
        "commit" if "/git/commit-" in str(f) else
        "chat-session" if "/chats/" in str(f) else "default")
    tier = {"pr-record": 30, "commit": 30, "chat-session": 45, "default": 180}[kind]
    state, detail = _reverify_source(f)
    if state == "fresh":
        if dry_run:
            return "fresh", detail
        new_review = (TODAY + timedelta(days=tier)).isoformat()
        if "review_after:" in s:
            s = _re.sub(r"review_after: \S+", f"review_after: {new_review}", s)
        else:
            s = s.replace("sha256:", f"review_after: {new_review}\nsha256:", 1)
        if "stale_after:" in s:
            s = _re.sub(r"^stale_after: \S+\n", "", s, count=1, flags=_re.MULTILINE)
        if "last_verified:" in s:
            s = _re.sub(r"last_verified: \S+", f"last_verified: {TODAY.isoformat()}", s)
        else:
            s = s.replace("review_after:", f"last_verified: {TODAY.isoformat()}\nreview_after:", 1)
        f.write_text(s, encoding="utf-8")
        return "refreshed", detail
    if state == "drifted":
        if dry_run:
            return "drifted", detail
        if "stale_after:" not in s:
            s = s.replace("sha256:", f"stale_after: {TODAY.isoformat()}\nsha256:", 1)
            f.write_text(s, encoding="utf-8")
        return "drifted", detail
    if state == "gone":
        if dry_run:
            return "expired", detail
        s = _re.sub(r"^status: .*$", "status: expired", s, count=1, flags=_re.MULTILINE)
        if "stale_after:" not in s:
            s = s.replace("sha256:", f"stale_after: {TODAY.isoformat()}\nsha256:", 1)
        f.write_text(s, encoding="utf-8")
        return "expired", detail
    return state, detail


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Staleness review: check + re-verify")
    parser.add_argument("--check", action="store_true", help="Full staleness report")
    parser.add_argument("--json", action="store_true",
                        help="Machine-readable output (report dict for --check/--verify-sources/--auto-reverify; issue #164)")
    parser.add_argument("--project", help="Limit to a project slug")
    parser.add_argument("--verify", metavar="CLAIM", help="Re-verify a claim (path or id)")
    parser.add_argument("--verify-all", action="store_true", help="Re-verify all overdue claims")
    parser.add_argument("--auto-reverify", action="store_true",
                        help="Mechanically re-verify claims whose source hasn't drifted (sha256 + quote check, 0 tokens)")
    parser.add_argument("--verify-sources", action="store_true",
                        help="Mechanically re-verify every source record (#160): fresh rolls review_after, raw-drifted stamps stale_after, upstream-deleted EXPIRES the record (0 tokens)")
    parser.add_argument("--dry-run", action="store_true", help="--verify-sources: report outcomes, write nothing")
    parser.add_argument("--verify-locators", action="store_true",
                        help="Re-check every claim's locator against its raw source (#109): rewrite drifted locators, strip the verification stamp + contest claims whose quote vanished (0 tokens)")
    parser.add_argument("--contradiction-sweep", action="store_true",
                        help="Newest-wins demotion (#175): same-source contradicts relations where the contradictor is strictly newer + supported mechanically demote the older claim (contested + stale_after); a contradictor no longer supported restores the demoted claim. Sources: hand-written relations blocks + registry/effects verdicts (0 tokens)")
    parser.add_argument("--demoted", action="store_true",
                        help="List claims demoted by the contradiction sweep (repairable via --restore-demoted + claim id)")
    parser.add_argument("--restore-demoted", metavar="CLAIM",
                        help="Re-ground a contradiction-demoted claim: clears the contradiction stamp (the contradicts-relation note stays in the body; re-run the sweep to re-demote if the contradictor still holds)")
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

    if args.verify_sources:
        from pathlib import Path as _P
        counts = {"refreshed": 0, "fresh": 0, "drifted": 0, "expired": 0, "none": 0}
        outcomes = []
        for sp in sorted(layout.sources(CORPUS_ROOT).glob("src-*.md")):
            if args.project and args.project not in sp.stem:
                continue
            outcome, detail = expire_or_reverify_source(sp, dry_run=args.dry_run)
            counts[outcome] = counts.get(outcome, 0) + 1
            outcomes.append({"source": sp.name, "outcome": outcome, "detail": detail})
            if outcome in ("drifted", "expired"):
                print(f"  {outcome.upper()}: {sp.name} — {detail}")
        print(f"Sources: {counts['refreshed']} refreshed, {counts['fresh']} fresh, "
              f"{counts['drifted']} drifted, {counts['expired']} expired"
              + (" [DRY RUN]" if args.dry_run else ""))
        if args.json:
            import json
            print(json.dumps({"mode": "verify-sources", "counts": counts,
                              "dry_run": bool(args.dry_run),
                              "outcomes": outcomes}, indent=2))
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

    if getattr(args, "contradiction_sweep", False):
        import json as _json
        demoted, restored, detail = contradiction_sweep(dry_run=args.dry_run,
                                                        project=args.project)
        skipped = sum(1 for d in detail if d.startswith("skip "))
        print(f"Contradiction sweep (newest-wins, #175): {demoted} demoted, "
              f"{restored} restored, {skipped} skipped"
              + (" [DRY RUN]" if args.dry_run else ""))
        for line in detail[:40]:
            print(f"  {line}")
        if args.json:
            print(_json.dumps({"mode": "contradiction-sweep", "demoted": demoted,
                               "restored": restored, "skipped": skipped,
                               "detail": detail}, indent=2))
        return 1 if demoted and not args.dry_run else 0

    if getattr(args, "restore_demoted", None):
        claims_dir = layout.claims(CORPUS_ROOT)
        target = Path(args.restore_demoted)
        if not target.exists():
            cands = list(claims_dir.glob(f"*{args.restore_demoted}*"))
            target = cands[0] if cands else None
        if not target or not target.exists():
            print(f"Claim not found: {args.restore_demoted}", file=sys.stderr)
            return 1
        if not _contested_by_stamp(target.read_text(encoding="utf-8", errors="replace")):
            print(f"{target.name}: no contradiction stamp — nothing to restore")
            return 0
        if not args.dry_run:
            _restore(target)
        print(f"restored {target.name} (re-run --contradiction-sweep to re-demote "
              f"if the contradictor still holds)")
        return 0

    if getattr(args, "demoted", False):
        n = 0
        for p in sorted(layout.claims(CORPUS_ROOT).glob("claim-*.md")):
            s = p.read_text(encoding="utf-8", errors="replace")
            if _contested_by_stamp(s):
                n += 1 if print(f"  {p.name}") else 1
        print(f"{n} contradiction-demoted claim(s)" if n else
              "none demoted (sweep clean)")
        return 0

    if args.auto_reverify:
        import json as _json
        verified, skipped, sketch = auto_reverify(dry_run=False, project=args.project, _collect=True)
        print(f"Auto-reverified: {verified} (source unchanged, quote verified)")
        print(f"Skipped: {skipped} (source drifted, no source, or quote not found — needs human review)")
        if args.json:
            print(_json.dumps({"mode": "auto-reverify", "verified": verified,
                               "skipped": skipped, "skipped_files": sketch}, indent=2))
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
    if args.json:
        import json
        print(json.dumps({"mode": "report", "date": TODAY.isoformat(),
                          "project": args.project,
                          "current": report["current"],
                          "due": report["due"], "overdue": report["overdue"],
                          "stale": report["stale"]}, indent=2))
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
    claims_dir = layout.claims(CORPUS_ROOT)
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
        src_page = layout.sources(CORPUS_ROOT) / (str(ref.get("source", "")).strip('"[]').lower() + ".md")
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


def auto_reverify(dry_run=False, project=None, _collect=False):
    """Mechanically re-verify claims whose source hasn't drifted:
    1. source sha256 matches recorded value → source is unchanged
    2. claim's quote still appears in the source text → claim holds
    Stamps last_verified + review_after. 0 tokens. Returns (verified, skipped, failed).
    _collect=True returns failed as the list of skipped file NAMES (for --json);\
    otherwise it stays a count (the historical shape)."""
    import hashlib
    from wf_common import parse_frontmatter
    report = scan()
    candidates = report["overdue"] + report["stale"]
    # also due-soon if they're doc-sourced (sha256-verified, mechanical)
    if not dry_run and not project:
        pass
    verified, skipped, failed = 0, 0, 0
    skipped_files: list = []
    for item in candidates:
        if item["type"] != "claim":
            continue
        f = Path(item["file"])
        if project and project not in f.name:
            continue
        # parse frontmatter for source_ref — real YAML parse, not regexes:
        # multi-line quotes carry \n escapes that the quote:"?(.*?)"? regex
        # returned literally (literal backslash-n matched nothing), and the
        # regex chain silently skipped every multi-line-quote claim.
        fm_text = f.read_text(encoding="utf-8", errors="replace")
        fm, _ = parse_frontmatter(f)
        refs = fm.get("source_refs") or []
        ref = refs[0] if refs and isinstance(refs[0], dict) else None
        if not ref or not str(ref.get("source", "")).strip():
            # legacy shape: source: "[[src-...]]" + bare quote/locator fields
            src_match = re.search(r'source: "\[\[(src-[^\]]+)\]\]"', fm_text)
            quote_match = re.search(r'quote: "?(.*?)"?\s*$', fm_text, re.MULTILINE)
            if not src_match or not quote_match:
                skipped += 1
                if _collect: skipped_files.append(f.name)
                continue
            src_stem = src_match.group(1).strip("[]")
            quote = quote_match.group(1).strip()
            if quote.startswith('"') and quote.endswith('"'):
                try:
                    import yaml as _y
                    _unq = _y.safe_load(quote)
                    if isinstance(_unq, str):
                        quote = _unq
                except Exception:
                    quote = quote.strip('"').replace('\\"', '"').replace("\\\\", "\\")
        else:
            src_stem = str(ref.get("source", "")).strip('"[]')
            quote = str(ref.get("quote", "")).strip()
        if not quote:
            skipped += 1
            if _collect: skipped_files.append(f.name)
            continue
        # find the source record
        src_file = layout.sources(CORPUS_ROOT) / f"{src_stem}.md"
        if not src_file.exists():
            skipped += 1
            if _collect: skipped_files.append(f.name)
            continue
        src_fm, src_body = parse_frontmatter(src_file)
        # source_path is CORPUS-relative (the layout contract); FABRIC_ROOT was
        # the pre-nested-corpus layout — on it, every claim skipped as "no
        # source" (verify-locators already resolved via CORPUS_ROOT; same fix).
        src_rel = str(src_fm.get("source_path") or "")
        src_path = (CORPUS_ROOT / src_rel) if src_rel else None
        if not src_path or not src_path.exists():
            legacy = FABRIC_ROOT / src_rel
            src_path = legacy if legacy.exists() else src_path
        if not src_path or not src_path.exists():
            skipped += 1
            if _collect: skipped_files.append(f.name)
            continue
        # check sha256 drift
        from wf_common import sha256_file
        recorded = str(src_fm.get("sha256", ""))
        actual = sha256_file(src_path)
        if recorded[:12] != actual[:12]:
            skipped += 1  # source drifted — needs human review, can't auto-verify
            if _collect: skipped_files.append(f.name)
            continue
        # check quote still in source (quote already YAML-unescaped above)
        quote_clean = re.sub(r"L\d+:", "", quote).strip()
        # per-repo routing note: auto-reverify is mechanical (no judgment
        # calls) — repo context affects only judgment-tier flows (verify-
        # effects, mining refinement), nothing here.
        src_text = src_path.read_text(encoding="utf-8", errors="replace")
        if quote_clean and quote_clean not in src_text:
            # fuzzy: try normalized
            from extract_backends import _normalize_for_match
            norm_src = _normalize_for_match(src_text)
            norm_q = _normalize_for_match(quote_clean)
            if norm_q and norm_q not in norm_src and norm_q[:int(len(norm_q)*0.6)] not in norm_src:
                skipped += 1
                if _collect: skipped_files.append(f.name)
                continue
        # verified: source unchanged, quote present
        if not dry_run:
            verify_claim(f)
        verified += 1
    return (verified, skipped, skipped_files) if _collect else (verified, skipped, failed)


# === Newest-wins contradiction sweep (#114 spike → #175) ====================

_DEMOTE_MARK = "contradicted-by"


def _contradiction_pairs(project=None):
    """Collect (demotee, contradictor, origin) pairs from the two carriers:
    hand-written relations blocks (type: contradicts in a claim frontmatter)
    and registry/effects/*.effects.json judged verdicts. Deterministic, 0
    tokens. Unknown-target pairs skip (relation to a deleted claim is an
    ORPHAN lint concern, not sweep input)."""
    from wf_common import parse_frontmatter
    import json as _json
    fx_dir = layout.registry(CORPUS_ROOT) / "effects"
    pairs = []
    claims_dir = layout.claims(CORPUS_ROOT)
    for f in sorted(claims_dir.glob("claim-*.md")):
        if project and project not in f.stem:
            continue
        fm, _ = parse_frontmatter(f)
        src_stem = f.stem
        for rel in (fm.get("relations") or []):
            if not isinstance(rel, dict) or str(rel.get("type", "")).lower() != "contradicts":
                continue
            target = str(rel.get("target", "")).strip('"[]')
            if target.startswith("[[") and target.endswith("]]"):
                target = target[2:-2]
            if not target:
                continue
            pairs.append((src_stem, target, "relation"))
    if fx_dir.is_dir():
        for ef in sorted(fx_dir.glob("*.effects.json")):
            try:
                d = _json.loads(ef.read_text())
            except Exception:
                continue  # torn write → not sweep input this cycle
            src_stem = str(d.get("claim") or "")
            if project and project not in src_stem:
                continue
            for against, effect in (d.get("judged_effects") or {}).items():
                if str(effect).lower() == "contradicts":
                    pairs.append((src_stem, str(against), "effects-verdict"))
    return pairs


def _claim_capture_date(stem):
    """The claim's ingestion-time clock for the newest-wins compare:
    captured || generated.at (the hierarchy ingest stamps). Date or None
    (unknown = never newest-wins — unknown clocks don't demote)."""
    from wf_common import parse_frontmatter
    f = layout.claims(CORPUS_ROOT) / f"{stem}.md"
    if not f.exists():
        return None
    fm, _ = parse_frontmatter(f)
    raw = str(fm.get("captured") or "").strip()[:10]
    try:
        return date.fromisoformat(raw)
    except Exception:
        pass
    gen = fm.get("generated") or {}
    if isinstance(gen, dict):
        raw = str(gen.get("at") or "").strip()[:10]
        try:
            return date.fromisoformat(raw)
        except Exception:
            pass
    return None


def _contested_by_stamp(s):
    return (_DEMOTE_MARK + ":") in s


def _set_contested(path, reason_line):
    s = path.read_text(encoding="utf-8", errors="replace")
    s = re.sub(r"^status: (?:supported|proposed)$",
               f"status: contested\n{_DEMOTE_MARK}: \"{reason_line}\"",
               s, count=1, flags=re.MULTILINE)
    if "stale_after:" not in s:
        s = s.replace("last_verified:", f"stale_after: {TODAY.isoformat()}\nlast_verified:", 1)
    path.write_text(s, encoding="utf-8")


def _restore(path):
    """Clear the contradiction stamp + flip back (the verify_claim stamp-
    clearing mechanism, #109-adjacent)."""
    s = path.read_text(encoding="utf-8", errors="replace")
    s = re.sub(rf'^{_DEMOTE_MARK}: ?"?[^"\n]*"?\n', "", s, count=1, flags=re.MULTILINE)
    s = re.sub(r"^status: contested$", "status: supported", s, count=1, flags=re.MULTILINE)
    s = re.sub(r"^stale_after: \S+\n", "", s, count=1, flags=re.MULTILINE)
    path.write_text(s, encoding="utf-8")


def contradiction_sweep(dry_run=False, project=None):
    """#175: mechanically demote claims a NEWER still-supported same-corpus
    claim contradicts; restore demoted claims whose contradictor lost
    support. Graphiti's newest-wins invariant in git-native form (the #114
    spike's one adoptable gap). The carriers are proposals (relations
    blocks + judged effects verdicts, G-J-gated upstream); the DECISION is
    deterministic date logic — same proposal/validation split as the
    compiler/judgment gates. Returns (demoted, restored, detail lines)."""
    demoted = restored = skipped = 0
    detail = []
    claims_dir = layout.claims(CORPUS_ROOT)
    from wf_common import parse_frontmatter
    for a, b, origin in _contradiction_pairs(project):
        if a == b:
            continue
        fa, fb = claims_dir / f"{a}.md", claims_dir / f"{b}.md"
        if not fa.exists() or not fb.exists():
            skipped += 1
            detail.append(f"skip {a} <- {b}: claim file missing")
            continue
        # Direction-free newest-wins: the pair contradicts; whichever side is
        # chronologically OLDER loses to the newer one (verify-effects writes
        # effects from the new claim's perspective; hand relations are
        # outward — normalizing both by DATE avoids two convention bugs).
        ta, tb = _claim_capture_date(a), _claim_capture_date(b)
        if ta is None or tb is None or ta == tb:
            skipped += 1
            detail.append(f"skip {a} <- {b}: clocks unknown or equal")
            continue
        demotee, t_dem, contradictor, t_con = (a, ta, b, tb) if ta < tb else (b, tb, a, ta)
        d_dem = claims_dir / f"{demotee}.md"
        dem_s = d_dem.read_text(encoding="utf-8", errors="replace")
        # the contradictor must still be supported — an unworthy judge demotes
        # nothing; demoted claims whose contradictor lost support RESTORE
        con_fm, _ = parse_frontmatter(claims_dir / f"{contradictor}.md")
        if str(con_fm.get("status") or "").lower() != "supported":
            if _contested_by_stamp(dem_s):
                if dry_run:
                    restored += 1
                    detail.append(f"[dry] RESTORE {demotee} (contradictor {contradictor} no longer supported)")
                else:
                    _restore(d_dem)
                    restored += 1
                    detail.append(f"RESTORE {demotee} (contradictor {contradictor} no longer supported)")
            continue
        if str(con_fm.get("status") or "").lower() == "supported" and not _contested_by_stamp(dem_s):
            # also restore when the demotee's stamp is absent but... no: only
            # demote when the DEMOTEE is currently supported/proposed
            pass
        if _contested_by_stamp(dem_s):
            continue  # already demoted — idempotent re-run
        dem_st = str((parse_frontmatter(d_dem)[0] or {}).get("status") or "").lower()
        if dem_st not in ("supported", "proposed", ""):
            continue  # only a live claim can be demoted (already contested for
            # another reason keeps ITS reason; superseded/expired untouched)
        if dry_run:
            demoted += 1
            detail.append(f"[dry] DEMOTE {demotee} (contradicted by newer {contradictor}, {origin})")
            continue
        _set_contested(d_dem, f"{contradictor} ({origin}, strictly newer {t_con})")
        demoted += 1
        detail.append(f"DEMOTE {demotee} (contradicted by newer {contradictor}, {origin})")
    return demoted, restored, detail


if __name__ == "__main__":
    sys.exit(main())