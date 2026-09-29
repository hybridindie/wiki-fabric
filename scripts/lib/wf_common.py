#!/usr/bin/env python3
# wf_common.py — Shared helpers for wiki-fabric scripts.
#
# The graphify audit found parse_frontmatter duplicated in 8+ scripts, with
# subtle behavioral drift between copies (error text, fallback shapes). This
# module is the single home for the canonical versions. Each script stays
# independently runnable: it only depends on the standard library + PyYAML
# (optional, like the per-script copies were).
#
# Contract notes:
#   parse_frontmatter: returns (fm_dict, body). Missing block => ({}, text).
#   Malformed YAML    => ({}, body) — same tolerance the per-script copies had.
#   lint.py keeps its own 3-tuple variant (it needs the parse ERROR, not a
#   silent fallback) — that one is intentionally not folded in here.

import re
import subprocess
from pathlib import Path

try:
    import yaml
    _HAVE_YAML = True
except ImportError:
    _HAVE_YAML = False

_FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def parse_frontmatter(path):
    """Parse a markdown page with a `---` frontmatter block.

    Returns (fm_dict, body). No block => ({}, full text); broken YAML => ({}, body).
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    if _HAVE_YAML:
        try:
            return (yaml.safe_load(m.group(1)) or {}), m.group(2)
        except Exception:
            return {}, m.group(2)
    # PyYAML-less fallback: top-level key: value lines only
    fm = {}
    for line in m.group(1).splitlines():
        mm = re.match(r"([\w-]+):\s*(.*)$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2).strip().strip("'\"") or None
    return fm, m.group(2)


def slugify(text):
    """Lowercase kebab-case slug (shared by ingest/bootstrap/log-experience)."""
    return re.sub(r'[^a-z0-9]+', '-', (text or "").lower()).strip('-')


def norm(s):
    """Normalize free text for fuzzy matching (query/synthesize/eval)."""
    return re.sub(r'[^a-z0-9]+', ' ', (s or "").lower()).strip()


def sha256_file(path):
    """Hex sha256 of a file's bytes (ingest/capture/lint/okf_export)."""
    import hashlib
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


def today():
    """Local-date ISO string (frontmatter `created`/`updated`/`captured`)."""
    from datetime import date
    return date.today().isoformat()


