#!/usr/bin/env python3
# hooks.py — install/uninstall/status wiki-fabric git hooks
#
# Modeled on graphify's hooks.py (marker-based append, detached launch,
# rebase/merge guards, worktree skip) but wired to wiki-fabric's pipeline:
#
#   post-commit   → wf capture <slug> (sha256 drift) → wf ingest --changed <slug> (LLM claims)
#   post-checkout → branch switch detected → refresh hint (never auto-ingests)
#
# Enhancements over graphify's hooks where they fit wiki-fabric:
#   - Drift-gated: capture exits 2 only when files are NEW/CHANGED; ingest is
#     skipped entirely when there is no drift (no wasted LLM calls).
#   - Self-skip: commits that only touch fabric content dirs (evidence/,
#     registry/, patterns/...) do not re-trigger capture — no rebuild loop.
#   - Content-only commits (docs) trigger capture; code-only commits skip it
#     unless the repo declares source globs that match code (globs win).
#   - Detached launch so git commit returns instantly; output to a log file.
#   - WIKI_SKIP_HOOK=1 opt-out (same as GRAPHIFY_SKIP_HOOK).

import os
import re
import subprocess
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
from pathlib import Path

_HOOK_MARKER = "# wiki-fabric-hook-start"
HOOK_VERSION = 2  # bump when hook script bodies change; wf hook status reports drift
_HOOK_MARKER_END = "# wiki-fabric-hook-end"
_CHECKOUT_MARKER = "# wf-checkout-hook-start"
# HOOK_VERSION is stamped inside the marker line: "# wiki-fabric-hook-start v<N>"
_CHECKOUT_MARKER_END = "# wf-checkout-hook-end"

# Directories whose changes should never re-trigger capture (they ARE the fabric output).
# Shell ERE, anchored per path segment prefix.
_FABRIC_OUTPUT_DIRS = (
    "evidence/|registry/|patterns/|anti-patterns/|skills/|concepts/|projects/|"
    "global/|domains/|syntheses/|graphify-out/|\\.wiki-fabric/"
)

_PYTHON_DETECT = """\
# Resolve the fabric root + venv python at hook time (not install time):
# the fabric can be re-installed or updated after the hook is installed.
_WF_FABRIC=""
for _wf_cand in "${WIKI_FABRIC_DIR:-}" "${XDG_DATA_HOME:-$HOME/.local/share}/wiki-fabric" "$HOME/Development/wiki-fabric" "$HOME/wiki-fabric" "$(dirname "$(pwd)")/wiki-fabric"; do
    [ -n "$_wf_cand" ] || continue
    [ -d "$_wf_cand/scripts" ] || continue
    _WF_FABRIC="$_wf_cand"
    break
done
if [ -z "$_WF_FABRIC" ]; then
    echo "[wf hook] fabric not found (set WIKI_FABRIC_DIR)" >&2
    exit 0
fi
if [ -x "$_WF_FABRIC/.venv/bin/python" ]; then
    WF_PYTHON="$_WF_FABRIC/.venv/bin/python"
else
    WF_PYTHON="$(command -v python3 || command -v python)"
fi
"""


