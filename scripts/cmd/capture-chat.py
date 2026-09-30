#!/usr/bin/env python3
# capture-chat.py — Capture agent-harness chat sessions as raw evidence.
#
# Sources (auto-detected, composable with --harness):
#   opencode : ~/.local/share/opencode/opencode.db (SQLite: session/part)
#   claude   : ~/.claude/projects/<encoded-path>/*.jsonl
#   codex    : ~/.codex/sessions/*.jsonl (best-effort format)
#
# Usage:
#   python3 scripts/cmd/capture-chat.py <project> --since 90d [--limit 20]
#        [--harness opencode|claude|codex|gemini|all] [--min-turns 4] [--dry-run]
#        [--project-root /path/to/project]
#
# Writes evidence/raw/<project>/chats/<date>-<slug>.md (kind: chat-transcript).
# The normal pipeline takes over: sha256 anti-loop, claims with chat-line
# locators, human gate.

import sqlite3
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone

from fabric_config import get_config, resolve_repo_path, FABRIC_ROOT, CORPUS_ROOT

MARKDOWN_FENCE = re.compile(r"```")
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
    return text.replace("```", "~~~")


# === Thread structure (#102): captures are graph nodes, not flat text ===
# Deterministic, 0 tokens: the metadata chat capture already knows (session,
# harness, files touched via tool calls) goes into frontmatter so the thread
# index and retrieval can traverse it. Provenance only — never content claims.

_FILES_TOOL_KEYS = {
    # opencode tool name → input key carrying a repo file path (live-verified)
    "read": "filePath",
    "edit": "filePath",
    "write": "filePath",
}


def _opencode_files_touched(parts_by_msg):
    """Relative project paths from tool-call parts (read/edit/write only).
    Deterministic projection of tool inputs; bash commands are NOT parsed."""
    files = []
    for plist in parts_by_msg.values():
        for p in plist:
            if p.get("type") != "tool":
                continue
            tool = str(p.get("tool", "")).lower()
            key = _FILES_TOOL_KEYS.get(tool)
            if not key:
                continue
            fp = str(((p.get("state") or {}).get("input") or {}).get(key) or "").strip()
            if fp:
                files.append(fp)
    return files


def capture_frontmatter(kind, project, session, harness, created_iso=None,
                        files_touched=None, extra=None):
    """Frontmatter block for a captured session/PR (#102). The file IS the
    graph node; derived indices read this, never the body."""
    # dedupe preserving order (a session touching context.py 8 times lists it once)
    seen, uniq = set(), []
    for f in files_touched or []:
        rel = fp_rel(f)
        if rel not in seen:
            seen.add(rel)
            uniq.append(rel)
    lines = ["---",
             "type: source",
             f"kind: {kind_of(harness)}",
             f"harness: {harness}",
             f"session: \"{session}\"",
             f"project: {project}"]
    if created_iso:
        lines.append(f"session_started: {created_iso}")
    if uniq:
        lines.append("files_touched:")
        for f in uniq[:20]:
            lines.append(f"  - \"{f}\"")
    for k, v in (extra or {}).items():
        if v is None:
            continue
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v[:20]:
                lines.append(f"  - \"{item}\"")
        else:
            lines.append(f"{k}: \"{v}\"")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def kind_of(harness):
    return "chat-session"


def fp_rel(f):
    """Normalize a file path for the index: absolute project paths →
    project-relative tail (deterministic, best-effort)."""
    f = str(f).replace("\\", "/")
    # strip the workspace root when present (opencode paths are absolute)
    root = str(getattr(_project_root_for_rel, "value", "") or "").rstrip("/") + "/"
    if root and f.startswith(root):
        return f[len(root):]
    for marker in ("/mcp_server/", "/scripts/", "/docs/", "/tests/", "/src/"):
        i = f.find(marker)
        if i > 0:
            return f[i + 1:]
    return f


def _set_rel_root(project_root):
    _project_root_for_rel.value = str(project_root)


class _project_root_for_rel:
    value = ""


