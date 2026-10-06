#!/usr/bin/env python3
# promote-patterns.py — apply human-approved chat-mined pattern candidates (#89)
#
# The gated second half of mine-chats --propose: staged candidates in
# patterns/_inbox/ move to canonical patterns/ on --apply, or are rejected
# with a required reason (--reject). Mirrors promote-questions.py.
#
# #190: the judged auto-apply tier (--auto) — inbox candidates ONLY.
# Deterministic preconditions + one calibrated judgment call band the
# candidate: p >= promotion.auto_threshold applies (recorded, reversible),
# in-band escalates to the human gate, below stays annoted in the inbox.
# Dossiers/claims/domains/questions are NEVER auto-promoted. Off until
# tuning.promotion.auto_apply is true — a policy change must be explicit.
#
# Usage:
#   python3 scripts/cmd/promote-patterns.py --list
#   python3 scripts/cmd/promote-patterns.py --apply <candidate> [--dry-run]
#   python3 scripts/cmd/promote-patterns.py --reject <id> --reason "..."
#   python3 scripts/cmd/promote-patterns.py --auto [--dry-run]
#   python3 scripts/cmd/promote-patterns.py --unapply <canonical-file>

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import argparse
import re
from pathlib import Path
from datetime import date, datetime, timezone
from wf_common import parse_frontmatter, dump_frontmatter
from fabric_config import CORPUS_ROOT
import layout

INBOX_DIR = layout.patterns_inbox(CORPUS_ROOT)
PATTERNS_DIR = layout.patterns(CORPUS_ROOT)
ANTI_PATTERNS_DIR = layout.anti_patterns(CORPUS_ROOT)


def list_pending():
    """Staged chat-mined candidates awaiting human review."""
    out = []
    if not INBOX_DIR.exists():
        return out
    for p in sorted(INBOX_DIR.glob("*.md")):
        fm, _ = parse_frontmatter(p)
        if str(fm.get("status", "")).lower() == "candidate":
            out.append((p, fm))
    return out


# ---- #190: the judged auto-apply tier (inbox candidates ONLY) --------------
# Contract: deterministic preconditions (0 tokens) → one calibrated judgment
# (G-J gated) → band: confident applies (recorded+reversible), near-band
# escalates, below stays annotated. The judgment never writes content: the
# move IS apply_candidate, the record IS the frontmatter stamp + log entry.


AUTO_APPLY_REASON = "judged-confident (p={prob:.2f}, judge={judge})"


_JUDGED_DIFFERENT_RE = re.compile(
    r"judged-different|judged: .*keep separate|"
    r'effect: "?(contradicts|supersedes)"?')


def _judged_different_present(fm, path):
    """Deterministic layer: a judged-different verdict anywhere in the
    candidate's record means a contest exists — the human decides. Covers
    twin-merge keep-separate records re-staged later and any contradicts/
    supersedes verdict on its provenance sources."""
    try:
        return bool(_JUDGED_DIFFERENT_RE.search(path.read_text(encoding="utf-8",
                                                                errors="replace")))
    except OSError:
        return False


def _preconditions(p, fm):
    """The deterministic half of --auto (0 tokens). Returns (ok, reason).
    All must hold — one failure refuses WITHOUT calling the judge."""
    if fm.get("type") not in ("pattern", "anti-pattern"):
        return False, f"not an inbox candidate type ({fm.get('type')}) — dossier/claims/domains are never auto-promoted"
    if str(fm.get("status", "")).lower() != "candidate":
        return False, f"status is {fm.get('status')}, not candidate"
    # age: twin-merge waves settle; a just-mined candidate waits a day
    created = str(fm.get("created") or "").strip()[:10]
    try:
        age = (date.today() - date.fromisoformat(created)).days
    except Exception:
        return False, "no parseable created date"
    if age < 1:
        return False, f"age {age}d < 1d (twin-merge waves settle)"
    # provenance completeness: every candidate carries at least one source
    # record ref with locator + quote (the citation contract, lint-checked
    # shape — checked here inline so preconditions are self-contained)
    provs = fm.get("provenance") or fm.get("source_refs") or []
    if not (isinstance(provs, list) and provs and isinstance(provs[0], dict)
            and str(provs[0].get("locator", "")).strip()
            and str(provs[0].get("quote", "")).strip()):
        return False, "incomplete provenance (needs source + locator + quote)"
    if _judged_different_present(fm, p):
        return False, "a judged-different verdict exists in the record — a contest means human"
    return True, ""