# post-commit body: capture (drift-gated) → ingest changed (LLM optional).
# Runs detached so git commit returns immediately.
# All subprocess calls use argument lists (no shell), so slug / fabric can
# never inject shell metacharacters.
_REBUILD_BODY_COMMIT = """\
import os, subprocess, sys
from pathlib import Path

fabric = Path(os.environ['WF_FABRIC'])
slug = os.environ['WF_SLUG']
py = sys.executable

# 1. Capture (sha256 drift vs recorded sources; exit 2 == drift)
r = subprocess.run([py, str(fabric / 'scripts/cmd/capture.py'), slug,
                    '--project-root', os.getcwd(), '--quiet'],
                   capture_output=True).returncode
if r not in (0, 2):
    print(f'[wf hook] capture failed (exit {r}) — run: wf capture {slug}', flush=True)
    sys.exit(1)
if r == 0:
    print('[wf hook] no doc drift — capture skipped', flush=True)
    # doc capture skipped, but CODE changes still drive the graphify cycle
    # (fall through to steps 3-4 rather than exiting)
else:

if r == 2:
    # 2. Ingest drift. LLM only when --extract-claims was enabled at install
    #    time (WIKI_HOOK_EXTRACT=1); otherwise sources are recorded without
    #    claims and the agent ingests interactively on next session.
    ingest_args = [py, str(fabric / 'scripts/cmd/ingest.py'), '--changed', slug]
    if os.environ.get('WIKI_HOOK_EXTRACT', '').lower() in ('1', 'true', 'yes'):
        ingest_args.append('--extract-claims')
    print('[wf hook] captured drift — ingesting...', flush=True)
    subprocess.run(ingest_args)

# 3. After intake, persist the pending-HITL manifest (promotion dossiers,
#    domain proposals, stale claims) so ANY AI harness can surface pending
#    decisions at session start by reading registry/pending-gate.md.
subprocess.run([py, str(fabric / 'scripts/cmd/gate.py'), '--quiet', '--write-manifest'])

# 4. Graphify cycle — ONLY when code files changed and the integration is
#    enabled. The graph is committed with the corpus (global/graphs/), so
#    staleness detection and code navigation stay fresh on every code commit.
CODE_CHANGED = subprocess.run(
    ['git', '-C', str(os.getcwd()), 'diff', '--name-only', 'HEAD~1', 'HEAD'],
    capture_output=True, text=True).stdout
code_files = [f for f in CODE_CHANGED.splitlines()
              if f.endswith(('.py', '.js', '.ts', '.gd', '.go', '.rs', '.java'))]
bridge = fabric / 'scripts/harness/graphify-bridge.py'
if not bridge.exists() or not code_files:
    sys.exit(0)
# integration check lives in the bridge itself (gated, prints reason)
r = subprocess.run([py, str(bridge), '--update', '--repo', slug],
                   capture_output=True, text=True, timeout=300)
if r.returncode != 0 or 'not enabled' in r.stdout:
    print(f'[wf hook] graphify skipped (rc={r.returncode}) '
          f'{(r.stderr or r.stdout)[-200:]}', flush=True)
    sys.exit(0)  # graphify off — quiet, by design
print('[wf hook] graphify update ok — importing/enriching...', flush=True)
for step in ('--import', '--enrich', '--diff'):
    r = subprocess.run([py, str(bridge), step, '--repo', slug],
                       capture_output=True, text=True, timeout=300)
    if r.stdout.strip():
        print('[wf hook] ' + r.stdout.strip().splitlines()[-1][:120], flush=True)
"""


_REBUILD_BODY_MERGE = """\
import os, subprocess, sys
from pathlib import Path

fabric = Path(os.environ['WF_FABRIC'])
slug = os.environ['WF_SLUG']
py = sys.executable

r = subprocess.run([py, str(fabric / 'scripts/cmd/capture.py'), slug,
                    '--project-root', os.getcwd(), '--quiet'],
                   capture_output=True).returncode
if r not in (0, 2):
    print(f'[wf hook] capture failed (exit {r}) — run: wf capture {slug}', flush=True)
    sys.exit(1)
if r == 0:
    print('[wf hook] no doc drift — capture skipped', flush=True)
    # doc capture skipped, but CODE changes still drive the graphify cycle
    # (fall through to steps 3-4 rather than exiting)
else:

ingest_args = [py, str(fabric / 'scripts/cmd/ingest.py'), '--changed', slug]
if os.environ.get('WIKI_HOOK_EXTRACT', '').lower() in ('1', 'true', 'yes'):
    ingest_args.append('--extract-claims')
print('[wf hook] captured drift — ingesting...', flush=True)
subprocess.run(ingest_args)

# Surface pending HITL decisions (promotion/domain proposals, stale claims)
# after a merge too — merge is a common moment for new upstream evidence.
subprocess.run([py, str(fabric / 'scripts/cmd/gate.py'), '--quiet', '--write-manifest'])
"""


_REBUILD_BODY_CHECKOUT = """\
import os, sys
print("[wf hook] branch switched — upstream docs may differ from captured raw.", flush=True)
print("[wf hook] refresh hint: wf capture <slug> && wf ingest --changed <slug>", flush=True)
"""


