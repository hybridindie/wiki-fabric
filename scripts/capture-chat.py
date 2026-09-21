#!/usr/bin/env python3
# capture-chat.py — Capture agent-harness chat sessions as raw evidence.
#
# Sources (auto-detected, composable with --harness):
#   opencode : ~/.local/share/opencode/opencode.db (SQLite: session/part)
#   claude   : ~/.claude/projects/<encoded-path>/*.jsonl
#   codex    : ~/.codex/sessions/*.jsonl (best-effort format)
#
# Usage:
#   python3 scripts/capture-chat.py <project> --since 30d [--limit 20]
#        [--harness opencode|claude|codex|all] [--min-turns 4] [--dry-run]
#        [--project-root /path/to/project]
#
# Writes evidence/raw/<project>/chats/<date>-<slug>.md (kind: chat-transcript).
# The normal pipeline takes over: sha256 anti-loop, claims with chat-line
# locators, human gate.

import sqlite3
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import get_config, resolve_repo_path, FABRIC_ROOT

MARKDOWN_FENCE = re.compile(r"```")


def _now_ms():
    return datetime.now(timezone.utc).timestamp() * 1000


def _parse_since(since):
    m = re.match(r"^(\d+)([dwy])$", since or "30d")
    if not m:
        raise SystemExit(f"invalid --since {since!r} (use e.g. 30d, 2w, 1y)")
    n, unit = int(m.group(1)), m.group(2)
    days = {"d": 1, "w": 7, "y": 365}[unit] * n
    return (datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000


def _slug(text, limit=60):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:limit] or "session"


def _md_escape(text):
    """Trim + fence-protect chat text (``` inside turns would break md blocks)."""
    text = (text or "").strip()
    return text.replace("```", "~~~")