def _banding(prob, threshold, band):
    """The one banding truth: >= thr applies; [thr-band, thr) escalates;
    else stays. ONE-SIDED below the floor (the auto-apply contract, #190):
    a probability far below the threshold is a clear STAY — escalating it
    would dump the judge's rejected items on the human; the escalation band
    exists for the genuinely borderline (just under the floor). The
    judgment.is_near_threshold symmetric semantics remain available for
    two-sided consumers; this band is the auto-tier's own."""
    if prob >= threshold:
        return "apply"
    if (threshold - prob) <= band:
        return "escalate"
    return "stay"


def _auto_thresholds(config):
    """(auto_apply, threshold, band) — tuning.promotion.* + judgment.near_band.
    The escalation band is DERIVED from the two settings (the #190 amendment:
    they trade off; banding is relative to the tuned threshold, never a
    constant)."""
    from fabric_config import get_tuning
    on = bool(get_tuning(config, "promotion", "auto_apply", False))
    thr = float(get_tuning(config, "promotion", "auto_threshold", 0.90))
    band = float(get_tuning(config, "judgment", "near_band", 0.1))
    return on, thr, band


def auto_applied_marker(corpus_root):
    """Candidates auto-applied in the last N days, from canonical pattern
    pages' auto_applied stamps — the gate's INFO surface. Deterministic."""
    out = []
    for d in (layout.patterns(corpus_root), layout.anti_patterns(corpus_root)):
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            fm, _ = parse_frontmatter(p)
            aa = fm.get("auto_applied")
            if isinstance(aa, dict) and aa:
                out.append({"id": p.stem, "judge": str(aa.get("judge", "")),
                            "prob": aa.get("prob"), "at": str(aa.get("at", ""))})
    return out


def unapply(canonical_name, dry_run=False):
    """Roll an auto-apply back: the exact canonical file returns to the inbox
    (the auto_applied stamp records the judgment — the restore is the
    reverse file op, logged). Refuses when the artifact isn't auto-applied
    (a human apply never auto-reverts)."""
    target = None
    for d in (PATTERNS_DIR, ANTI_PATTERNS_DIR):
        cand = d / (canonical_name if canonical_name.endswith(".md")
                    else f"{canonical_name}.md")
        if cand.exists():
            target = cand
            break
    if target is None:
        print(f"Not found in patterns/ or anti-patterns/: {canonical_name}")
        return False
    fm, body = parse_frontmatter(target)
    if not isinstance(fm.get("auto_applied"), dict):
        print(f"{target.name}: not auto-applied (no auto_applied stamp) — "
              f"human applies revert through promote-patterns --reject workflow, not --unapply")
        return False
    if dry_run:
        print(f"[dry-run] would move {target.name} back to {INBOX_DIR}")
        return True
    dest = INBOX_DIR / target.name
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    from wf_common import write_frontmatter
    write_frontmatter(dest, fm, body)  # stamp stays: the history is real
    target.unlink()
    _log_auto("unapply", target.name, prob=None, judge=None)
    print(f"unapplied: {target.name} → {INBOX_DIR} (auto_applied stamp retained; "
          f"the human gate sees it again)")
    return True


