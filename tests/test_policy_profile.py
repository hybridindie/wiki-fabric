"""Policy profile v1 (#66): compilation policy as a versioned artifact.

default-coding-agent.yaml = shipped behavior, byte-identical. Invalid/
missing profiles fall back to built-ins. Behavior evals gate profiles.

Run: python3 -m pytest tests/test_policy_profile.py -v
"""
import importlib.util
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ctx = _load("context", REPO / "scripts" / "cmd" / "context.py")


class TestPolicyProfile:
    def test_default_profile_loads(self):
        p = ctx._load_policy_profile()
        assert p is not None
        assert p["schema"] == "wiki-fabric/policy-profile-v1"
        assert p["name"] == "default-coding-agent"

    def test_profile_matches_builtin_tiers(self):
        p = ctx._load_policy_profile()
        assert p["tiers"]["P1-project"] == ["decision", "experience-event", "commitment", "claim"]
        assert p["tiers"]["P2-domain"] == ["pattern", "anti-pattern", "skill", "question"]
        assert p["tiers"]["P3-global"] == ["pattern", "anti-pattern", "skill", "concept"]
        assert p["tier_order"] == ["P1-project", "P2-domain", "P3-global"]

    def test_invalid_schema_falls_back(self, tmp_path, monkeypatch):
        # _HERE points at scripts/cmd; parent.parent = repo root. Build a
        # fabric tree whose profile has a wrong schema.
        fabric = tmp_path / "harness"
        (fabric / "scripts" / "cmd").mkdir(parents=True)
        shutil.copy(REPO / "scripts" / "cmd" / "context.py", fabric / "scripts" / "cmd" / "context.py")
        d = fabric / "system" / "policy-profiles"
        d.mkdir(parents=True)
        (d / "default-coding-agent.yaml").write_text("schema: wrong\nname: broken\n")
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("ctx2", fabric / "scripts" / "cmd" / "context.py")
        ctx2 = _ilu.module_from_spec(spec)
        spec.loader.exec_module(ctx2)
        assert ctx2._load_policy_profile() is None

    def test_missing_profile_falls_back(self, tmp_path, monkeypatch):
        import importlib.util as _ilu
        fabric = tmp_path / "harness"
        (fabric / "scripts" / "cmd").mkdir(parents=True)
        shutil.copy(REPO / "scripts" / "cmd" / "context.py", fabric / "scripts" / "cmd" / "context.py")
        spec = _ilu.spec_from_file_location("ctx3", fabric / "scripts" / "cmd" / "context.py")
        ctx3 = _ilu.module_from_spec(spec)
        spec.loader.exec_module(ctx3)
        assert ctx3._load_policy_profile() is None
