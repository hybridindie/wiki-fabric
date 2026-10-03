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

import layout



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


def _gate_contributions(stale_days=30):
    """Contribution freshness per connected project (team-knowledge loop):
    a project whose last experience-event/capture is staler than stale_days
    is a knowledge source going dark — the chat-mining / git-capture channel
    may be idle on that machine. Deterministic; NOT actionable-by-command
    (info tier — the fix is a human conversation, not a script)."""
    import layout as _lay
    from datetime import timedelta
    from wf_common import parse_frontmatter as _pf
    from fabric_config import CORPUS_ROOT
    projects_dir = _lay.projects(CORPUS_ROOT)
    if not projects_dir.exists():
        return [], []
    cutoff = date.today() - timedelta(days=stale_days)
    rows = []
    for ns in sorted(projects_dir.iterdir()):
        if not ns.is_dir():
            continue
        last = None
        ev_dir = ns / "experience-events"
        if ev_dir.exists():
            for ev in ev_dir.glob("ee-*.md"):
                fm, _ = _pf(ev)
                stamp = str(fm.get("created") or "")[:10] or (ev.stem[3:13] if len(ev.stem) > 13 else "")
                if stamp > (last or ""):
                    last = stamp
        raw_root = _lay.evidence_raw(CORPUS_ROOT) / ns.name
        mark = raw_root / "git" / ".last-capture"
        try:
            stamp = mark.read_text().strip()[:10]
            if stamp and stamp > (last or ""):
                last = stamp
        except OSError:
            pass
        chats = raw_root / "chats"
        if chats.exists():
            for cf in chats.glob("*.md"):
                d = cf.stem[:10]
                if len(d) == 10 and d[4] == "-" and d > (last or ""):
                    last = d
        if last is None or last < cutoff.isoformat():
            rows.append({"project": ns.name, "last": last or "never",
                         "stale_days": None if last is None else (date.today() - date.fromisoformat(last)).days})
    return rows, rows


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
    dirs = [layout.registry(_C) / "receipts"]
    projects_root = layout.projects(_C)
    if projects_root.is_dir():
        dirs.extend(sorted(projects_root.glob("*/receipts")))
    for d in dirs:
        if not d.is_dir():
            continue
        for rp in sorted(d.glob("receipt-*.json")):
            try:
                data = _json.loads(rp.read_text(encoding="utf-8"))
            except Exception:
                continue  #continue  # torn receipt mid-write → not reportable this cycle
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


def _age_days_impl(fm, today):
    raw = str(fm.get("created") or "").strip()
    try:
        created = date.fromisoformat(raw[:10])
    except Exception:
        return None
    return (today - created).days


def _escalated(fm, threshold=None):
    """True when a pending artifact has waited past the escalation threshold
    (#174: the human queue can't rot invisibly — info → actionable on age).
    Threshold: tuning.escalation.days (default 7d)."""
    age = _age_days_impl(fm, date.today())
    if age is None:
        return False
    if threshold is None:
        from fabric_config import get_tuning
        threshold = int(get_tuning(None, "escalation", "days", 7))
    return age >= threshold


def gate():
    sections = {
        "review": _safe(_gate_review),
        "promotions": _safe(_gate_promotions),
        "domains": _safe(_gate_domains),
        "pattern-candidates": _safe(_gate_pattern_candidates),
        "questions": _safe(_gate_questions),
        "contributions": _safe(_gate_contributions),
    }
    # contributions are INFO (no command resolves them); they never make the
    # gate actionable on their own — actionable = every OTHER section pending.
    actionable = any(p for k, (p, _, _) in sections.items()
                     if k != "contributions" and p)
    return sections, actionable