_LAUNCHER_TEMPLATE = """\
import os, subprocess, sys
_src = '''
__REBUILD_BODY__
'''
_log = os.environ.get('WIKI_HOOK_LOG') or os.path.join(os.path.expanduser('~'), '.cache', 'wiki-fabric-hook.log')
try:
    os.makedirs(os.path.dirname(_log), exist_ok=True)
    _out = open(_log, 'a', buffering=1, encoding='utf-8', errors='replace')
except OSError:
    _out = subprocess.DEVNULL
_kw = dict(stdout=_out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=os.getcwd(), close_fds=True)
_cmd = [sys.executable, '-c', _src]
if os.name == 'nt':
    _flags = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    try:
        subprocess.Popen(_cmd, creationflags=_flags | 0x01000000, **_kw)
    except OSError:
        subprocess.Popen(_cmd, creationflags=_flags, **_kw)
else:
    subprocess.Popen(_cmd, start_new_session=True, **_kw)
"""


def _detached_launch(rebuild_body: str) -> str:
    import base64
    launcher = _LAUNCHER_TEMPLATE.replace("__REBUILD_BODY__", rebuild_body)
    # base64 the whole -c payload: the body contains single quotes, ${...}
    # and nested quotes that a shell double-quoted -c string mangles (found
    # when the graphify block's quoting silently truncated the launcher —
    # the background job died with a syntax error before its first log line)
    b64 = base64.b64encode(launcher.encode("utf-8")).decode("ascii")
    return f"WF_HOOK_B64={b64} '$WF_PYTHON' -c \"import base64,os;exec(base64.b64decode(os.environ['WF_HOOK_B64']).decode())\"\n"


_WORKTREE_GUARD = """\
_WF_GITDIR=$(cd "$(git rev-parse --git-dir 2>/dev/null)" 2>/dev/null && pwd)
_WF_COMMONDIR=$(cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd)
if [ -n "$_WF_COMMONDIR" ] && [ "$_WF_GITDIR" != "$_WF_COMMONDIR" ]; then
    exit 0
fi
"""


_MERGE_MARKER = "# wf-merge-hook-start"
_MERGE_MARKER_END = "# wf-merge-hook-end"

_MERGE_SCRIPT = """\
# wf-merge-hook-start
# Fast-forward pulls integrate several commits at once; diff the whole range.
# Installed by: wf hook install
(
[ "${WIKI_SKIP_HOOK:-0}" = "1" ] && exit 0
GIT_DIR=${GIT_DIR:-$(git rev-parse --git-dir 2>/dev/null)}
[ -f "$GIT_DIR/MERGE_HEAD" ] && exit 0

""" + _WORKTREE_GUARD + """
if git rev-parse --verify --quiet ORIG_HEAD >/dev/null; then
    CHANGED=$(git diff --name-only ORIG_HEAD HEAD 2>/dev/null || true)
else
    CHANGED=$(git diff-tree --root --no-commit-id --name-only -r HEAD 2>/dev/null || true)
fi
[ -z "$CHANGED" ] && exit 0

_NON_FABRIC=$(printf '%s\n' "$CHANGED" | grep -Ev '^(evidence/|registry/|patterns/|anti-patterns/|skills/|concepts/|projects/|global/|domains/|syntheses/|graphify-out/)' || true)
[ -z "$_NON_FABRIC" ] && exit 0

_DOCS=$(printf '%s\n' "$_NON_FABRIC" | grep -E '\\.(md|markdown)$' || true)
[ -z "$_DOCS" ] && exit 0

""" + _PYTHON_DETECT + """
WF_SLUG=$(basename "$(pwd)")
export WF_SLUG

_WF_LOG="${HOME}/.cache/wiki-fabric-hook.log"
mkdir -p "$(dirname "$_WF_LOG")"
export WIKI_HOOK_LOG="$_WF_LOG"
export WF_FABRIC="$_WF_FABRIC"
echo "[wf hook] merged upstream docs — launching background capture (log: $_WF_LOG)"
""" + _detached_launch(_REBUILD_BODY_MERGE) + """)
# wf-merge-hook-end
"""


