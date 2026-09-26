"""Tuning section: constants read from fabric.yaml with shipped defaults.

Contract: defaults reproduce shipped behavior exactly (G2-style no-op) —
calibration provenance travels with each value (see #63, #39).

Run: python3 -m pytest tests/test_tuning.py -v
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


fc = _load("fabric_config_test", REPO / "scripts" / "lib" / "fabric_config.py")


class TestTuning:
    def test_defaults_match_shipped_values(self):
        cfg = {"tuning": {}}
        assert fc.get_tuning(cfg, "mining", "min_projects", 2) == 2
        assert fc.get_tuning(cfg, "judgment", "mining_threshold", 0.8) == 0.8
        assert fc.get_tuning(cfg, "judgment", "near_band", 0.1) == 0.1
        assert fc.get_tuning(cfg, "context", "nav_max_files", 5) == 5

    def test_override_wins(self):
        cfg = {"tuning": {"judgment": {"near_band": 0.2}}}
        assert fc.get_tuning(cfg, "judgment", "near_band", 0.1) == 0.2
        # unset keys still fall back
        assert fc.get_tuning(cfg, "judgment", "mining_threshold", 0.8) == 0.8

    def test_getter_via_config(self):
        cfg = {"tuning": {"mining": {"min_projects": 3}}}
        assert fc.get_tuning(cfg, "mining", "min_projects") == 3

    def test_bad_section_returns_default(self):
        cfg = {"tuning": {"judgment": "not-a-dict"}}
        assert fc.get_tuning(cfg, "judgment", "near_band", 0.1) == 0.1