def promote_auto(dry_run=False):
    """The --auto run: per pending candidate, preconditions → judgment → band.
    Returns the report dict. When tuning.promotion.auto_apply is false this
    is a no-op with a loud pointer (the policy change must be explicit)."""
    config = _get_config()
    on, thr, band = _auto_thresholds(config)
    if not on:
        print("Auto-promote is OFF (tuning.promotion.auto_apply: false) — "
              "turn it on explicitly if this fabric wants the confident tier.")
        return {"mode": "auto", "off": True}
    from judgment import noul, judgment_eval_recorded, judge_identity, JudgmentUnavailable
    ok, why = judgment_eval_recorded(config)
    if not ok:
        print(f"G-J gate refused — no auto-promote: {why}")
        return {"mode": "auto", "refused": "G-J", "detail": why}
    identity = judge_identity(config)
    judge = f"{identity[0]}:{identity[1]}"
    report = {"mode": "auto", "judge": judge, "threshold": thr, "band": band,
              "applied": [], "escalated": [], "stayed": [], "refused": []}
    for p, fm in list_pending():
        okp, why = _preconditions(p, fm)
        if not okp:
            report["refused"].append({"id": p.stem, "reason": why})
            print(f"  refused (deterministic): {p.stem} — {why}")
            continue
        body = p.read_text(encoding="utf-8", errors="replace")
        statement = _candidate_statement(body)
        state = (f"CANDIDATE (type: {fm.get('type')}, origin: {fm.get('origin')}, "
                 f"project: {fm.get('project', 'none')}):\n{statement}\n\n"
                 f"Provenance: {_provenance_summary(fm)}\n\n"
                 "Should this candidate enter the corpus without human review? "
                 "Yes only if: the statement is fully entailed by the provenance "
                 "quotes (no extrapolation), applicability is concrete (not "
                 "vacuous), and the rule is specific enough to act on unchanged. "
                 "No when anything is unclear, unverifiable, or judgment-shaped.")
        if dry_run:
            print(f"  [dry-run] would judge {p.stem} (threshold {thr}, band {band})")
            continue
        try:
            prob = noul("Should this pattern candidate enter the corpus without "
                        "human review?", state)
        except JudgmentUnavailable as e:
            report["refused"].append({"id": p.stem, "reason": f"tier unavailable: {e}"})
            print(f"  tier unavailable — no decisions (never silent): {p.stem}")
            continue
        verdict = _banding(prob, thr, band)
        if verdict == "apply":
            ok_a = apply_candidate(p, dry_run=False)
            if ok_a:
                from fabric_config import actor as _actor
                _stamp_auto_applied(_dest_for(fm), prob, judge,
                                    _actor(config, "process", model="promote-patterns"))
                _log_auto("apply", p.stem, prob=prob, judge=judge)
                report["applied"].append({"id": p.stem, "prob": round(prob, 3), "judge": judge})
                print(f"  AUTO-APPLIED {p.stem} (p={prob:.2f} >= {thr}) — recorded, reversible (--unapply)")
        elif verdict == "escalate":
            _log_auto("escalate", p.stem, prob=prob, judge=judge)
            report["escalated"].append({"id": p.stem, "prob": round(prob, 3)})
            print(f"  ESCALATED {p.stem} (p={prob:.2f} in-band [{thr - band:.2f}, {thr})) — human gate")
        else:
            _log_auto("stay", p.stem, prob=prob, judge=judge)
            report["stayed"].append({"id": p.stem, "prob": round(prob, 3)})
            print(f"  in inbox {p.stem} (p={prob:.2f} < {thr - band:.2f}) — verdict recorded; --list annotates")
    return report


def _auto_note(fm):
    """--list annotation from the last recorded auto-tier verdict for this
    candidate id (log.md carries the verdicts; the inbox page is never
    rewritten for them). Empty when never auto-assessed."""
    cid = str(fm.get("id") or "")
    if not cid:
        return ""
    try:
        log = layout.registry(CORPUS_ROOT) / "log.md"
        if not log.exists():
            return ""
        text = log.read_text(encoding="utf-8", errors="replace")
        hits = re.findall(
            r"\* \*\*pattern-auto-(\w+) \| ([^*]+)\*\*\n- " + re.escape(cid) +
            r"( p=([0-9.]+))?( judge=([^\n]+))?", text)
        if not hits:
            return ""
        kind, _actor_line, _, prob, _, judge = hits[-1]
        bits = [f"auto-{kind}"]
        if prob:
            bits.append(f"p={float(prob):.2f}")
        if judge:
            bits.append(judge.strip())
        return f"  ⟂ {' · '.join(bits)}"
    except Exception:
        return ""


def _candidate_statement(body):
    """The RULE content, not the template boilerplate (the #173 lesson at
    this layer: whole-file comparison dilutes). The '## Rule' section or the
    body minus the mined-from tail."""
    if "## Rule" in body:
        return body.split("## Rule", 1)[1].split("\n## ", 1)[0].strip()
    head = body.split("**Mined from:**")[0]
    return re.sub(r"^#\s+\S+.*$", "", head, flags=re.M).strip()


def _provenance_summary(fm):
    provs = fm.get("provenance") or []
    lines = []
    for pr in provs[:4]:
        if isinstance(pr, dict):
            lines.append(f"- {str(pr.get('source', ''))[:60]} "
                         f"[{str(pr.get('locator', ''))[:40]}]: "
                         f"\"{str(pr.get('quote', ''))[:80]}\"")
    return "\n".join(lines) or "- (none)"


def _dest_for(fm):
    d = ANTI_PATTERNS_DIR if fm.get("type") == "anti-pattern" else PATTERNS_DIR
    return d / f"{fm.get('id') or 'candidate'}.md"


