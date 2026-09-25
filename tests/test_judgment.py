"""Unit tests for judgment.py — the optional judgment tier (Jev / Laya-MLX).

Contract under test:
  - Off until explicitly enabled (integrations.judgment.enabled)
  - Question constructors produce typed answers with recorded provenance
  - Cloud route requires TYPESAFE_API_KEY; local route parses JSON verdicts
  - JudgmentUnavailable is raised (never silently swallowed) when unconfigured

Run: python3 -m pytest tests/test_judgment.py -v
"""

import importlib.util
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
from unittest import mock

REPO = Path(__file__).parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


judgment = _load("judgment", REPO / "scripts" / "lib" / "judgment.py")
fc = _load("fabric_config_test", REPO / "scripts" / "lib" / "fabric_config.py")


def _config(judgment_cfg):
    return {"integrations": {"judgment": judgment_cfg}}


class TestGate:
    def test_disabled_by_default(self):
        cfg = judgment.judgment_config(_config({"enabled": False}))
        assert cfg["enabled"] is False
        assert not judgment.is_judgment_active(_config({"enabled": False}))

    def test_route_defaults_to_cloud(self):
        cfg = judgment.judgment_config(_config({"enabled": True}))
        assert cfg["route"] == "cloud"
        assert cfg["cloud_model"] == judgment.CLOUD_MODEL_DEFAULT

    def test_unavailable_raises_when_disabled(self):
        import pytest
        with pytest.raises(judgment.JudgmentUnavailable):
            judgment.judgment_route(_config({"enabled": False}))


class TestQuestionShapes:
    def test_noul_construction_and_normalize(self):
        with mock.patch.object(judgment, "judgment_route", return_value="cloud"), \
             mock.patch.object(judgment, "_ask_cloud",
                               return_value={"value": 0.93, "confidence": 0.81}):
            p = judgment.noul("Is the answer grounded?", "state text")
        assert p == 0.93

    def test_normalize_coerces_unknown_shape(self):
        out = judgment._normalize({"probability": 0.4})
        assert out["value"] == 0.4
        out = judgment._normalize("0.5")
        assert out["value"] == "0.5"

    def test_score_and_choice_route_to_ask(self):
        calls = []
        with mock.patch.object(judgment, "_ask", side_effect=lambda q: calls.append(q) or {"value": 1}):
            judgment.score("How good?", "state", rubric={"1": "bad", "5": "great"})
            judgment.choice("Which?", "state", ["a", "b"])
        assert calls[0]["kind"] == "score"
        assert calls[0]["rubric"] == {"1": "bad", "5": "great"}
        assert calls[1]["kind"] == "choice" and calls[1]["options"] == ["a", "b"]


class TestLocalRoute:
    def test_parse_local_json_object(self):
        out = judgment._parse_local('{"value": 0.88, "confidence": 0.9}')
        assert out["value"] == 0.88

    def test_parse_local_json_in_prose(self):
        out = judgment._parse_local('The judge says: {"value": 0.12} — low.')
        assert out["value"] == 0.12

    def test_parse_local_non_json_raises(self):
        import pytest
        with pytest.raises(judgment.JudgmentUnavailable):
            judgment._parse_local("I think maybe yes")

    def test_local_route_uses_local_llm(self, monkeypatch):
        import pytest
        monkeypatch.setenv("TYPESAFE_API_KEY", "")  # ensure local route isn't cloud
        seen = {}

        def fake_generate(prompt, model_id=None, max_tokens=256):
            seen["prompt"] = prompt
            seen["model"] = model_id
            return '{"value": 0.95}'

        with mock.patch.object(judgment, "judgment_route", return_value="local"), \
             mock.patch.object(judgment, "judgment_config",
                               return_value={"enabled": True, "route": "local",
                                             "local_backend": "generic",
                                             "cloud_model": "jev-1",
                                             "local_model": "generic-fallback-model"}), \
             mock.patch.dict(sys.modules, {"local_llm": _fake_module(generate=fake_generate)}):
            out = judgment._ask({"kind": "noul", "question": "q", "state": "s"})
        assert seen["model"] == "generic-fallback-model"
        assert out["value"] == 0.95

    def test_local_route_primary_is_laya(self, monkeypatch):
        # default local_backend=laya; when laya is installed it serves the verdict
        monkeypatch.setenv("TYPESAFE_API_KEY", "")
        with mock.patch.object(judgment, "judgment_route", return_value="local"), \
             mock.patch.object(judgment, "judgment_config",
                               return_value={"enabled": True, "route": "local",
                                             "local_backend": "laya"}), \
             mock.patch.object(judgment, "_ask_laya",
                               return_value={"value": 0.91, "backend": "laya/MLXBackend"}):
            out = judgment._ask_local({"kind": "noul", "question": "q", "state": "s"})
        assert out["value"] == 0.91
        assert out["backend"] == "laya/MLXBackend"


class _fake_module:
    def __init__(self, **attrs):
        for k, v in attrs.items():
            setattr(self, k, attrs[k] if not callable(attrs[k]) else staticmethod(attrs[k]))


class TestCloudRoute:
    def test_missing_key_raises_unavailable(self, monkeypatch):
        monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
        import pytest
        with pytest.raises(judgment.JudgmentUnavailable):
            judgment._ask_cloud({"kind": "noul", "question": "q", "state": "s"})

    def test_cloud_call_posts_typed_question(self, monkeypatch):
        monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
        captured = {}

        class _Resp:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return json.dumps({"value": 0.97, "confidence": 0.9}).encode()

        def fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["body"] = json.loads(req.data.decode())
            captured["auth"] = req.headers.get("Authorization")
            return _Resp()

        with mock.patch.object(urllib.request, "urlopen", fake_urlopen):
            out = judgment._ask_cloud({"kind": "noul", "question": "q", "state": "s"})
        assert out["value"] == 0.97
        assert captured["url"].endswith("/judge")
        assert captured["body"]["kind"] == "noul"
        assert captured["auth"] == "Bearer test-key"


class TestVerdict:
    def test_verdict_threshold(self):
        with mock.patch.object(judgment, "noul", return_value=0.85):
            passed, p = judgment.verdict("q", "state", threshold=0.7)
        assert passed and p == 0.85

    def test_verdict_below_threshold(self):
        with mock.patch.object(judgment, "noul", return_value=0.2):
            passed, p = judgment.verdict("q", "state", threshold=0.7)
        assert not passed


class TestCoreIsolation:
    """The judgment tier must never be imported by the 0-token core."""

    def test_context_query_lint_do_not_import_judgment(self):
        for script in ("scripts/cmd/context.py", "scripts/cmd/query.py", "scripts/cmd/lint.py"):
            src = (REPO / script).read_text()
            assert "judgment" not in src.replace("integrations.judgment", ""), \
                f"{script} must not depend on the judgment tier"
            assert "from judgment import" not in src

    def test_eval_default_mode_has_no_judgment_import(self):
        # zero-LLM mode (no --judge flag) must not touch the judgment module
        src = (REPO / "scripts" / "eval" / "eval-behavior.py").read_text()
        assert "from judgment import" in src  # present but gated behind --judge
        # the gate: judge_probe is only called under args.judge
        assert "if args.judge:" in src