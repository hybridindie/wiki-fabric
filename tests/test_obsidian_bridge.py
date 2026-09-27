"""Unit tests for the obsidian two-way vault bridge (#112).

Run: python3 -m pytest tests/test_obsidian_bridge.py -v
"""

import json
import sys
import importlib.util
from pathlib import Path
from unittest import mock

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ob = _load("obsidian_bridge", _SCRIPTS / "lib/obsidian_bridge.py")


class _Fabric:
    """A temp fabric with a vault + wiki."""

    def __init__(self, tmp):
        self.root = tmp / "fabric"
        self.vault = tmp / "vault"
        (self.root / "registry").mkdir(parents=True)
        (self.root / "evidence").mkdir(parents=True)
        self.wiki = self.vault / "wiki"
        self.wiki.mkdir(parents=True)
        ob = self.root / "evidence" / "raw"  # harvest output root


def _patch_paths(br, root):
    return (
        mock.patch.object(br, "CORPUS_ROOT", root),
        mock.patch.object(br, "MANIFEST_PATH", root / "registry" / "wiki-export-manifest.json"),
        mock.patch.object(br_module(), "get_vault_path", lambda: root / "vault"),
    )


class TestManifest:
    def test_first_run_baselines_without_harvest(self, tmp_path):
        root = tmp_path / "fabric"
        root.mkdir()
        (root / "evidence" / "raw").mkdir(parents=True)
        (root / "vault" / "wiki").mkdir(parents=True)
        (root / "vault" / "wiki" / "a.md").write_text("content a\n")
        with mock.patch.object(br_module(), "MANIFEST_PATH", root / "registry" / "wiki-export-manifest.json"), \
                mock.patch.object(br_module(), "CORPUS_ROOT", root), \
                mock.patch("fabric_config.get_vault_path", lambda: root / "vault"):
            br = br_module()
            r = br.harvest_before_export()
        assert r["harvested"] == 0
        assert r["reason"] == "baseline established"
        m = json.loads((root / "registry" / "wiki-export-manifest.json").read_text())
        assert m["files"]["a.md"]

    def test_human_edit_is_harvested(self, tmp_path):
        root = tmp_path / "fabric"
        (root / "registry").mkdir(parents=True)
        (root / "evidence" / "raw").mkdir(parents=True)
        wiki = root / "vault" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "a.md").write_text("content a\n")
        with mock.patch.object(br_module(), "MANIFEST_PATH", root / "registry" / "wiki-export-manifest.json"), \
                mock.patch.object(br_module(), "CORPUS_ROOT", root), \
                mock.patch("fabric_config.get_vault_path", lambda: root / "vault"):
            br = br_module()
            br.harvest_before_export()
            # human edit AFTER export
            (wiki / "a.md").write_text("content a\n\nhuman edit\n")
            r = br.harvest_before_export()
        assert r["harvested"] == 1
        harvested = r["harvested_paths"]
        assert harvested == ["a.md"]
        # the edit landed in evidence
        raw = root / "evidence" / "raw" / "vault" / "obsidian"
        files = list(raw.glob("*-a.md"))
        assert len(files) == 1
        assert "human edit" in files[0].read_text()

    def test_no_false_positive_on_unchanged(self, tmp_path):
        root = tmp_path / "fabric"
        (root / "registry").mkdir(parents=True)
        (root / "evidence" / "raw").mkdir(parents=True)
        wiki = root / "vault" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "a.md").write_text("content a\n")
        with mock.patch.object(br_module(), "MANIFEST_PATH", root / "registry" / "wiki-export-manifest.json"), \
                mock.patch.object(br_module(), "CORPUS_ROOT", root), \
                mock.patch("fabric_config.get_vault_path", lambda: root / "vault"):
            br = br_module()
            br.harvest_before_export()
            r = br.harvest_before_export()
        assert r["harvested"] == 0

    def test_second_harvest_dedupes(self, tmp_path):
        root = tmp_path / "fabric"
        (root / "registry").mkdir(parents=True)
        (root / "evidence" / "raw").mkdir(parents=True)
        wiki = root / "vault" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "a.md").write_text("v1\n")
        with mock.patch.object(br_module(), "MANIFEST_PATH", root / "registry" / "wiki-export-manifest.json"), \
                mock.patch.object(br_module(), "CORPUS_ROOT", root), \
                mock.patch("fabric_config.get_vault_path", lambda: root / "vault"):
            br = br_module()
            br.harvest_before_export()
            (wiki / "a.md").write_text("v2\n")
            r1 = br.harvest_before_export()
            assert r1["harvested"] == 1
            # re-export re-records → re-running harvest doesn't duplicate
            br.harvest_before_export()  # baseline reset (no drift)
            r2 = br.harvest_before_export()
        assert r2["harvested"] == 0

    def test_orphans_tracked(self, tmp_path):
        root = tmp_path / "fabric"
        (root / "registry").mkdir(parents=True)
        (root / "evidence" / "raw").mkdir(parents=True)
        wiki = root / "vault" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "a.md").write_text("a\n")
        with mock.patch.object(br_module(), "MANIFEST_PATH", root / "registry" / "wiki-export-manifest.json"), \
                mock.patch.object(br_module(), "CORPUS_ROOT", root), \
                mock.patch("fabric_config.get_vault_path", lambda: root / "vault"):
            br = br_module()
            br.harvest_before_export()
            # a stray file appears that no export step wrote
            (wiki / "stray-old-layout.md").write_text("stray\n")
            r = br.harvest_before_export()
        assert r["orphans"] == 1
        m = json.loads((root / "registry" / "wiki-export-manifest.json").read_text())
        assert "stray-old-layout.md" in m["orphans"]


def br_module():
    """Loader indirection so tests patch the loaded module's MANIFEST_PATH."""
    return br_module()


def br_module():
    return sys.modules["obsidian_bridge"]


class TestPushNotes:
    def test_push_calls_rest(self, capsys):
        br = br_module()
        calls = []

        def fake_request(method, path, api_url, key, body=None, content_type="text/markdown"):
            calls.append((method, path, body))
            return 204, ""

        with mock.patch.object(br, "_request", fake_request), \
                mock.patch.object(br, "_integration_cfg", lambda: {"enabled": True,
                                                                   "api_url": "https://x",
                                                                   "api_key_env": "K"}), \
                mock.patch.object(br, "_resolve_key", lambda cfg: ("key123", "env")):
            w, f = br.push_notes([("a.md", "content"), ("sub/b.md", "more")])
        assert (w, f) == (2, 0)
        assert calls[0] == ("PUT", "a.md", "content")
        assert calls[1] == ("PUT", "sub/b.md", "more")

    def test_push_failure_counted(self, capsys):
        br = br_module()

        def fake_request(*a, **kw):
            raise RuntimeError("connection refused")

        with mock.patch.object(br, "_request", fake_request), \
                mock.patch.object(br, "_integration_cfg", lambda: {"enabled": True,
                                                                   "api_url": "https://x",
                                                                   "api_key_env": "K"}), \
                mock.patch.object(br, "_resolve_key", lambda cfg: ("k", "env")):
            w, f = br.push_notes([("a.md", "x")])
        assert (w, f) == (0, 1)


class TestGate:
    def test_disabled_returns_none(self, tmp_path):
        with mock.patch("fabric_config.get_integrations", lambda cfg: {"obsidian": {"enabled": False}}), \
                mock.patch("fabric_config.get_config", lambda: {"integrations": {"obsidian": {"enabled": False}}}):
            assert br_module()._integration_cfg() is None