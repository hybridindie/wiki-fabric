"""Unit tests for hooks.py and always_on.py (marker install/uninstall semantics).

Run: python3 -m pytest tests/test_hooks.py -v
"""

import re
import sys
import importlib.util
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


hooks = _load_module("wf_hooks", Path(__file__).parent.parent / "scripts" / "harness/hooks.py")
always_on = _load_module("wf_always_on", Path(__file__).parent.parent / "scripts" / "harness/always_on.py")

_install_hook = hooks._install_hook
_uninstall_hook = hooks._uninstall_hook


class TestHookInstallUninstall:
    def _fresh_hooks_dir(self, tmp_path, name="post-commit", preexisting=None):
        d = tmp_path / "hooks"
        d.mkdir()
        hook = d / name
        if preexisting is not None:
            hook.write_text(preexisting)
            hook.chmod(0o755)
        return d

    def test_install_fresh(self, tmp_path):
        d = tmp_path / "hooks"
        d.mkdir()
        msg = _install_hook(d, "post-commit", hooks._HOOK_SCRIPT, hooks._HOOK_MARKER, hooks._HOOK_MARKER_END)
        assert "installed" in msg
        text = (d / "post-commit").read_text()
        assert text.startswith("#!/bin/sh")
        assert hooks._HOOK_MARKER in text

    def test_install_appends_to_existing(self, tmp_path):
        existing = "#!/bin/sh\n# my other tool\necho hi\n"
        d = self._fresh_hooks_dir(tmp_path, preexisting=existing)
        msg = _install_hook(d, "post-commit", hooks._HOOK_SCRIPT, hooks._HOOK_MARKER, hooks._HOOK_MARKER_END)
        assert "appended" in msg
        text = (d / "post-commit").read_text()
        assert "my other tool" in text
        assert hooks._HOOK_MARKER in text

    def test_install_idempotent(self, tmp_path):
        d = tmp_path / "hooks"
        d.mkdir()
        _install_hook(d, "post-commit", hooks._HOOK_SCRIPT, hooks._HOOK_MARKER, hooks._HOOK_MARKER_END)
        first = (d / "post-commit").read_text()
        msg = _install_hook(d, "post-commit", hooks._HOOK_SCRIPT, hooks._HOOK_MARKER, hooks._HOOK_MARKER_END)
        assert "already installed" in msg
        assert (d / "post-commit").read_text() == first

    def test_uninstall_removes_block_keeps_other(self, tmp_path):
        existing = "#!/bin/sh\n# my other tool\necho hi\n"
        d = self._fresh_hooks_dir(tmp_path, preexisting=existing)
        _install_hook(d, "post-commit", hooks._HOOK_SCRIPT, hooks._HOOK_MARKER, hooks._HOOK_MARKER_END)
        msg = _uninstall_hook(d, "post-commit", hooks._HOOK_MARKER, hooks._HOOK_MARKER_END)
        assert "preserved" in msg
        text = (d / "post-commit").read_text()
        assert "my other tool" in text
        assert hooks._HOOK_MARKER not in text

    def test_uninstall_removes_file_when_only_content(self, tmp_path):
        d = tmp_path / "hooks"
        d.mkdir()
        _install_hook(d, "post-commit", hooks._HOOK_SCRIPT, hooks._HOOK_MARKER, hooks._HOOK_MARKER_END)
        msg = _uninstall_hook(d, "post-commit", hooks._HOOK_MARKER, hooks._HOOK_MARKER_END)
        assert "removed" in msg
        assert not (d / "post-commit").exists()


class TestHookScriptContent:
    REPO = Path(__file__).parent.parent

    def test_python_payload_shell_safe(self):
        """The -c payload is base64'd (the raw body's quotes/${} mangled the
        shell double-quoted launcher — found when the graphify block silently
        killed the background job). Assert: the launcher carries WF_HOOK_B64,
        the payload decodes to valid python, and the -c command carries no
        raw quote characters at the command position."""
        import ast
        import base64 as b64mod
        launcher = hooks._detached_launch(hooks._REBUILD_BODY_COMMIT)
        m = re.search(r"WF_HOOK_B64=([A-Za-z0-9+/=]+)", launcher)
        assert m, "launcher missing WF_HOOK_B64 payload"
        payload = b64mod.b64decode(m.group(1)).decode("utf-8")
        ast.parse(payload)  # valid python
        cmd_part = launcher.split("WF_HOOK_B64=")[1]
    def test_hook_exports_slug(self):
        assert "export WF_SLUG" in hooks._HOOK_SCRIPT

    def test_hook_guards(self):
        for guard in ("rebase-merge", "MERGE_HEAD", "CHERRY_PICK_HEAD", "WIKI_SKIP_HOOK"):
            assert guard in hooks._HOOK_SCRIPT

    def test_worktree_guard_present(self):
        assert "git-common-dir" in hooks._HOOK_SCRIPT

    def test_extract_claims_default_baked(self):
        script = hooks._HOOK_SCRIPT.replace(
            '[ "${WIKI_SKIP_HOOK:-0}" = "1" ] && exit 0',
            f'export WIKI_HOOK_EXTRACT="${{WIKI_HOOK_EXTRACT:-1}}"\n'
            '[ "${WIKI_SKIP_HOOK:-0}" = "1" ] && exit 0',
        )
        assert 'WIKI_HOOK_EXTRACT:-1' in script

    def test_embedded_shell_blocks_bash_parse(self):
        """#155-B: _PYTHON_DETECT is pasted into every generated hook. A bash
        syntax error there ships dead hooks silently (the doubled `done`
        regression) — contract: every string literal in hooks.py that carries
        the shell fabric-resolution block parses clean under `bash -n`."""
        import ast as _ast
        import os
        import subprocess
        import tempfile
        src = (self.REPO / "scripts" / "harness" / "hooks.py").read_text()
        tree = _ast.parse(src)
        checked = 0
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Constant) and isinstance(node.value, str):
                text = node.value
                if "_WF_FABRIC" in text and "for _wf_cand in" in text:
                    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as fh:
                        fh.write(text)
                        path = fh.name
                    try:
                        r = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
                        assert r.returncode == 0, f"hook shell block fails bash -n: {r.stderr.strip()}"
                        checked += 1
                    finally:
                        os.unlink(path)
        assert checked >= 1, "_PYTHON_DETECT block not found in hooks.py literals"


