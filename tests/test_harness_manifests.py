"""Manifest-driven harness adapters (#65): user-declared harnesses via YAML.

Run: python3 -m pytest tests/test_harness_manifests.py -v
"""
import importlib.util
import shutil
import sys
from pathlib import Path
from unittest import mock

REPO = Path(__file__).parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


h = _load("harnesses", REPO / "scripts" / "harness" / "harnesses.py")


class TestManifestAdapters:
    def _manifest(self, tmp, key="myagent"):
        local = tmp / ".wiki-fabric" / "harnesses"
        local.mkdir(parents=True, exist_ok=True)
        (local / f"{key}.yaml").write_text(
            f"key: {key}\nname: My Agent\ninstructions: [\"AGENTS.md\"]\n"
            f"skills_dir: .{key}/skills\ndetect: [\".{key}\"]\n")

    def test_manifest_adapter_joins_all_specs(self, tmp_path):
        self._manifest(tmp_path)
        specs = h.all_specs(tmp_path)
        keys = {s["key"] for s in specs}
        assert "myagent" in keys
        assert "claude" in keys  # built-ins survive

    def test_builtin_wins_on_key_clash(self, tmp_path):
        # a manifest trying to shadow a governed adapter is ignored
        local = tmp_path / ".wiki-fabric" / "harnesses"
        local.mkdir(parents=True)
        (local / "claude.yaml").write_text(
            "key: claude\nname: Impostor\ninstructions: [\"x.md\"]\n")
        specs = h.all_specs(tmp_path)
        claude = next(s for s in specs if s["key"] == "claude")
        assert claude.get("name") == "Claude Code"

    def test_invalid_manifest_skipped(self, tmp_path):
        local = tmp_path / ".wiki-fabric" / "harnesses"
        local.mkdir(parents=True)
        (local / "bad.yaml").write_text("key: bad\n")  # no name, no surfaces
        specs = h.all_specs(tmp_path)
        assert "bad" not in {s["key"] for s in specs}

    def test_detect_installed_finds_manifest_harness(self, tmp_path):
        self._manifest(tmp_path)
        (tmp_path / ".myagent").mkdir()
        found = {s["key"] for s in h.detect_installed(tmp_path)}
        assert "myagent" in found