def _emit(sections, actionable, quiet=False):
    contrib, contrib_list, contrib_err = sections.get("contributions", ([], [], None))
    if quiet and not actionable:
        if contrib_list:
            _emit_contributions(contrib_list)
        return
    if not actionable:
        print("gate: nothing pending — fabric is current (HITL queues empty)")
        if contrib_list:
            _emit_contributions(contrib_list)
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
        n_esc = sum(1 for _, fm in prom_list if _escalated(fm))
        print(f"  Pending pattern promotions ({len(prom)})"
              + (f" — {n_esc} ESCALATED (waiting > threshold)" if n_esc else "") + ":")
        for path, fm in prom_list[:10]:
            esc = "  ⏰ ESCALATED" if _escalated(fm) else ""
            print(f"    ◆ {path.stem}  ({fm.get('status')}){esc}")
    dom, dom_list, dom_err = sections["domains"]
    if dom:
        print(f"  Pending domain proposals ({len(dom)}):")
        for path, fm in dom_list[:10]:
            print(f"    ▸ {path.name}  ({fm.get('domain')})")
    pcand, pclist, pc_err = sections["pattern-candidates"]
    if pcand:
        n_esc = sum(1 for _, fm in pclist if _escalated(fm))
        print(f"  Chat-mined pattern candidates ({len(pcand)})"
              + (f" — {n_esc} ESCALATED (waiting > threshold)" if n_esc else "") + ":")
        for path, fm in pclist[:10]:
            esc = "  ⏰ ESCALATED" if _escalated(fm) else ""
            print(f"    ◆ {path.stem}  ({fm.get('origin', 'chat-mined')}){esc}")
    qpending, qopen, q_err = sections["questions"]
    if qpending:
        print(f"  Open questions awaiting triage ({len(qpending)}):")
        for path, fm in qpending[:10]:
            print(f"    ? {path.stem}  ({fm.get('priority')}) {str(fm.get('question', ''))[:60]}")
    if contrib_list:
        _emit_contributions(contrib_list)
    for section, (p, _, err) in sections.items():
        if err:
            print(f"  [{section} skipped: {err}]")
    print("\n  Resolve:  wf review --auto-reverify | wf promote --promote <dossier> | "
          "wf promote-domains --apply <dossier> | "
          "wf promote-questions --apply <id> --reject <id> --reason <why> | "
          "wf promote-patterns --apply <id> --reject <id> --reason <why>")




def _emit_contributions(rows):
    """Team-knowledge loop (info tier): which connected projects have gone
    dark — no experience-event, chat capture, or git capture within the
    window. The fix is a conversation with the project's owner, not a
    command; actionable is deliberately untouched."""
    stale = [r for r in rows if r.get("stale_days") is not None]
    silent = [r for r in rows if r.get("stale_days") is None]
    if stale:
        print(f"\n  Knowledge sources going dark ({len(stale)} — no contribution in 30d):")
        for r in stale[:10]:
            print(f"    ○ {r['project']:24} last: {r['last']} ({r['stale_days']}d ago)")
        print("    (remedy: wf capture chat <slug> / wf log --project <slug> on the owning "
              "machine, then wf sync push)")
    if silent:
        print(f"\n  Connected projects with no captured history at all ({len(silent)}):")
        for r in silent[:10]:
            print(f"    ○ {r['project']:24} no experience-events, chats, or git captures")


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