def find_thread_links(session_id, transcript_text, other_sessions):
    """#102c: explicit thread links — sessions whose ids appear in the
    transcript (continuations, references) or a shared summary line.
    Deterministic substring scan; edges only when the reference is exact."""
    linked = []
    for other in other_sessions:
        if other == session_id:
            continue
        if other in transcript_text:
            linked.append(other)
    return linked


def _render_opencode_session(db_path, session_id, min_turns):
    """Render one opencode session to markdown.
    Returns (turns, user_turns, files_touched) or None."""
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
            continue  # malformed JSONL line — transcripts are skip-tolerant by design

    msgs = []
    for mid, data in rows:
        try:
            m = _json.loads(data)
            m["id"] = mid
            msgs.append(m)
        except Exception:
            continue  # malformed record — skip-tolerant (see :180)

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
    files = _opencode_files_touched(parts_by_msg)
    return out, user_turns, files


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
    session_ids = list(meta.keys())
    for sid, (directory, slug, created_ms) in meta.items():
        rendered = _render_opencode_session(db, sid, min_turns)
        if not rendered:
            continue
        turns, user_turns, files_touched = rendered
        if len(written) >= limit:
            break
        # thread edges (#102c): references to other captured sessions
        transcript_text = "\n".join(t for _, t in turns)
        links = find_thread_links(sid, transcript_text, session_ids)
        dt = datetime.fromtimestamp(created_ms / 1000, tz=timezone.utc)
        date = dt.strftime("%Y-%m-%d")
        first_user = next((t[:80] for r, t in turns if r == "user"), sid)
        slug = _slug(first_user)
        fname = f"{date}-chat-{slug}.md"
        out_path = raw_dir / fname
        if out_path.exists():
            continue  # anti-loop: session already captured
        lines = [capture_frontmatter("chat-session", project, sid, "opencode",
                                     created_iso=dt.isoformat(),
                                     files_touched=files_touched,
                                     extra={"related_sessions": links} if links else None),
                 f"# Chat session {sid} — {date}", "",
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
        files_touched = []
        _CLAUDE_FILE_TOOLS = {"Read", "Edit", "Write", "NotebookEdit"}
        for line in lines:
            try:
                rec = json.loads(line)
            except Exception:
                continue  # malformed JSONL line — skip-tolerant (see :181)
            role = rec.get("type")
            msg = rec.get("message") or {}
            content = msg.get("content")
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") in _CLAUDE_FILE_TOOLS:
                        fp = str((c.get("input") or {}).get("filePath") or (c.get("input") or {}).get("file_path") or "").strip()
                        if fp:
                            files_touched.append(fp)
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
        md = [capture_frontmatter("chat-session", project, jsonl.stem, "claude",
                                  created_iso=date,
                                  files_touched=sorted(set(files_touched))),
              f"# Chat session {jsonl.stem} — {date}", "",
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


def capture_codex(project, project_root, raw_dir, since_ms, limit, min_turns, dry_run):
    """Capture Codex CLI sessions from ~/.codex/sessions/**/*.jsonl (#113).

    Schema (claude-mem's transcript-watch 0.3, verified against their docs):
      type: session_meta  → payload.id, payload.cwd
      type: turn_context  → payload.cwd
      payload.type: user_message  → payload.message
      payload.type: agent_message → payload.message
      payload.type: function_call/custom_tool_call/web_search_call
                    → payload.name/arguments (tool use, call_id)
      payload.type: function_call_output/custom_tool_call_output → payload.output
    """
    base = Path.home() / ".codex" / "sessions"
    if not base.is_dir():
        print("  codex: no ~/.codex/sessions — skipping", file=sys.stderr)
        return []
    # cwd filter like claude: sessions record the working directory
    root = str(project_root)
    written = []
    for jsonl in sorted(base.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
        if len(written) >= limit:
            break
        if not jsonl.is_file():
            continue
        turns, files_touched, sid, cwd, last_ms = _read_codex_session(jsonl, root)
        user_turns = sum(1 for r, _ in turns if r == "user")
        if user_turns < min_turns or len(written) >= limit:
            continue
        # window filter on the newest event timestamp
        if last_ms and last_ms < since_ms:
            continue
        date = datetime.fromtimestamp(last_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d") if last_ms else "unknown"
        first_user = next((t[:80] for r, t in turns if r == "user"), sid)
        out_path = raw_dir / f"{date}-chat-{_slug(first_user)}.md"
        if out_path.exists():
            continue  # anti-loop
        md = [capture_frontmatter("chat-session", project, sid, "codex",
                                  created_iso=date, files_touched=sorted(set(files_touched))),
              f"# Chat session {sid} — {date}", "",
              "## Metadata",
              "- Harness: codex",
              f"- Session: {sid}",
              f"- Directory: {root}",
              f"- User turns: {user_turns}",
              f"- Project: {project}",
              "", "## Transcript", ""]
        for role, text in turns:
            label = "User" if role == "user" else ("Assistant" if role == "assistant" else "Tool")
            md.append(f"### {label}")
            md.append("")
            md.append(_md_escape(text))
            md.append("")
        if dry_run:
            print(f"  [DRY] {out_path.name}: {user_turns} user turns")
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("\n".join(md), encoding="utf-8")
            print(f"  captured {out_path.name} ({user_turns} user turns)")
        written.append(out_path)
    return written


def _read_codex_session(jsonl_path, project_root):
    """Parse one codex JSONL into (turns, files_touched, session_id, cwd, last_ms)."""
    import json as _json
    turns, files = [], []
    sid, cwd, last_ts = jsonl_path.stem, None, None
    tool_names = {}
    for line in jsonl_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = _json.loads(line)
        except Exception:
            continue  # malformed JSONL line — skip-tolerant (see :181)
        rec_type = rec.get("type")
        payload = rec.get("payload") or {}
        ptype = payload.get("type")
        ts = rec.get("timestamp")
        if isinstance(ts, str):
            try:
                from datetime import datetime as _dt
                last_ts = int(_dt.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000)
            except Exception:
                pass  # timestamp metadata only — session ordering degrades mildly
        if rec_type == "session_meta":
            sid = payload.get("id") or sid
            cwd = payload.get("cwd") or cwd
            continue
        if rec_type == "turn_context":
            cwd = payload.get("cwd") or cwd
            continue
        if ptype == "user_message":
            text = str(payload.get("message") or "").strip()
            if text:
                turns.append(("user", text))
        elif ptype == "agent_message":
            text = str(payload.get("message") or "").strip()
            if text:
                turns.append(("assistant", text))
        elif ptype in ("function_call", "custom_tool_call", "web_search_call"):
            name = str(payload.get("name") or ptype)
            cid = payload.get("call_id")
            tool_names[cid] = name
            # file paths for the thread index (read/edit/write families)
            import json as _j2
            args = payload.get("arguments")
            if isinstance(args, str):
                try:
                    args = _j2.loads(args)
                except Exception:
                    args = {}
            if isinstance(args, dict):
                for k in ("filePath", "file_path", "path"):
                    fp = str(args.get(k) or "").strip()
                    if fp and any(m in name.lower() for m in ("read", "edit", "write")):
                        files.append(fp)
                        break
        elif ptype in ("exec_command_end", "exec_command_output"):
            pass  # bash never parsed for files (#102 rule)
    return turns, files, sid, cwd, last_ts


def capture_gemini(project, project_root, raw_dir, since_ms, limit, min_turns, dry_run):
    """Capture Gemini CLI sessions from ~/.gemini/tmp/<hash>/chats/*.jsonl (#113).

    Schema (google-gemini/gemini-cli chatRecordingTypes.ts): one JSON object
    per FILE (ConversationRecord), not per line — sessions: sessionId,
    projectHash, startTime, lastUpdated, messages[] where each message has
    type (user | info | error | warning | gemini) and gemini messages carry
    toolCalls[{name, args}]. memoryScratchpad.touchedPaths is a bonus
    files_touched source.
    """
    base = Path.home() / ".gemini" / "tmp"
    if not base.is_dir():
        print("  gemini: no ~/.gemini/tmp — skipping", file=sys.stderr)
        return []
    root = str(project_root)
    written = []
    files = sorted(base.glob("*/chats/session-*.jsonl"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files:
        if len(written) >= limit:
            break
        try:
            record = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue  # unreadable session file — skip-tolerant (see :181)
        sid = str(record.get("sessionId") or path.stem)
        turns, files_touched = [], []
        for msg in record.get("messages") or []:
            mtype = msg.get("type")
            content = msg.get("displayContent") or msg.get("content")
            text = _part_text(content)
            if mtype == "user" and text.strip():
                turns.append(("user", text.strip()))
            elif mtype == "gemini" and text.strip():
                turns.append(("assistant", text.strip()))
            for tc in msg.get("toolCalls") or []:
                name = str(tc.get("name") or "")
                args = tc.get("args") or {}
                if isinstance(args, dict):
                    for k in ("filePath", "file_path", "path", "target_dir", "abs_path"):
                        fp = str(args.get(k) or "").strip()
                        if fp and any(m in name.lower() for m in ("read", "edit", "write", "replace")):
                            files_touched.append(fp)
            # memoryScratchpad.touchedPaths is a bonus files_touched signal
        files_touched += [str(p) for p in scratchpad_touched_paths(record)]
        user_turns = sum(1 for r, _ in turns if r == "user")
        if user_turns < min_turns or len(written) >= limit:
            continue
        start = str(record.get("startTime") or "")
        date = start[:10] if start else "unknown"
        first_user = next((t[:80] for r, t in turns if r == "user"), sid[:12])
        out_path = raw_dir / f"{date}-chat-{_slug(first_user)}.md"
        if out_path.exists():
            continue
        md = [capture_frontmatter("chat-session", project, sid, "gemini",
                                  created_iso=date, files_touched=sorted(set(files_touched))),
              f"# Chat session {sid[:16]} — {date}", "",
              "## Metadata",
              "- Harness: gemini",
              f"- Session: {sid}",
              f"- Project: {project}",
              "", "## Transcript", ""]
        for role, text in turns:
            label = "User" if role == "user" else "Assistant"
            md.append(f"### {label}")
            md.append("")
            md.append(_md_escape(text))
            md.append("")
        if dry_run:
            print(f"  [DRY] {out_path.name}: {user_turns} user turns")
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("\n".join(md), encoding="utf-8")
            print(f"  captured {out_path.name} ({user_turns} user turns)")
        written.append(out_path)
    return written


def scratchpad_touched_paths(record):
    """memoryScratchpad.touchedPaths — the session's own file footprint."""
    sp = record.get("memoryScratchpad") or {}
    return sp.get("touchedPaths") or []


def _part_text(content):
    """Flatten gemini's PartListUnion (str | {text} | [{text}, ...]) to text."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return str(content.get("text") or "")
    if isinstance(content, list):
        return "\n".join(_part_text(p) for p in content if isinstance(p, (str, dict)))
    return ""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Capture agent-harness chat sessions as raw evidence")
    parser.add_argument("project", help="Project slug")
    parser.add_argument("--since", default="90d", help="Window: 90d, 2w, 1y (default 90d — chat formats change fast; older sessions rarely match current reality)")
    parser.add_argument("--limit", type=int, default=20, help="Max sessions per harness")
    parser.add_argument("--min-turns", type=int, default=1, help="Skip sessions with fewer user turns")
    parser.add_argument("--harness", default="all", choices=["opencode", "claude", "codex", "gemini", "all"])
    parser.add_argument("--project-root", default=None, help="Project dir (default: resolved from fabric.yaml)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = get_config()
    project_root = Path(args.project_root) if args.project_root else resolve_repo_path(config, args.project)
    if not project_root or not project_root.exists():
        print(f"Unknown project {args.project!r} (no repos entry / dir)", file=sys.stderr)
        return 2
    _set_rel_root(project_root)
    raw_dir = CORPUS_ROOT / "evidence" / "raw" / args.project / "chats"
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
    if args.harness in ("codex", "all"):
        written += capture_codex(args.project, project_root, raw_dir, since_ms,
                                 args.limit, args.min_turns, args.dry_run)
    if args.harness in ("gemini", "all"):
        written += capture_gemini(args.project, project_root, raw_dir, since_ms,
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