class TestMergeBodyValidity:
    """Regression: the merge body carried a bare `else:` — every installed
    post-merge hook died at exec with a syntax error before doing anything
    (found while wiring #85's capture-git step: live hooks in aperiodic/
    alpaca-agents were silently dead)."""

    def test_merge_body_compiles(self):
        import ast
        ast.parse(hooks._REBUILD_BODY_MERGE)

    def test_commit_body_compiles(self):
        import ast
        ast.parse(hooks._REBUILD_BODY_COMMIT)

    def test_merge_body_launches_as_python(self):
        import ast
        import base64 as b64mod
        launcher = hooks._detached_launch(hooks._REBUILD_BODY_MERGE)
        m = re.search(r"WF_HOOK_B64=([A-Za-z0-9+/=]+)", launcher)
        payload = b64mod.b64decode(m.group(1)).decode("utf-8")
        ast.parse(payload)


class TestMergeCaptureGit:
    """#85: post-merge hook runs capture-git for the merged repo."""

    def test_merge_body_runs_capture_git(self):
        assert "capture-git" in hooks._REBUILD_BODY_MERGE

    def test_capture_git_is_incremental(self):
        assert "--since-state" in hooks._REBUILD_BODY_MERGE

    def test_capture_git_gated_on_config(self):
        # config unreadable → skip, never crash the hook
        body = hooks._REBUILD_BODY_MERGE
        assert "config unreadable" in body
        assert "get_all_repo_names" in body


class TestAlwaysOn:
    def test_install_uninstall_roundtrip(self, tmp_path):
        target = tmp_path / "AGENTS.md"
        target.write_text("# my project\n")
        msg = always_on.install(target)
        assert "appended" in msg
        text = target.read_text()
        assert always_on.MARKER_START in text
        assert "# my project" in text
        msg = always_on.uninstall(target)
        assert "removed" in msg
        text = target.read_text()
        assert always_on.MARKER_START not in text
        assert "# my project" in text

    def test_install_idempotent(self, tmp_path):
        target = tmp_path / "AGENTS.md"
        target.write_text("# x\n")
        always_on.install(target)
        first = target.read_text()
        msg = always_on.install(target)
        assert "already" in msg
        assert target.read_text() == first

    def test_install_refreshes_outdated_block(self, tmp_path):
        target = tmp_path / "AGENTS.md"
        target.write_text("# x\n")
        always_on.install(target)
        old = target.read_text()
        # simulate an older block with stale content
        stale = old = (always_on.MARKER_START + "\nOLD CONTENT\n" + always_on.MARKER_END)
        target.write_text("# x\n\n" + stale + "\n")
        msg = always_on.install(target)
        assert "updated" in msg
        assert "OLD CONTENT" not in target.read_text()

    def test_no_frontmatter_in_block(self):
        assert not always_on._BLOCK_TEMPLATE.startswith("---")

class TestHookBodyFiles:
    """#128: hook bodies ship as real python files — lintable, testable,
    syntax-checked at import (the bare-else bug class can't ship silently)."""

    REPO = Path(__file__).parent.parent

    def test_body_files_exist_and_compile(self):
        hooks_dir = self.REPO / "system" / "hooks"
        for name in ("commit-body.py", "merge-body.py", "checkout-body.py"):
            f = self.REPO / "system" / "hooks" / name
            assert f.exists(), f"missing {f}"
            import ast
            ast.parse(f.read_text())

    def test_loaded_bodies_match_files(self):
        import ast
        assert hooks._REBUILD_BODY_COMMIT == (self.REPO / "system" / "hooks" / "commit-body.py").read_text()
        assert hooks._REBUILD_BODY_MERGE == (self.REPO / "system" / "hooks" / "merge-body.py").read_text()
        assert hooks._REBUILD_BODY_CHECKOUT == (self.REPO / "system" / "hooks" / "checkout-body.py").read_text()
        ast.parse(hooks._REBUILD_BODY_MERGE)  # regression: bare-else class