def now_iso_utc():
    """ISO-8601 instant with explicit UTC offset (OKF §5)."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def github_repo_from_remote_url(url):
    """Derive 'owner/name' from a GitHub remote URL (git@ or https forms).

    None when the URL isn't GitHub. Shared by capture-git (repo gating)
    and sync (#100 PR push path). """
    if not url:
        return None
    url = str(url).strip()
    m = re.match(r"^git@github\.com:([^/]+/[^/]+?)(?:\.git)?$", url)
    if not m:
        m = re.match(r"^https://github\.com/([^/]+/[^/]+?)(?:\.git)?$", url)
    return m.group(1) if m else None


def github_repo_from_remote(repo_path, remote="origin", git_fn=None):
    """Derive 'owner/name' from a repo's git remote. None when the remote
    is missing or isn't GitHub — local-only repos keep working without gh.
    git_fn(path, *args) is injectable for tests; default shells out."""
    if git_fn is None:
        def git_fn(cwd, *args):
            try:
                out = subprocess.run(["git"] + list(args), cwd=str(cwd),
                                     capture_output=True, text=True, timeout=30)
                return out.stdout if out.returncode == 0 else None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return None
    url = git_fn(repo_path, "remote", "get-url", remote)
    return github_repo_from_remote_url(url)

def normalize_match(text, casefold=False):
    """Markdown-normalized comparison text for quote/locator matching.

    Canonical form: strips markdown artifacts (*, `, >), collapses whitespace.
    casefold=True adds lowercase (locator verification matches regardless of
    case; extraction repair preserves case distinctions)."""
    t = re.sub(r"[*`>]+", "", text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower() if casefold else t


def yaml_scalar(value):
    """Emit a YAML-safe inline double-quoted scalar for LLM-derived free text.

    Hand-escaping breaks on model artifacts (literal backslash-escaped quotes
    inside already-decoded JSON strings land as `\\"` and break the block
    mapping). Build the double-quoted form explicitly: backslash, double
    quote, and control chars are the only characters that need escaping in
    YAML double-quoted style; everything else passes through literally."""
    s = str(value or "")
    out = s.replace("\\", "\\\\").replace('"', '\\"')
    out = out.replace("\n", "\\n").replace("\r", "").replace("\t", "\\t")
    return f'"{out}"'


_STATEMENT_KEY_RE = re.compile(r"^statement:[ \t]*(.*)$", re.MULTILINE)
_FM_BLOCK_RE = re.compile(r"\A---\n(.*?)\n---", re.DOTALL)

# Corpus walk exclusions, one truth (#155-C: context/query/rebuild-index kept
# private copies that drifted — query's omitted .venv/venv/node_modules).
# SKIPPED are machine-irrelevant or human-facing layers; SKIP_FILES are
# top-level markers. Callers layer extra filtering (traces, fixtures, ignores).
SKIP_PARTS = {".git", ".obsidian", ".opencode", "__pycache__", ".venv", "venv",
              "node_modules", "templates", "schemas", "evaluations", "raw",
              "traces", "system", "tests", "examples", "wiki", "syntheses",
              "scripts"}
SKIP_FILES = {"index.md", "log.md", "catalog.json", "README.md",
              "CONTRIBUTING.md", "AGENTS.md"}


def corpus_walk(root):
    """Deterministic corpus walk yielding (path, rel parts, rel posix) for
    catalogable corpus pages. Shared by context / query / rebuild-index."""
    root = Path(root)
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        parts = rel.parts
        if any(x in SKIP_PARTS for x in parts):
            continue
        if rel.name in SKIP_FILES or rel.name.endswith("README.md"):
            continue
        if "traces" in parts:  # evidence/traces: run artifacts, not pages
            continue
        yield p, parts, rel

def claim_statement(text_or_path):
    """The claim's statement, parsed from `statement:` frontmatter — the one
    parser for all consumers (#154: 12 drifted regex copies, two incompatible
    variants).

    Tolerant of every shipped shape:
      - double/single-quoted inline:  statement: "..."
      - bare inline:                  statement: Alpaca Agents is ...
      - block scalars:                statement: | / > (literal/folded)
    Returns the statement unwrapped and right-trimmed; "" when absent. A
    block scalar is read to the end of its indentation block; quoted/inline
    forms end at the line. Accepts raw page text or a Path."""
    from pathlib import Path as _Path
    if isinstance(text_or_path, _Path) or hasattr(text_or_path, "read_text"):
        try:
            text = _Path(text_or_path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
    else:
        text = text_or_path or ""
    # only the frontmatter block counts — a body line `statement: ...` is prose
    mb = _FM_BLOCK_RE.match(text)
    if not mb:
        return ""
    scope = mb.group(1)
    m = _STATEMENT_KEY_RE.search(scope)
    if not m:
        return ""
    rest = m.group(1).strip()
    if rest in ("|", "|-", "|+", ">", ">-", ">+"):
        # block scalar: the lines after the key line, up to the block's end
        # (deeper-indent run inside the frontmatter scope)
        after_key = scope[m.end():]
        lines = after_key.splitlines()
        block, indent = [], None
        for line in lines:
            if not line.strip():
                block.append("")
                continue
            cur = len(line) - len(line.lstrip())
            if indent is None:
                indent = cur
            if cur < indent:
                break
            block.append(line[indent:])
        return "\n".join(block).strip("\n") if rest.startswith("|") else \
            re.sub(r"\s+", " ", " ".join(b.strip() for b in block)).strip()
    if len(rest) >= 2 and rest[0] == rest[-1] and rest[0] in ('"', "'"):
        rest = rest[1:-1]
    return rest.rstrip()


def git_sh(*args, cwd=None, timeout=120):
    """Run a git command; return stdout or None on failure."""
    import subprocess
    try:
        out = subprocess.run(
            ["git"] + [str(a) for a in args],
            cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=timeout,
        )
        return out.stdout if out.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def dump_frontmatter(fm):
    """Serialize a frontmatter dict — ONE dump convention (#154: promote/
    okf_export/repos-migrate each re-implemented it with different options;
    only okf_export set width, so long scalars wrapped differently for the
    same page). Keys preserved in insertion order, unicode kept, no line
    wrapping (width=10**6), block style off."""
    import yaml
    return yaml.dump(fm, sort_keys=False, allow_unicode=True, width=10**6)


def write_frontmatter(path, fm, body):
    """Write a markdown page: `---` + frontmatter + `---` + body (#154 — the
    one frontmatter writer; promote.py owned the only named one and okf_export/
    repos-migrate/configure dumped inline with drifted options)."""
    path = Path(path)
    path.write_text(f"---\n{dump_frontmatter(fm)}---\n{body}", encoding="utf-8")