_HOOK_SCRIPT = """\
# wiki-fabric-hook-start
# Auto-captures upstream doc drift after each commit and ingests changed raw
# files (LLM claims only when WIKI_HOOK_EXTRACT=1 was set at install).
# Installed by: wf hook install
(

# Skip during rebase/merge/cherry-pick
GIT_DIR=${GIT_DIR:-$(git rev-parse --git-dir 2>/dev/null)}
[ -d "$GIT_DIR/rebase-merge" ] && exit 0
[ -d "$GIT_DIR/rebase-apply" ] && exit 0
[ -f "$GIT_DIR/MERGE_HEAD" ] && exit 0
[ -f "$GIT_DIR/CHERRY_PICK_HEAD" ] && exit 0

[ "${WIKI_SKIP_HOOK:-0}" = "1" ] && exit 0

""" + _WORKTREE_GUARD + """
CHANGED=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || git diff --name-only HEAD 2>/dev/null)
[ -z "$CHANGED" ] && exit 0

# Skip when only fabric-owned paths changed (prevents ingest/capture loop)
_NON_FABRIC=$(printf '%s\\n' "$CHANGED" | grep -Ev '^(""" + _FABRIC_OUTPUT_DIRS + """)' || true)
[ -z "$_NON_FABRIC" ] && exit 0

# Only doc-bearing files trigger capture (capture globs are md-centric)
_DOCS=$(printf '%s\\n' "$_NON_FABRIC" | grep -E '\\.(md|markdown)$|^AGENTS\\.md$|^README\\.md$|^CONTRIBUTING\\.md$' || true)
[ -z "$_DOCS" ] && exit 0

""" + _PYTHON_DETECT + """
# Project slug = directory name of this repo (matches bootstrap slugify for
# simple names; a slug mismatch is harmless — capture reports it in the log)
WF_SLUG=$(basename "$(pwd)")
export WF_SLUG
export WF_FABRIC="$_WF_FABRIC"

_WF_LOG="${HOME}/.cache/wiki-fabric-hook.log"
mkdir -p "$(dirname "$_WF_LOG")"
export WIKI_HOOK_LOG="$_WF_LOG"
echo "[wf hook] doc drift committed — launching background capture+ingest (log: $_WF_LOG)"
""" + _detached_launch(_REBUILD_BODY_COMMIT) + """)
# wiki-fabric-hook-end
"""


_CHECKOUT_SCRIPT = """\
# wf-checkout-hook-start
# Branch-switch refresh hint for wiki-fabric captures.
# Installed by: wf hook install
(
[ "${WIKI_SKIP_HOOK:-0}" = "1" ] && exit 0
PREV_HEAD=$1
NEW_HEAD=$2
BRANCH_SWITCH=$3
[ "$BRANCH_SWITCH" != "1" ] && exit 0
[ "$PREV_HEAD" = "$NEW_HEAD" ] && exit 0
[ ! -f ".wiki-overlay.md" ] && exit 0
""" + _PYTHON_DETECT + """
echo "[wf hook] branch switched — run 'wf capture $(basename "$(pwd)")' if upstream docs changed"
)
# wf-checkout-hook-end
"""


def _git_root(path: Path):
    """Nearest .git dir, or None."""
    current = path.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def _hooks_dir(root: Path) -> Path:
    # core.hooksPath wins: git EXECUTES hooks from there, so installing to
    # .git/hooks while core.hooksPath is set silently no-ops (found when the
    # wiki-fabric repo set core.hooksPath=scripts/hooks for its own dev hooks
    # and wf hook install landed in .git/hooks — never fired).
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "config", "--get", "core.hooksPath"],
            capture_output=True, text=True,
        )
        if res.returncode == 0 and res.stdout.strip():
            raw = res.stdout.strip()
            if "\n" not in raw and "\x00" not in raw and "\\" not in raw:
                hp = Path(raw)
                d = (hp if hp.is_absolute() else (root / hp)).resolve()
                d.mkdir(parents=True, exist_ok=True)
                return d
    except (OSError, FileNotFoundError):
        pass
    try:
        res = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--git-path", "hooks"],
            capture_output=True, text=True,
        )
        if res.returncode == 0 and res.stdout.strip():
            raw = res.stdout.strip()
            if "\n" not in raw and "\x00" not in raw and "\\" not in raw:
                d = (root / raw).resolve()
                d.mkdir(parents=True, exist_ok=True)
                return d
    except (OSError, FileNotFoundError):
        pass
    d = root / ".git" / "hooks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _user_hooks_dir(hooks_dir: Path) -> Path:
    # Husky 9: core.hooksPath -> .husky/_ (wrappers); user hooks in .husky/
    if hooks_dir.name == "_":
        return hooks_dir.parent
    return hooks_dir


def _stamp(marker: str, version: int) -> str:
    """Marker line with version stamp for drift detection."""
    return f"{marker} v{version}"


def _installed_version(content: str, marker: str) -> int:
    """Parse the v<N> stamp from an installed block; 1 = unstamped (legacy)."""
    for line in content.splitlines():
        if marker in line:
            m = re.search(r"v(\d+)", line)
            return int(m.group(1)) if m else 1
    return 0


