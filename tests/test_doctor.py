"""Unit tests for doctor.py — environment drift diagnosis.

All endpoint calls mocked; no live network in CI.

Run: python3 -m pytest tests/test_doctor.py -v
"""
import importlib.util
import json
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


doctor = _load("doctor", REPO / "scripts" / "cmd" / "doctor.py")


class TestEndpointModels:
    def test_lists_models(self):
        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps({"data": [{"id": "a"}, {"id": "b"}]}).encode()

        with mock.patch.object(doctor.urllib.request, "urlopen", return_value=_Resp()):
            models = doctor.endpoint_models("http://x/v1", "key")
        assert models == ["a", "b"]

    def test_unreachable_returns_none(self):
        with mock.patch.object(doctor.urllib.request, "urlopen",
                               side_effect=Exception("conn refused")):
            assert doctor.endpoint_models("http://x/v1", "key") is None


class TestCoreIsolation:
    def test_doctor_does_not_import_judgment_at_import_time(self):
        # judgment import must be lazy (inside the check) so doctor runs
        # without the tier installed
        src = (REPO / "scripts" / "cmd" / "doctor.py").read_text()
        assert "from judgment import" in src or "import judgment" in src
        # and it must be inside a function/try, not module level
        # module-level import lines only (top-of-file imports, not docstring/try)
        module_level = [l for l in src.split("\n")[:35]
                        if l.strip().startswith(("from judgment", "import judgment"))]
        assert module_level == [], "judgment import must be lazy (inside main's try)"

    def test_never_mutates(self):
        src = (REPO / "scripts" / "cmd" / "doctor.py").read_text()
        assert ".write_text(" not in src and ".mkdir(" not in src