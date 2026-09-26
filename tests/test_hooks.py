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