def _install_hook(hooks_dir: Path, name: str, script: str, marker: str, marker_end: str, version: int = 1) -> str:
    hook_path = hooks_dir / name
    script = script.replace(marker, _stamp(marker, version), 1)
    if hook_path.exists():
        content = hook_path.read_text(encoding="utf-8")
        if marker in content:
            if marker_end in content:
                start = content.find(marker)
                end = content.find(marker_end) + len(marker_end)
                new_content = content[:start] + script.rstrip() + content[end:]
                if new_content == content:
                    return f"already installed at {hook_path}"
                hook_path.write_text(new_content, encoding="utf-8", newline="\n")
                return f"updated existing {name} hook at {hook_path}"
            return f"already installed at {hook_path}"
        hook_path.write_text(content.rstrip() + "\n\n" + script, encoding="utf-8", newline="\n")
        return f"appended to existing {name} hook at {hook_path}"
    hook_path.write_text("#!/bin/sh\n" + script, encoding="utf-8", newline="\n")
    hook_path.chmod(0o755)
    return f"installed at {hook_path}"


def _uninstall_hook(hooks_dir: Path, name: str, marker: str, marker_end: str) -> str:
    hook_path = hooks_dir / name
    if not hook_path.exists():
        return f"no {name} hook found — nothing to remove."
    content = hook_path.read_text(encoding="utf-8")
    if marker not in content:
        return f"wiki-fabric hook not found in {name} — nothing to remove."
    new_content = re.sub(
        rf"{re.escape(marker)}.*?{re.escape(marker_end)}\n?",
        "", content, flags=re.DOTALL,
    ).strip()
    if not new_content or new_content in ("#!/bin/bash", "#!/bin/sh"):
        hook_path.unlink()
        return f"removed {name} hook at {hook_path}"
    hook_path.write_text(new_content + "\n", encoding="utf-8", newline="\n")
    return f"wiki-fabric removed from {name} at {hook_path} (other hook content preserved)"


def _find_fabric_dir():
    candidates = [
        os.environ.get("WIKI_FABRIC_DIR", ""),
        str(Path.home() / "Development" / "wiki-fabric"),
        str(Path.home() / "wiki-fabric"),
    ]
    for c in candidates:
        if c and (Path(c) / "scripts").is_dir():
            return Path(c)
    return None


def install(extract_claims: bool = False) -> str:
    root = _git_root(Path("."))
    if root is None:
        raise RuntimeError(f"No git repository found at or above {Path('.').resolve()}")

    fabric = _find_fabric_dir()
    if fabric is None:
        raise RuntimeError("wiki-fabric not found (set WIKI_FABRIC_DIR or install at ~/Development/wiki-fabric)")

    hooks_dir = _user_hooks_dir(_hooks_dir(root))
    body = _REBUILD_BODY_COMMIT.replace("__FABRIC__", str(fabric))
    hook = _HOOK_SCRIPT
    # Embed extract-claims preference as an env default baked into the hook
    extract_default = "1" if extract_claims else "0"
    hook = hook.replace(
        '[ "${WIKI_SKIP_HOOK:-0}" = "1" ] && exit 0',
        f'export WIKI_HOOK_EXTRACT="${{WIKI_HOOK_EXTRACT:-{extract_default}}}"\n'
        '[ "${WIKI_SKIP_HOOK:-0}" = "1" ] && exit 0',
    )
    checkout = _CHECKOUT_SCRIPT

    commit_msg = _install_hook(hooks_dir, "post-commit", hook, _HOOK_MARKER, _HOOK_MARKER_END, version=HOOK_VERSION)
    checkout_msg = _install_hook(hooks_dir, "post-checkout", checkout, _CHECKOUT_MARKER, _CHECKOUT_MARKER_END, version=HOOK_VERSION)
    merge_msg = _install_hook(hooks_dir, "post-merge", _MERGE_SCRIPT, _MERGE_MARKER, _MERGE_MARKER_END, version=HOOK_VERSION)

    slug = root.name
    return (
        f"post-commit: {commit_msg}\n"
        f"post-checkout: {checkout_msg}\n"
        f"post-merge: {merge_msg}\n"
        f"project slug: {slug}\n"
        f"fabric: {fabric}\n"
        f"llm claims on drift: {'yes' if extract_claims else 'no (set WIKI_HOOK_EXTRACT=1 or reinstall with --extract-claims)'}\n"
        f"log: ~/.cache/wiki-fabric-hook.log\n"
        f"opt-out per command: WIKI_SKIP_HOOK=1 git commit ..."
    )


