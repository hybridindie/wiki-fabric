#!/usr/bin/env python3
# wiki_generate.py — the wiki-generation bookkeeper (#144 / living-wiki S2).
#
# Writer/bookkeeper split: the host coding agent (via MCP tools or CLI) writes
# prose; this module owns the durable queue, claim reconciliation, citation
# validation, and run state — deterministically, 0 LLM tokens. The agent
# submits SPARSE claim deltas (confirm/revise/add/retract); unaffected claims
# are retained deterministically, never re-flowed through a model.
#
# Lifecycle:
#   begin    — build the deterministic outline (STORM two-stage, 0 tokens):
#              topics → pages → section outlines with assigned claims.
#              Checkpointed at evidence/traces/wiki-runs/<id>/.run.json.
#   next     — pop the next pending page job (outline + claims to cite).
#   submit   — validate citation presence, reconcile claim deltas, write the
#              page (staged, provenance-stamped), mark done, checkpoint.
#   finish   — refuse while any page lacks durable state; else write summary.
#   inspect  — the full claim set assigned to a page (for broad rewrites).
#   resume   — .run.json is the state: begin on an open run resumes it.
#
# Page completion is the durability boundary: markdown + reconciled claim set
# + citation check + manifest entry. Interrupted runs resume without re-doing
# completed pages.
#
# Usage:
#   python3 scripts/cmd/wiki_generate.py begin --project <slug> [--topic <slug>]
#   python3 scripts/cmd/wiki_generate.py next
#   python3 scripts/cmd/wiki_generate.py submit --page <page-id> --file <draft.md>
#            [--confirm claim-id ...] [--retract claim-id ...] [--add file.md ...]
#   python3 scripts/cmd/wiki_generate.py finish
#   python3 scripts/cmd/wiki_generate.py status [--json]
#   python3 scripts/cmd/wiki_generate.py inspect --page <page-id>

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))

import argparse
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

from fabric_config import CORPUS_ROOT, get_config
from wf_common import parse_frontmatter

import layout

def _wiki_root():
    from fabric_config import get_vault_path
    v = get_vault_path()
    return (v / "wiki") if v else (CORPUS_ROOT / "wiki")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _runs_dir():
    d = layout.wiki_runs(CORPUS_ROOT)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _open_run():
    """The open (non-finished) run, if any. State = .run.json (durable)."""
    for d in sorted(_runs_dir().glob("run-*")):
        rp = d / ".run.json"
        if rp.exists():
            try:
                r = json.loads(rp.read_text(encoding="utf-8"))
                if r.get("status") in ("open", "writing"):
                    return d, r
            except Exception:
                continue  #continue  # corrupt bookkeeping state → not resumable here
    return None, None


def _checkpoint(run_dir, run):
    run["updated"] = _now()
    (run_dir / ".run.json").write_text(json.dumps(run, indent=1, sort_keys=True) + "\n",
                                       encoding="utf-8")


def _cite_claim(claim_id):
    return f"[[{claim_id}]]"


# ---- Deterministic outline (STORM two-stage, 0 tokens) ----------------------

