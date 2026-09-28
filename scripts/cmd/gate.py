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
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
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


def _gate_pattern_candidates():
    """#89: chat-mined pattern candidates awaiting human review
    (patterns/_inbox/ staged by mine-chats --propose)."""
    import importlib
    promote_patterns = importlib.import_module("promote-patterns")
    pending = promote_patterns.list_pending()
    return pending, pending


def _gate_questions():
    """#88: harvested open questions awaiting triage (staging proposals +
    canonical open questions). Returns (pending, open_qs)."""
    import importlib
    promote_questions = importlib.import_module("promote-questions")
    pending = promote_questions.list_pending()
    open_qs = promote_questions.list_open_questions()
    return pending, open_qs


def _recent_deliveries(limit=10):
    """#87: recent context receipts — 'these tasks ran with this knowledge'.
    The review question: was the manifest right? Provenance only; never scored.
    Returns newest-first [{receipt_id, task, namespace, compiled, path}]."""
    from fabric_config import get_CORPUS_ROOT_or_none
    _C = get_CORPUS_ROOT_or_none()
    import json as _json
    seen = {}
    if _C is None:
        return []
    dirs = [_C / "registry" / "receipts"]
    projects_root = _C / "projects"
    if projects_root.is_dir():
        dirs.extend(sorted(projects_root.glob("*/receipts")))
    for d in dirs:
        if not d.is_dir():
            continue
        for rp in sorted(d.glob("receipt-*.json")):
            try:
                data = _json.loads(rp.read_text(encoding="utf-8"))
            except Exception:
                continue
            rid = data.get("receipt_id") or rp.stem
            seen.setdefault(rid, {
                "receipt_id": rid,
                "task": str(data.get("task", ""))[:70],
                "namespace": data.get("namespace", ""),
                "compiled": data.get("compiled", ""),
                "path": rp,
            })
    return sorted(seen.values(), key=lambda x: str(x.get("compiled", "")), reverse=True)[:limit]


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
        "pattern-candidates": _safe(_gate_pattern_candidates),
        "questions": _safe(_gate_questions),
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
    pcand, pclist, pc_err = sections["pattern-candidates"]
    if pcand:
        print(f"  Chat-mined pattern candidates ({len(pcand)}):")
        for path, fm in pclist[:10]:
            print(f"    ◆ {path.stem}  ({fm.get('origin', 'chat-mined')})")
    qpending, qopen, q_err = sections["questions"]
    if qpending:
        print(f"  Open questions awaiting triage ({len(qpending)}):")
        for path, fm in qpending[:10]:
            print(f"    ? {path.stem}  ({fm.get('priority')}) {str(fm.get('question', ''))[:60]}")
    for section, (p, _, err) in sections.items():
        if err:
            print(f"  [{section} skipped: {err}]")
    print("\n  Resolve:  wf review --auto-reverify | wf promote --promote <dossier> | "
          "python3 scripts/cmd/promote-domains.py --apply <dossier> | "
          "python3 scripts/cmd/promote-questions.py --apply <id> --reject <id> --reason <why> | "
          "python3 scripts/cmd/promote-patterns.py --apply <id> --reject <id> --reason <why>")




def _emit_deliveries(deliveries):
    """#87 delivery-review surface: recent receipts, newest first. The review
    question is 'was the manifest right?' — provenance artifacts only, the
    gate never scores them (human gate unchanged)."""
    if not deliveries:
        print("gate: no context receipts on record yet")
        print("  Agents record one per delivery: wf context --write-receipt (0 extra cost)")
        return
    print("Recent deliveries (context receipts, newest first):\n")
    for d in deliveries:
        print(f"  □ {d['receipt_id']}  [{d['namespace']}]  {d['compiled']}  {d['task']}")
    print("\n  Review: was the manifest right? Link outcomes: wf log --project <slug> --receipt <id>")


def _notify(manifest_path, sections, _log_prefix="[gate notify]"):
    """Gate notification seam (#67): push pending decisions to where the human is.

    Opt-in via fabric.yaml notify: adapters — the payload is the manifest
    content (selection facts: what, why, evidence), never hidden reasoning.
    Deterministic, fire-and-forget; notification failure never fails the gate."""
    import urllib.request
    from fabric_config import get_config as _get_config
    try:
        cfg = _get_config()
    except Exception as e:
        print(f"{_log_prefix} disabled (config unreadable: {e})", file=sys.stderr)
        return
    for adapter in (cfg.get("notify") or []):
        if not isinstance(adapter, dict) or adapter.get("kind") != "webhook":
            continue
        import os
        url_env = adapter.get("url_env", "WF_GATE_WEBHOOK_URL")
        url = os.environ.get(url_env)
        if not url:
            continue
        try:
            payload = json.dumps({
                "kind": "wiki-fabric-gate",
                "manifest": manifest_path.read_text(encoding="utf-8", errors="replace")[:8000],
                "summary": {k: len(v[1]) for k, v in sections.items() if v[1]},
            }).encode()
            req = urllib.request.Request(url, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"{_log_prefix} webhook {url} -> {resp.status}")
        except Exception as e:
            print(f"{_log_prefix} webhook failed: {e}")

def main():
    import argparse
    from fabric_config import CORPUS_ROOT
    parser = argparse.ArgumentParser(description="Aggregate HITL decisions")
    parser.add_argument("--quiet", action="store_true", help="Emit only when actionable")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--write-manifest", action="store_true",
                        help="Persist a deterministic pending-manifest to registry/pending-gate.md "
                             "(read by the AI harness at session start)")
    parser.add_argument("--deliveries", action="store_true",
                        help="Surface recent context receipts (#87): 'these tasks ran with this knowledge' — review was the manifest right?")
    args = parser.parse_args()

    sections, actionable = gate()

    if args.deliveries:
        _emit_deliveries(_recent_deliveries())
        sys.exit(0)

    manifest_path = CORPUS_ROOT / "registry" / "pending-gate.md"
    if args.write_manifest:
        _write_manifest(manifest_path, sections, actionable)
        if actionable:
            _notify(manifest_path, sections)

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