def uninstall() -> str:
    root = _git_root(Path("."))
    if root is None:
        raise RuntimeError(f"No git repository found at or above {Path('.').resolve()}")
    hooks_dir = _user_hooks_dir(_hooks_dir(root))
    commit_msg = _uninstall_hook(hooks_dir, "post-commit", _HOOK_MARKER, _HOOK_MARKER_END)
    checkout_msg = _uninstall_hook(hooks_dir, "post-checkout", _CHECKOUT_MARKER, _CHECKOUT_MARKER_END)
    merge_msg = _uninstall_hook(hooks_dir, "post-merge", _MERGE_MARKER, _MERGE_MARKER_END)
    return f"post-commit: {commit_msg}\npost-checkout: {checkout_msg}\npost-merge: {merge_msg}"


def status() -> str:
    root = _git_root(Path("."))
    if root is None:
        return "Not in a git repository."

    def _check(name: str, marker: str, marker_end: str = None) -> str:
        p = _user_hooks_dir(_hooks_dir(root)) / name
        if not p.exists():
            return "not installed"
        text = p.read_text(encoding="utf-8")
        if marker not in text:
            return "not installed (hook exists but wiki-fabric not found)"
        ver = _installed_version(text, marker)
        if ver < HOOK_VERSION:
            return f"installed (outdated v{ver} < v{HOOK_VERSION} — run: wf hook install)"
        return "installed"

    commit = _check("post-commit", _HOOK_MARKER, _HOOK_MARKER_END)
    checkout = _check("post-checkout", _CHECKOUT_MARKER, _CHECKOUT_MARKER_END)
    merge = _check("post-merge", _MERGE_MARKER, _MERGE_MARKER_END)
    fabric = _find_fabric_dir()
    overlay = "yes" if (root / ".wiki-overlay.md").exists() else "no (run: wf bootstrap here)"
    extract = os.environ.get("WIKI_HOOK_EXTRACT", "")
    return (
        f"repo: {root}\n"
        f"overlay: {overlay}\n"
        f"post-commit: {commit}\n"
        f"post-checkout: {checkout}\n"
        f"post-merge: {merge}\n"
        f"fabric: {fabric or 'not found'}\n"
        f"WIKI_HOOK_EXTRACT: {extract or '(unset)'}"
    )


def reinstall(repos_from_config: bool = False) -> str:
    """Reinstall outdated hook blocks in connected repos (wf update calls this)."""
    import subprocess as _sp
    from fabric_config import get_config, resolve_repo_path, get_all_repo_names
    results = []
    targets = []
    if repos_from_config:
        cfg = get_config()
        for name in get_all_repo_names(cfg):
            rp = resolve_repo_path(cfg, name)
            if rp and (rp / ".git").exists() and (rp / ".wiki-overlay.md").exists():
                targets.append(rp)
    for t in targets:
        os.chdir(t)
        try:
            msg = install(extract_claims=os.environ.get("WIKI_HOOK_EXTRACT", "").lower() in ("1", "true", "yes"))
            results.append(f"{t.name}: {msg.splitlines()[0]}")
        except RuntimeError as e:
            results.append(f"{t.name}: skipped ({e})")
    return "\n".join(results) if results else "no connected repos to refresh"


def _sys_exec():
    return sys.executable


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="wiki-fabric git hooks")
    parser.add_argument("cmd", choices=["install", "uninstall", "status", "reinstall"])
    parser.add_argument("--extract-claims", action="store_true",
                        help="post-commit hook also runs LLM claim extraction on drift")
    parser.add_argument("--repos-from-config", action="store_true",
                        help="reinstall hooks in all repos registered in fabric.yaml")
    args = parser.parse_args()
    if args.cmd == "install":
        print(install(extract_claims=args.extract_claims))
    elif args.cmd == "uninstall":
        print(uninstall())
    elif args.cmd == "reinstall":
        print(reinstall(repos_from_config=args.repos_from_config))
    else:
        print(status())# graphify hook probe 1790382013
# hook cycle probe 1790382458
# graphify cycle probe 3 1790382537
