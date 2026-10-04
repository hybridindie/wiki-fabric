#!/usr/bin/env python3
# always_on.py — write/remove the wiki-fabric always-on instruction block in
# CLAUDE.md / AGENTS.md (project or user level). Modeled on graphify's
# `claude install` / `graphify claude install`.
#
# Usage:
#   python3 scripts/harness/always_on.py install [--file CLAUDE.md|AGENTS.md] [--user]
#   python3 scripts/harness/always_on.py uninstall [--file ...] [--user]
#   python3 scripts/harness/always_on.py status [--file ...] [--user]

import re
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import argparse
from pathlib import Path

BLOCK_START = "## wiki-fabric"
MARKER_START = "<!-- wiki-fabric-always-on-start -->"
MARKER_END = "<!-- wiki-fabric-always-on-end -->"

_FABRIC_ROOT = _HERE.parent.parent  # scripts/harness → ../.. = repo root
_tpl = (_FABRIC_ROOT / "system" / "always-on" / "wiki-fabric-block.md").read_text(
    encoding="utf-8"
).strip()
# Strip the template's own frontmatter (lint contract only); the managed block
# is instructions, not a fabric note.
_tpl = re.sub(r"^---\n.*?\n---\n", "", _tpl, flags=re.DOTALL).strip()
_BLOCK_TEMPLATE = _tpl


def _target(path_arg: str | None, user: bool) -> Path:
    if path_arg:
        return Path(path_arg)
    if user:
        candidates = [Path.home() / ".claude" / "CLAUDE.md", Path.home() / "CLAUDE.md"]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]
    # project level: AGENTS.md preferred, CLAUDE.md fallback
    for name in ("AGENTS.md", "CLAUDE.md"):
        if Path(name).exists():
            return Path(name)
    return Path("AGENTS.md")


def _cwd_project_slug():
    try:
        from wf_common import parse_frontmatter as _pf
        from pathlib import Path as _P
        for name in (".wiki-overlay.md",):
            p = _P.cwd() / name
            if p.exists():
                fm, _ = _pf(p)
                return str(fm.get("namespace") or fm.get("project") or "") or None
    except Exception:
        pass
    return None


def _block_text(project=None) -> str:
    base = f"{MARKER_START}\n{_BLOCK_TEMPLATE.strip()}\n{MARKER_END}"
    proj = project or (_cwd_project_slug() if "standing_rules_block" in globals() else None)
    rules = standing_rules_block(proj) if "standing_rules_block" in globals() else ""
    return base + ("\n\n" + rules if rules else "")


def _has_marker(content: str) -> bool:
    return MARKER_START in content


def install(path: Path) -> str:
    if path.exists():
        content = path.read_text(encoding="utf-8")
        if "wiki-fabric" in content and not _has_marker(content):
            return f"already registered in {path} (wiki-fabric mentioned; no marker — skipping to avoid duplication)"
        if _has_marker(content):
            # refresh in place (block content may have been updated)
            new = re.sub(
                rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}",
                _block_text(), content, flags=re.DOTALL,
            )
            if new == content:
                return f"already installed in {path}"
            path.write_text(new, encoding="utf-8")
            return f"updated block in {path}"
        new = content.rstrip() + "\n\n" + _block_text() + "\n"
        path.write_text(new, encoding="utf-8")
        return f"appended block to {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_block_text() + "\n", encoding="utf-8")
    return f"created {path}"


def uninstall(path: Path) -> str:
    if not path.exists():
        return f"no {path} — nothing to remove."
    content = path.read_text(encoding="utf-8")
    if not _has_marker(content):
        return f"wiki-fabric block not found in {path}."
    new = re.sub(rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}\n?", "", content, flags=re.DOTALL).strip()
    path.write_text(new + "\n", encoding="utf-8")
    return f"removed block from {path}"


