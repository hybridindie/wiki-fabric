#!/usr/bin/env python3
# gate.py — Aggregate human-in-the-loop decisions into one "action needed" report.
#
# Deterministic (0 tokens). Pulls every pending human gate — stale claims
# (review.py), promotion dossiers (promote.py), new domain proposals
# (propose-domains.py) — so an agent/hook can surface ONE report instead of
# remembering three commands.
#
# Usage:
#   python3 scripts/cmd/gate.py                     # full gate report (exit 1 if any action)
#   python3 scripts/cmd/gate.py --quiet             # only emit when something is actionable
#   python3 scripts/cmd/gate.py --json              # machine-readable (CI / hooks)
#
# Exit code: 0 = nothing pending; 1 = at least one HITL action needed.

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
import json
from datetime import date
from pathlib import Path



def _gate_review():
    """Reuse review.scan() — returns (pending, list)."""
    import review
    report = review.scan()
    pending = report.get("overdue", []) + report.get("stale", [])
    return pending, sorted(pending, key=lambda x: -x.get("overdue_days", 0))


def _gate_promotions():
    """Reuse promote.list_pending_promotions() — returns (pending, list)."""
    import promote
    dossiers = promote.list_pending_promotions()
    return dossiers, dossiers


def _gate_domains():
    """Reuse promote-domains.list_pending_proposals() — pending domain-merge
    dossiers awaiting human review. Returns (pending, ordered_display)."""
    import importlib
    promote_domains = importlib.import_module("promote-domains")
    dossiers = promote_domains.list_pending_proposals()
    return dossiers, dossiers


def _safe(fn):
    """Run a gate section; on failure report an error instead of crashing."""
    try:
        pending, full = fn()
        return pending, full, None
    except Exception as e:  # one broken queue must not crash the report
        return [], [], f"{fn.__name__}: {e}"


def gate():
    sections = {
        "review": _safe(_gate_review),
        "promotions": _safe(_gate_promotions),
        "domains": _safe(_gate_domains),
    }
    actionable = any(p for p, _, _ in sections.values())
    return sections, actionable

def _emit(sections, actionable, quiet=False):
    if quiet and not actionable:
        return
    if not actionable:
        print("gate: nothing pending — fabric is current (HITL queues empty)")
        return

    print("gate: action needed — the following want a human eye\n")
    rev, rev_list, rev_err = sections["review"]
    if rev:
        print(f"  Stale/overdue claims ({len(rev)}):")
        for item in rev_list[:10]:
            days = item.get("overdue_days", 0)
            name = Path(item.get("file", "")).name[:60]
            print(f"    ⚠ {days:3d}d  {name}")
    prom, prom_list, prom_err = sections["promotions"]
    if prom:
        print(f"  Pending pattern promotions ({len(prom)}):")
        for path, fm in prom_list[:10]:
            print(f"    ◆ {path.stem}  ({fm.get('status')})")
    dom, dom_list, dom_err = sections["domains"]
    if dom:
        print(f"  Pending domain proposals ({len(dom)}):")
        for path, fm in dom_list[:10]:
            print(f"    ▸ {path.name}  ({fm.get('domain')})")
    for section, (p, _, err) in sections.items():
        if err:
            print(f"  [{section} skipped: {err}]")
    print("\n  Resolve:  wf review --auto-reverify | wf promote --promote <dossier> | "
          "python3 scripts/cmd/promote-domains.py --apply <dossier>")


def main():
    import argparse
    from fabric_config import CORPUS_ROOT
    parser = argparse.ArgumentParser(description="Aggregate HITL decisions")
    parser.add_argument("--quiet", action="store_true", help="Emit only when actionable")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--write-manifest", action="store_true",
                        help="Persist a deterministic pending-manifest to registry/pending-gate.md "
                             "(read by the AI harness at session start)")
    args = parser.parse_args()

    sections, actionable = gate()

    if args.write_manifest:
        _write_manifest(CORPUS_ROOT / "registry" / "pending-gate.md", sections, actionable)

    if args.json:
        print(json.dumps({
            "actionable": actionable,
            "review": sections["review"][0],
            "promotions": [{"id": str(p.stem), "status": fm.get("status")}
                           for p, fm in sections["promotions"][1]],
            "domains": [{"id": str(p.stem), "domain": fm.get("domain")}
                        for p, fm in sections["domains"][1]],
            "errors": {k: v[2] for k, v in sections.items() if v[2]},
        }, indent=2))
    else:
        _emit(sections, actionable, quiet=args.quiet)

    sys.exit(1 if actionable else 0)


def _write_manifest(manifest_path, sections, actionable):
    """Deterministic, agent-readable manifest of pending human decisions. The
    git hook writes this so ANY harness (open, claude, codex, gemini, ...) can
    surface it at session start without running commands. 0 tokens.
    NOTE: `manifest_path` is intentionally distinct from the loop vars — a
    shadowed `path` here previously overwrote a real dossier. Never loop a
    variable named `path` in this function."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: registry",
        "title: Pending HITL Manifest",
        f"updated: {date.today().isoformat()}",
        "---",
        "",
        "# Pending Human Decisions",
        "",
    ]
    if not actionable:
        lines.append("No pending human decisions.")
    rev, rev_list, _ = sections["review"]
    if rev:
        lines.append(f"## Claims needing review ({len(rev)})")
        for item in rev_list[:10]:
            lines.append(f"- {Path(str(item.get('file',''))).name} "
                         f"{item.get('overdue_days',0)}d overdue")
        lines.append("")
    prom, prom_list, _ = sections["promotions"]
    if prom:
        lines.append(f"## Promotion dossiers awaiting review ({len(prom)})")
        for doss, fm in prom_list[:10]:
            lines.append(f"- {doss.stem} ({fm.get('status')})")
        lines.append("")
    dom, dom_list, _ = sections["domains"]
    if dom:
        lines.append(f"## Domain proposals awaiting approval ({len(dom)})")
        for doss, fm in dom_list[:10]:
            lines.append(f"- {doss.name} ({fm.get('domain')})")
        lines.append("")
    lines += [
        "To resolve: `wf review --auto-reverify` | `wf promote --promote <dossier>` | "
        "`python3 scripts/cmd/promote-domains.py --apply <dossier>`",
    ]
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_path


if __name__ == "__main__":
    main()
