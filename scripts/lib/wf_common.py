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