def _notify(manifest_path, sections, _log_prefix="[gate notify]", summary=None):
    """Gate notification seam (#67, loudness round 2026-09-30): push pending
    decisions to where the human is. Adapters (fabric.yaml notify:):
      kind: webhook   url_env (default WF_GATE_WEBHOOK_URL)
      kind: macos     osascript display notification (macOS only)
      kind: terminal  stderr banner + bell — the always-on default
    Opt-out: notify: [] (silences terminal too — the manifest stays the record).
    Payload: selection facts (what, why, evidence), never hidden reasoning.
    Deterministic, fire-and-forget; notification failure never fails the gate."""
    import urllib.request
    from fabric_config import get_config as _get_config
    try:
        cfg = _get_config()
    except Exception as e:
        print(f"{_log_prefix} disabled (config unreadable: {e})", file=sys.stderr)
        return
    adapters = cfg.get("notify")
    summary = summary or {k: len(v[1]) for k, v in sections.items() if isinstance(v, tuple) and v[1]}
    if adapters is None:
        # no config → the no-setup default: terminal banner (+ macOS bump if possible)
        _notify_terminal(summary, _log_prefix)
        if sys.platform == "darwin":
            _notify_macos(summary, _log_prefix)
        return
    for adapter in adapters or []:
        if not isinstance(adapter, dict):
            continue
        kind = adapter.get("kind")
        if kind == "webhook":
            import os
            url_env = adapter.get("url_env", "WF_GATE_WEBHOOK_URL")
            url = os.environ.get(url_env)
            if not url:
                continue
            try:
                payload = json.dumps({
                    "kind": "wiki-fabric-gate",
                    "manifest": manifest_path.read_text(encoding="utf-8", errors="replace")[:8000] if manifest_path and manifest_path.exists() else "",
                    "summary": summary,
                }).encode()
                req = urllib.request.Request(url, data=payload,
                                             headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    print(f"{_log_prefix} webhook {url} -> {resp.status}")
            except Exception as e:
                print(f"{_log_prefix} webhook failed: {e}")
        elif kind == "macos":
            _notify_macos(summary, _log_prefix)
        elif kind == "terminal":
            _notify_terminal(summary, _log_prefix)


def _notify_terminal(summary, _log_prefix="[gate notify]"):
    """stderr banner + bell: reaches the user of THIS command, every time."""
    if not summary:
        return
    hits = ", ".join(f"{k}: {n}" for k, n in summary.items() if n)
    sys.stderr.write(f"\a{_log_prefix} human decisions pending — {hits} "
                     f"(wf gate)\n")


def _notify_macos(summary, _log_prefix="[gate notify]"):
    """macOS notification center via osascript (best-effort)."""
    if sys.platform != "darwin" or not summary:
        return
    try:
        import subprocess
        hits = ", ".join(f"{n} {k}" for k, n in list(summary.items())[:3] if n)
        script = (
            'display notification "' + hits.replace('"', "'") +
            ' — run: wf gate" with title "wiki-fabric" sound name "Pop"')
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
    except Exception:
        pass

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

    manifest_path = layout.registry(CORPUS_ROOT) / "pending-gate.md"
    if args.write_manifest:
        _write_manifest(manifest_path, sections, actionable)
        if actionable:
            _notify(manifest_path, sections)

    if args.json:
        def _aged(entries):
            out = []
            for p, fm in entries:
                age = _age_days_impl(fm, date.today())
                out.append({"id": str(p.stem),
                            "age_days": age,
                            "escalated": _escalated(fm)})
            return out
        print(json.dumps({
            "actionable": actionable,
            "review": sections["review"][0],
            "promotions": [{**{"id": str(p.stem), "status": fm.get("status")},
                             "age_days": _age_days_impl(fm, date.today()),
                             "escalated": _escalated(fm)}
                           for p, fm in sections["promotions"][1]],
            "domains": [{"id": str(p.stem), "domain": fm.get("domain")}
                        for p, fm in sections["domains"][1]],
            "pattern-candidates": _aged(sections["pattern-candidates"][1]),
            "escalation_threshold_days": int(
                __import__("fabric_config").get_tuning(None, "escalation", "days", 7)),
            "contributions": sections["contributions"][1],
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
        n_esc = sum(1 for _, fm in prom_list if _escalated(fm))
        lines.append(f"## Promotion dossiers awaiting review ({len(prom)})"
                     + (f" — {n_esc} ESCALATED (waiting > escalation threshold)" if n_esc else ""))
        for doss, fm in prom_list[:10]:
            age = _age_days_impl(fm, date.today())
            esc = " ESCALATED" if _escalated(fm) else ""
            lines.append(f"- {doss.stem} ({fm.get('status')}{esc}"
                         + (f", waiting {age}d" if age is not None else "") + ")")
        lines.append("")
    dom, dom_list, _ = sections["domains"]
    if dom:
        lines.append(f"## Domain proposals awaiting approval ({len(dom)})")
        for doss, fm in dom_list[:10]:
            lines.append(f"- {doss.name} ({fm.get('domain')})")
        lines.append("")
    pcand, pclist, _ = sections.get("pattern-candidates", ([], [], None))
    if pcand:
        # was manifest-missing entirely (candidates visible only in prose) —
        # #174: the persisted record must show the inbox too, aged + escalated
        n_esc = sum(1 for _, fm in pclist if _escalated(fm))
        lines.append(f"## Chat-mined pattern candidates (patterns/_inbox/) ({len(pcand)})"
                     + (f" — {n_esc} ESCALATED (waiting > escalation threshold)" if n_esc else ""))
        for p, fm in pclist[:10]:
            age = _age_days_impl(fm, date.today())
            esc = " ESCALATED" if _escalated(fm) else ""
            lines.append(f"- {p.stem} (candidate{esc}"
                         + (f", waiting {age}d" if age is not None else "") + ")")
        lines.append("")
    contrib, contrib_list, _ = sections.get("contributions", ([], [], None))
    if contrib_list:
        lines.append("## Knowledge sources going dark (info — team-knowledge loop)")
        for r in contrib_list[:10]:
            if r.get("stale_days") is not None:
                lines.append(f"- {r['project']}: last contribution {r['last']} "
                             f"({r['stale_days']}d ago) — chat-mining/capture may be idle")
            else:
                lines.append(f"- {r['project']}: no captured history (experience-events/chats/git)")
        lines.append("")
    lines += [
        "To resolve: `wf review --auto-reverify` | `wf promote --promote <dossier>` | "
        "`wf promote-domains --apply <dossier>` | `wf promote-questions --apply <id>`",
    ]
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_path


if __name__ == "__main__":
    main()