def status(path: Path) -> str:
    if not path.exists():
        return f"{path}: not present (not installed)"
    content = path.read_text(encoding="utf-8")
    out = ""
    if _has_marker(content):
        out += f"{path}: installed"
    elif "wiki-fabric" in content:
        out += f"{path}: wiki-fabric mentioned but no managed block"
    else:
        out += f"{path}: not installed"
    # other detected managed blocks (co-existence audit)
    others = []
    for tool, marker in (("graphify", "## graphify"), ("opencode", "## opencode")):
        if marker in content and "wiki-fabric" not in content:
            others.append(marker[2:])
        elif marker in content:
            others.append(marker)
    others = sorted(set(others) - {"## wiki-fabric"})
    if others:
        out += f"\nother managed blocks detected: {', '.join(others)}"
    return out


def main():
    parser = argparse.ArgumentParser(description="wiki-fabric always-on instructions")
    parser.add_argument("cmd", choices=["install", "uninstall", "status"])
    parser.add_argument("--file", help="Target file (default: AGENTS.md/CLAUDE.md project-level, ~/.claude/CLAUDE.md with --user)")
    parser.add_argument("--user", action="store_true", help="Install at user level (~/.claude/CLAUDE.md)")
    args = parser.parse_args()

    target = _target(args.file, args.user)
    if args.cmd == "install":
        print(install(target))
    elif args.cmd == "uninstall":
        print(uninstall(target))
    else:
        print(status(target))


if __name__ == "__main__":
    main()

# === Standing rules (#178-A): the corpus's promoted rules rendered in the
# managed block — the multi-project parity layer (rendered, source-linked,
# regenerated on every install/update; ABSENT when nothing qualifies) =======

RULES_MARKER_START = "<!-- wiki-fabric-rules-start -->"
RULES_MARKER_END = "<!-- wiki-fabric-rules-end -->"


def standing_rules_block(project=None, corpus_root=None):
    """The corpus's PROMOTED patterns (maturity >= recommended) + due
    commitments, rendered into a managed marker block. Deterministic (render
    joins, 0 tokens); the corpus is the single truth; absent when nothing
    qualifies. Every rule carries its source page (agents cite provenance)."""
    import re as _re
    try:
        from wf_common import parse_frontmatter as _pf
        import layout as _lay
        from fabric_config import CORPUS_ROOT as _c, get_repo_config as _rconf
        corpus = corpus_root or _c
        patterns_dir = _lay.patterns(corpus)
        rules = []
        if patterns_dir.is_dir():
            for pf in sorted(patterns_dir.glob("pattern-*.md")):
                text = pf.read_text(encoding="utf-8", errors="replace")
                st_m = _re.search(r"^status: (\S+)$", text, _re.M)
                st = (st_m.group(1) if st_m else "candidate")
                if st not in ("recommended", "standard"):
                    continue  # promoted set only (candidates stay pull-only)
                t_m = _re.search(r"^title: (.+)$", text, _re.M)
                title = (t_m.group(1).strip() if t_m else pf.stem)
                scope_m = _re.search(r"^project: (\S+)$", text, _re.M)
                if scope_m and project and scope_m.group(1) != project:
                    continue  # project-scoped elsewhere
                rules.append((pf.stem, title, st))
        lines = []
        if rules:
            lines += ["", "## Standing rules (wiki-fabric corpus)", ""]
            for stem, title, st in rules[:10]:
                lines.append(f"- **{title}** `[{st}]` — source: `{stem}` "
                             "(the pattern page is the truth; this file regenerates)")
        # due commitments (prospective memory, compact)
        try:
            shown = 0
            total = 0
            for cdir in sorted((_lay.projects(corpus)).glob("*/commitments")):
                if not cdir.is_dir():
                    continue
                for cm in sorted(cdir.glob("*.md")):
                    cfm, _ = _pf(cm)
                    if str(cfm.get("status") or "open").lower() not in ("open", "", "none"):
                        continue
                    total += 1
                    if shown < 3:
                        lines.append(f"- ⏳ commitment: {str(cfm.get('title') or cm.stem)[:80]} — [[{cm.stem}]]")
                        shown += 1
            if total > shown:
                lines.append(f"- ⏳ +{total - shown} more open commitments — surfaces in `wf context` by trigger")
        except Exception:
            pass
        if not lines:
            return ""
        return f"{RULES_MARKER_START}\n" + "\n".join(lines) + f"\n{RULES_MARKER_END}"
    except Exception:
        return ""  # the corpus's absence never breaks the install flow