def _stamp_auto_applied(dest_path, prob, judge, actor_str):
    """Frontmatter marker: auto_applied: {judge, prob, at, by}. The stamp is
    what --unapply keys on and the gate's INFO surface reads — every
    auto-decision discoverable. ONE frontmatter writer (#154)."""
    from wf_common import parse_frontmatter as _pf, write_frontmatter
    fm, body = _pf(dest_path)
    fm["auto_applied"] = {"judge": judge, "prob": round(float(prob), 3),
                          "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                          "by": actor_str}
    write_frontmatter(dest_path, fm, body)


def _log_auto(kind, cid, prob=None, judge=None):
    """registry/log.md timeline entry (OKF §9 shape) — the audit trail per
    action, matching promotion-apply/reject entries. Fail-soft (the log is
    append-only but its absence must never crash the run)."""
    from fabric_config import actor as _actor
    try:
        log = layout.registry(CORPUS_ROOT) / "log.md"
        _at = datetime.now(timezone.utc)
        with open(log, "a") as f:
            f.write(f"\n## {_at.strftime('%Y-%m-%d')}\n"
                    f"* **pattern-auto-{kind} | {_actor(_get_config(), 'process', model='promote-patterns')}**\n")
            p = f" p={prob:.3f}" if prob is not None else ""
            j = f" judge={judge}" if judge else ""
            f.write(f"- {cid}{p}{j}\n")
    except Exception as e:
        print(f"warn: auto-{kind} not logged: {e}", file=sys.stderr)


def _get_config():
    from fabric_config import get_config
    return get_config()


def apply_candidate(p, dry_run=False):
    """Move one inbox candidate into its canonical dir (status: candidate
    kept — the pattern maturity gates still apply from here). type:
    anti-pattern pages go to anti-patterns/ (they never landed there before —
    the unconditional patterns/ dest made promote.py unable to see them)."""
    fm, _ = parse_frontmatter(p)
    if fm.get("type") not in ("pattern", "anti-pattern"):
        print(f"Not a pattern/anti-pattern candidate: {p}")
        return False
    if fm.get("type") == "anti-pattern":
        dest = ANTI_PATTERNS_DIR / f"{fm.get('id') or p.stem}.md"
    else:
        dest = PATTERNS_DIR / f"{fm.get('id') or p.stem}.md"
    if dry_run:
        print(f"[dry-run] would move {p.name} -> {dest}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = p.read_text(encoding="utf-8")
    text = text.replace("tags: [chat-mined, inbox]", "tags: [chat-mined]", 1)
    text = text.replace("tags: [rules-harvest, inbox]", "tags: [rules-harvest]", 1)
    dest.write_text(text, encoding="utf-8")
    p.unlink()
    # #178-B: a rules-harvested candidate RETIRES its source hand file (a
    # tombstone pointer replaces it — the corpus is the truth; the managed
    # export regenerates the rules file; the hand edit source is gone)
    if fm.get("origin") == "rules-file":
        _retire_source_rule(fm, dest)
    print(f"applied: {dest} — the pattern maturity gates now govern it (review_after applies)")
    return True


def _retire_source_rule(fm, canonical_path):
    """Replace the harvested rule's SOURCE file with a pointer to the corpus
    pattern (#178-B): the hand file's project repo + relative path from the
    provenance entry. Best-effort + loud: repo resolution failures print,
    never crash."""
    try:
        from fabric_config import FABRIC_ROOT, get_repo_config
        from wf_common import project_slug
        import re as _re
        provs = fm.get("provenance") or []
        if not provs or not isinstance(provs[0], dict):
            return
        src = str(provs[0].get("source") or "").strip('"')
        # the harvest writes 'repo/relative-path' (twin) or the relpath
        parts = src.split("/", 1)
        if len(parts) != 2:
            return  # no repo prefix → the file lives at an unknown root
        repo_name, rel = parts
        rcfg = get_repo_config(get_repo_config.__self__ if hasattr(get_repo_config, "__self__") else None, repo_name) \
            if False else get_repo_config(getattr(__import__("fabric_config"), "get_config")(), project_slug(repo_name))
        rp = (rcfg or {}).get("path") or ""
        repo = (FABRIC_ROOT / rp).resolve() if rp else None
        if not repo or not (repo / ".claude" / "rules").is_dir() and not (repo / rel).exists():
            return
        target = repo / rel
        if target.exists():
            target.write_text(f"""# RETIRED — promoted to the wiki-fabric corpus
# This rule file was harvested and promoted; the canonical version lives at
# `{canonical_path.name}` and the managed render regenerates it under
# .claude/rules/wiki-fabric/. Edit the PATTERN, not this file.
# (This pointer replaces the hand file — the corpus is the single truth; #178-B)
""")
            subprocess_git_add_commit(repo, target, canonical_path.name)
    except Exception as e:
        print(f"  (rule-retirement skipped: {e})", file=__import__("sys").stderr)


def subprocess_git_add_commit(repo, target, canonical_name):
    import subprocess
    subprocess.run(["git", "-C", str(repo), "add", "--", str(target.relative_to(repo))],
                   capture_output=True)
    # runner-safe identity: CI runners carry no global git user (the seed-
    # test class); the -c flags ride without breaking user-local config
    # (git prefers the -c values when the environment has none)
    subprocess.run(["git", "-C", str(repo),
                    "-c", "user.name=wiki-fabric", "-c", "user.email=wf@corpus.local",
                    "commit", "-m",
                    f"chore: rule promoted to wiki-fabric corpus ({canonical_name}) — this file is a pointer now"],
                   capture_output=True)


def reject_candidate(qid, reason, dry_run=False):
    """Reject: delete the staging page; the reason goes in the log."""
    p = INBOX_DIR / f"{qid}.md"
    if not p.exists():
        p = Path(qid)
    if not p.exists():
        print(f"Candidate not found: {qid}")
        return False
    if not str(reason or "").strip():
        print("--reject requires a reason (the audit trail must say why)")
        return False
    if dry_run:
        print(f"[dry-run] would reject {p.name}: {reason}")
        return True
    # Tombstone first (#140): rejection becomes negative evidence, not deletion
    try:
        from wiki_lib import tombstones as T
        from fabric_config import get_config, actor
        _cfg = get_config()
        fm_cand, _body = parse_frontmatter(p)
        sig = T._sig_tokens(_body or "")
        T.write_tombstone(CORPUS_ROOT, "chat-mined-pattern", fm_cand.get("id") or p.stem,
                          reason, sig, actor(_cfg, "process", model="promote-patterns"))
    except Exception as e:
        print(f"warn: tombstone not written: {e}", file=sys.stderr)
    p.unlink()
    print(f"rejected {qid}: {reason} (tombstone written to patterns/_rejected/)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Apply/reject chat-mined pattern candidates (human-gated; --auto is the judged confident tier, #190)")
    parser.add_argument("--list", action="store_true", help="List pending candidates (auto-tier verdicts annotated)")
    parser.add_argument("--apply", metavar="CANDIDATE", help="Apply a specific candidate (id)")
    parser.add_argument("--reject", metavar="ID", help="Reject a candidate (requires --reason)")
    parser.add_argument("--reason", help="Rejection reason (required with --reject)")
    parser.add_argument("--auto", action="store_true",
                        help="#190: judged auto-apply tier — preconditions + calibrated judgment band per candidate (needs tuning.promotion.auto_apply: true; G-J gated)")
    parser.add_argument("--unapply", metavar="CANONICAL",
                        help="#190: roll an auto-applied candidate back to the inbox (refuses non-auto-applied files)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.list:
        pending = list_pending()
        for p, fm in pending:
            note = _auto_note(fm)
            print(f"  ✎ {p.stem}  ({fm.get('origin', 'chat-mined')}) "
                  f"{str(fm.get('title', ''))[:70]}{note}")
        if not pending:
            print("  (no pending candidates — mine with: wf mine chats <project> --propose)")
        return

    if getattr(args, "unapply", None):
        ok = unapply(args.unapply, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    if args.auto:
        report = promote_auto(dry_run=args.dry_run)
        if args.dry_run:
            return
        import json as _json
        print(f"auto run: {len(report.get('applied', []))} applied, "
              f"{len(report.get('escalated', []))} escalated, "
              f"{len(report.get('stayed', []))} stayed, "
              f"{len(report.get('refused', []))} refused"
              + (f" (judge {report['judge']} @ {report['threshold']})" if report.get("judge") else ""))
        return

    if args.apply:
        p = INBOX_DIR / (args.apply if args.apply.endswith(".md") else f"{args.apply}.md")
        if not p.exists():
            print(f"Candidate not found: {args.apply}")
            sys.exit(1)
        ok = apply_candidate(p, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    if args.reject:
        ok = reject_candidate(args.reject, args.reason, dry_run=args.dry_run)
        sys.exit(0 if ok else 1)

    parser.print_help()


if __name__ == "__main__":
    main()