def _render_opencode_session(db_path, session_id, min_turns):
    """Render one opencode session to markdown. Returns (md, meta) or None."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, CAST(data AS TEXT) FROM message WHERE session_id=? ORDER BY time_created",
            (session_id,)).fetchall()
        parts_rows = conn.execute(
            "SELECT message_id, CAST(data AS TEXT) FROM part WHERE session_id=? ORDER BY time_created",
            (session_id,)).fetchall()
    finally:
        conn.close()
    import json as _json
    parts_by_msg = {}
    for mid, data in parts_rows:
        try:
            parts_by_msg.setdefault(mid, []).append(_json.loads(data))
        except Exception:
            continue

    msgs = []
    for mid, data in rows:
        try:
            m = _json.loads(data)
            m["id"] = mid
            msgs.append(m)
        except Exception:
            continue

    user_turns = 0
    out = []
    for m in msgs:
        role = m.get("role")
        mid = m.get("id")
        plist = parts_by_msg.get(mid, [])
        if role == "user":
            texts = [p.get("text", "") for p in plist if p.get("type") == "text"]
            text = "\n".join(t for t in texts if t).strip()
            if text:
                user_turns += 1
                out.append(("user", text))
        elif role == "assistant":
            for p in plist:
                if p.get("type") == "text" and (p.get("text") or "").strip():
                    out.append(("assistant", p["text"].strip()))
                elif p.get("type") == "tool":
                    tool = p.get("tool", "?")
                    state = p.get("state", {})
                    cmd = (state.get("input") or {}).get("command") or ""
                    brief = f"[tool: {tool}] {str(cmd)[:160]}" if cmd else f"[tool: {tool}]"
                    out.append(("tool", brief))
    if user_turns < min_turns:
        return None
    return out, user_turns


def capture_opencode(project, project_root, raw_dir, since_ms, limit, min_turns, dry_run):
    db = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
    if not db.exists():
        print("  opencode: no database — skipping", file=sys.stderr)
        return []
    root = str(project_root)
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute(
            "SELECT id, directory, slug, time_created FROM session WHERE directory=? AND time_created >= ? "
            "ORDER BY time_created DESC LIMIT ?",
            (root, since_ms, limit * 3)).fetchall()
        meta = {r[0]: (r[1], r[2], r[3]) for r in rows}
    finally:
        conn.close()

    written = []
    for sid, (directory, slug, created_ms) in meta.items():
        rendered = _render_opencode_session(db, sid, min_turns)
        if not rendered:
            continue
        turns, user_turns = rendered
        if len(written) >= limit:
            break
        dt = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
        date = dt.strftime("%Y-%m-%d")
        first_user = next((t[:80] for r, t in turns if r == "user"), sid)
        slug = _slug(first_user)
        fname = f"{date}-chat-{slug}.md"
        out_path = raw_dir / fname
        if out_path.exists():
            continue  # anti-loop: session already captured
        lines = [f"# Chat session {sid} — {date}", "",
                 "## Metadata",
                 f"- Harness: opencode",
                 f"- Session: {sid}",
                 f"- Directory: {directory}",
                 f"- Date: {dt.isoformat()}",
                 f"- User turns: {user_turns}",
                 f"- Project: {project}",
                 "",
                 "## Transcript",
                 ""]
        for role, text in turns:
            label = "User" if role == "user" else ("Assistant" if role == "assistant" else "Tool")
            text = _md_escape(text)
            lines.append(f"### {label}")
            lines.append("")
            lines.append(text)
            lines.append("")
        md = "\n".join(lines)
        est_tokens = len(md) // 4
        if dry_run:
            print(f"  [DRY] {fname}: {len(turns)} turns, ~{est_tokens:,} extraction tokens")
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(md, encoding="utf-8")
            print(f"  captured {fname} ({user_turns} user turns, ~{est_tokens:,} tokens)")
        written.append(out_path)
    return written


def capture_claude(project, project_root, raw_dir, since_ms, limit, min_turns, dry_run):
    base = Path.home() / ".claude" / "projects"
    if not base.is_dir():
        return []
    # claude encodes the project path: /foo/bar -> -foo-bar
    encoded = str(project_root).replace("/", "-")
    matches = sorted(base.glob(encoded[1:] + "*" if encoded.startswith("-") else encoded))
    if not matches:
        return []
    written = []
    for jsonl in matches:
        if not jsonl.is_file():
            continue
        lines = jsonl.read_text(encoding="utf-8", errors="replace").splitlines()
        turns = []
        user_turns = 0
        for line in lines:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            role = rec.get("type")
            msg = rec.get("message") or {}
            content = msg.get("content")
            text = ""
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = "\n".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")
            if role == "user" and text.strip():
                user_turns += 1
                turns.append(("user", text.strip()))
            elif role == "assistant" and text.strip():
                turns.append(("assistant", text.strip()))
        if user_turns < min_turns or len(written) >= limit:
            continue
        date = datetime.fromtimestamp(jsonl.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
        slug = _slug(next((t[:80] for r, t in turns if r == "user"), jsonl.stem))
        out_path = raw_dir / f"{date}-chat-{slug}.md"
        if out_path.exists():
            continue
        md = [f"# Chat session {jsonl.stem} — {date}", "",
              "## Metadata",
              f"- Harness: claude",
              f"- Project: {project}",
              f"- User turns: {user_turns}",
              "", "## Transcript", ""]
        for role, text in turns:
            text = _md_escape(text)
            md.append(f"### {'User' if role == 'user' else 'Assistant'}")
            md.append("")
            md.append(text)
            md.append("")
        if dry_run:
            print(f"  [DRY] {out_path.name}: {user_turns} user turns")
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("\n".join(md), encoding="utf-8")
            print(f"  captured {out_path.name} ({user_turns} user turns)")
        written.append(out_path)
    return written


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Capture agent-harness chat sessions as raw evidence")
    parser.add_argument("project", help="Project slug")
    parser.add_argument("--since", default="30d", help="Window: 30d, 2w, 1y (default 30d)")
    parser.add_argument("--limit", type=int, default=20, help="Max sessions per harness")
    parser.add_argument("--min-turns", type=int, default=1, help="Skip sessions with fewer user turns")
    parser.add_argument("--harness", default="all", choices=["opencode", "claude", "codex", "all"])
    parser.add_argument("--project-root", default=None, help="Project dir (default: resolved from fabric.yaml)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = get_config()
    project_root = Path(args.project_root) if args.project_root else resolve_repo_path(config, args.project)
    if not project_root or not project_root.exists():
        print(f"Unknown project {args.project!r} (no repos entry / dir)", file=sys.stderr)
        return 2
    raw_dir = FABRIC_ROOT / "evidence" / "raw" / args.project / "chats"
    since_ms = _parse_since(args.since)

    print(f"=== Capturing chat sessions for {args.project} ===")
    print(f"  Window: since {args.since}, limit {args.limit}/harness, min {args.min_turns} user turns")
    print(f"  Project root: {project_root}")
    print()

    written = []
    if args.harness in ("opencode", "all"):
        written += capture_opencode(args.project, project_root, raw_dir, since_ms,
                                    args.limit, args.min_turns, args.dry_run)
    if args.harness in ("claude", "all"):
        written += capture_claude(args.project, project_root, raw_dir, since_ms,
                                  args.limit, args.min_turns, args.dry_run)

    print()
    if args.dry_run:
        print(f"[DRY RUN] {len(written)} session(s) would be captured")
    else:
        print(f"Capture summary: {len(written)} session(s) captured")
        if written:
            print("\nNext: ingest the captured transcripts:")
            print(f"  wf ingest 'evidence/raw/{args.project}/chats/'*.md --extract-claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())