def build_outline(project=None, min_claims=6):
    """Section outlines from concepts + their claims. Each page job carries:
    title, slug, ordered section list, and the claim set each section must
    cite (the reconciliation baseline). Pure graph reads — 0 tokens."""
    concepts = []
    for c in sorted((layout.concepts(CORPUS_ROOT)).glob("concept-*.md")):
        s = c.read_text(encoding="utf-8", errors="replace")
        title = re.search(r"^title: (.+)$", s, re.MULTILINE)
        claims = re.findall(r"\[\[(claim-[\w-]+)\]\]", s)
        if len(claims) >= min_claims:
            concepts.append({"slug": re.sub(r"[^a-z0-9-]+", "-", (title.group(1) if title else c.stem).lower()).strip("-"),
                             "title": title.group(1) if title else c.stem,
                             "claims": list(dict.fromkeys(claims)),
                             "body": s})
    pages = []
    for c in concepts:
        # section outline: intro (first half of claims) + takeaways (all) + sources
        half = max(1, len(c["claims"]) // 2)
        sections = [
            {"name": "summary", "claims": c["claims"][:half]},
            {"name": "key-takeaways", "claims": c["claims"]},
            {"name": "sources", "claims": c["claims"]},
        ]
        pages.append({"page": c["slug"], "title": c["title"], "sections": sections,
                      "claims": c["claims"], "status": "pending",
                      "deltas": {"confirm": [], "retract": [], "add": []}})
    return pages


# ---- Claim reconciliation (sparse deltas) ------------------------------------

def reconcile(baseline_claims, deltas):
    """Apply sparse deltas to a page's claim set. Unaffected claims are
    retained deterministically. Returns (final_claims, applied, rejected)."""
    claims = [c for c in baseline_claims if c not in deltas.get("retract", [])]
    for c in deltas.get("retract", []):
        if c not in baseline_claims:
            return None, [], [f"retract of unassigned claim {c}"]
    added = []
    for a in deltas.get("add", []):
        if a not in claims:
            added.append(a)
    applied = {"confirmed": deltas.get("confirm", []),
               "retracted": deltas.get("retract", []),
               "added": added}
    return claims + added, applied, []


# ---- Citation validation ------------------------------------------------------

def validate_citations(text, required_claims):
    """A generated page must cite its assigned claims (footnote or wikilink).
    Returns (ok, missing: list, cited: list)."""
    cited = set(re.findall(r"\[\[(claim-[\w-]+)\]\]", text))
    missing = [c for c in required_claims if c not in cited]
    return (not missing), missing, sorted(cited)


# ---- Lifecycle commands --------------------------------------------------------

def cmd_begin(args):
    run_dir, run = _open_run()
    if run_dir:
        done = sum(1 for p in run["pages"] if p["status"] == "done")
        print(f"Resuming open run {run_dir.name} ({done}/{run['total']} pages done)")
        return 0
    pages = build_outline(min_claims=args.min_claims)
    if not pages:
        print("No topics with enough claims — nothing to generate.", file=sys.stderr)
        return 1
    rid = _now().replace(":", "").replace("-", "")[:13]
    run_dir = _runs_dir() / f"run-{rid}"
    run_dir.mkdir(parents=True, exist_ok=True)
    run = {"id": f"run-{rid}", "status": "open", "task": args.task,
           "project": args.project, "started": _now(), "total": len(pages),
           "pages": pages}
    _checkpoint(run_dir, run)
    print(f"Run {run_dir.name}: outline built — {len(pages)} page(s), "
          f"{sum(len(p['claims']) for p in pages)} claim assignments")
    for p in pages:
        print(f"  - {p['page']} ({len(p['claims'])} claims)")
    print("Next: wiki_next → write the cited prose → wiki_submit --page <id> --file <draft>")
    return 0


def cmd_next(args):
    run_dir, run = _open_run()
    if not run_dir:
        print("No open run — start with: wiki_generate begin", file=sys.stderr)
        return 1
    for p in run["pages"]:
        if p["status"] == "pending":
            job = {"page": p["page"], "title": p["title"],
                   "sections": p["sections"], "claims": p["claims"],
                   "claims_baseline": p["claims"],
                   "run": run_dir.name,
                   "citation_rule": "every assigned claim must appear as [[claim-id]]"}
            print(json.dumps(job, indent=1))
            return 0
    print("All pages done — run: wiki_generate finish")
    return 0


def cmd_submit(args):
    run_dir, run = _open_run()
    if not run_dir:
        print("No open run.", file=sys.stderr)
        return 1
    page = next((p for p in run["pages"] if p["page"] == args.page), None)
    if not page:
        print(f"Page not in queue: {args.page}", file=sys.stderr)
        return 1
    if page["status"] == "done":
        print("Page already complete (durable) — skipping (no rework).")
        return 0
    src = Path(args.file)
    if not src.exists():
        print(f"Draft missing: {src}", file=sys.stderr)
        return 1
    text = src.read_text(encoding="utf-8")
    final_claims, applied, errors = reconcile(page["claims"], args.__dict__)
    if errors:
        for e in errors:
            print(f"delta error: {e}", file=sys.stderr)
        return 1
    # citation validation: every required claim must be cited
    ok, missing, cited = validate_citations(text, final_claims)
    if not ok:
        print(f"REJECTED: {len(missing)} assigned claim(s) not cited: "
              f"{', '.join(missing[:6])}{'…' if len(missing) > 6 else ''}", file=sys.stderr)
        print("Every assigned claim needs a [[claim-id]] citation (or retract it via --retract).",
              file=sys.stderr)
        return 1
    # durable page write
    out_dir = _wiki_root() / "staged" / run_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{page['page']}.md"
    out.write_text(text, encoding="utf-8")
    page["status"] = "done"
    page["deltas"] = applied
    page["file"] = str(out)
    page["cited"] = cited
    page["verified"] = {"citations": "ok", "checked": _now()}
    _checkpoint(run_dir, run)
    done = sum(1 for p in run["pages"] if p["status"] == "done")
    print(f"Page accepted: {page['page']} → {out}")
    print(f"  citations: {len(cited)}/{len(final_claims)} | durable boundary: done "
          f"({done}/{run['total']})")
    return 0


def cmd_finish(args):
    run_dir, run = _open_run()
    if not run_dir:
        print("No open run.", file=sys.stderr)
        return 1
    pending = [p["page"] for p in run["pages"] if p["status"] != "done"]
    if pending:
        print(f"REFUSED: {len(pending)} page(s) lack durable claim state: "
              f"{', '.join(pending[:5])}{'…' if len(pending) > 5 else ''}", file=sys.stderr)
        return 1
    run["status"] = "finished"
    run["finished"] = _now()
    _checkpoint(run_dir, run)
    n_claims = sum(len(p["claims"]) for p in run["pages"])
    print(f"Run {run_dir.name} finished: {run['total']} page(s), {n_claims} claim citations.")
    print("Pages are staged under wiki/staged/ — the change-set flow (lint + "
          "human gate) takes over from here.")
    return 0


def cmd_status(args):
    run_dir, run = _open_run()
    if args.json:
        print(json.dumps(run or {"status": "none"}, indent=1))
        return 0
    if not run_dir:
        print("No open run.")
        return 0
    done = sum(1 for p in run["pages"] if p["status"] == "done")
    print(f"{run_dir.name} — {run['task'] or '(no task)'} — {done}/{run['total']} pages durable")
    for p in run["pages"]:
        mark = "✓" if p["status"] == "done" else "·"
        print(f"  {mark} {p['page']}")
    return 0


def cmd_inspect(args):
    run_dir, run = _open_run()
    page = next((p for p in (run["pages"] if run else []) if p["page"] == args.page), None)
    if not page:
        print(f"Page not in queue: {args.page}", file=sys.stderr)
        return 1
    print(json.dumps({"page": page["page"], "claims": page["claims"],
                      "deltas": page.get("deltas", {})}, indent=1))
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Wiki-generation bookkeeper (writer/bookkeeper split, #144)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("begin", help="Build the deterministic outline and open a run (resumes if one is open)")
    b.add_argument("--project")
    b.add_argument("--task", default="wiki generation")
    b.add_argument("--min-claims", type=int, default=6)
    sub.add_parser("next", help="Emit the next pending page job (JSON)")
    s = sub.add_parser("submit", help="Submit a written page (citation-validated, durable)")
    s.add_argument("--page", required=True)
    s.add_argument("--file", required=True)
    s.add_argument("--confirm", nargs="*", default=[])
    s.add_argument("--retract", nargs="*", default=[])
    s.add_argument("--add", nargs="*", default=[])
    sub.add_parser("finish", help="Finish the run (refuses if any page is not durable)")
    st = sub.add_parser("status", help="Run status")
    st.add_argument("--json", action="store_true")
    i = sub.add_parser("inspect", help="Inspect a page's claim set")
    i.add_argument("--page", required=True)
    args = parser.parse_args()
    return {"begin": cmd_begin, "next": cmd_next, "submit": cmd_submit,
            "finish": cmd_finish, "status": cmd_status, "inspect": cmd_inspect}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())