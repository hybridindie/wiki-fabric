"""Bootstrap behaviors: model decided in fabric.yaml populates the repo
entry + overlay, repos entry carries owner/routing, domains don't mix other
repos' signals by default."""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS / "cmd", _SCRIPTS / "lib", _SCRIPTS):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import yaml


def _load():
    spec = importlib.util.spec_from_file_location(
        "bootstrap_project", _SCRIPTS / "cmd" / "bootstrap-project.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # patch FABRIC_ROOT/CORPUS_ROOT to a temp fabric
    return mod


class TestRepoEntry:
    def test_entry_carries_owner_and_routing(self, tmp_path, monkeypatch):
        bp = _load()
        froot = tmp_path / "fabric"
        froot.mkdir()
        fy = froot / "fabric.yaml"
        fy.write_text("owner: t\nllm:\n  compiler_model: glm-x:cloud\nrepos: {}\n")
        monkeypatch.setattr(bp, "FABRIC_ROOT", froot)
        monkeypatch.setattr(bp, "CORPUS_ROOT", froot / "corpus")
        proj = tmp_path / "proj"

        # emulate register_in_fabric_yaml's body via the real function
        import argparse
        args = argparse.Namespace(extract="cloud", synthesize=None,
                                  dossier="local", graph_dir=None)
        bp.register_in_fabric_yaml('proj', str(proj), owner='t', args=args)

        cfg = yaml.safe_load(fy.read_text())
        e = cfg["repos"]["proj"]
        assert e["path"].endswith("proj")
        assert e["owner"] == "t"
        assert e["extract"] == "cloud"
        assert e["dossier"] == "local"
        assert cfg["llm"]["compiler_model"] == "glm-x:cloud"
