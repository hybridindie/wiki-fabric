"""Tests for llm.local_model resolution + ensure_local_model (no network)."""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import pytest

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("", "cmd", "lib", "eval", "harness"):
    sys.path.insert(0, str(_SCRIPTS / _rel))


class TestGetLocalModel(unittest.TestCase):
    def test_explicit_config_wins(self):
        from fabric_config import get_local_model
        cfg = {"llm": {"local_model": "mlx-community/foo-4bit"}}
        assert get_local_model(cfg) == "mlx-community/foo-4bit"

    def test_platform_default_darwin(self):
        from fabric_config import get_local_model, DEFAULT_LOCAL_MODELS
        cfg = {"llm": {}}
        env = {k: v for k, v in os.environ.items() if k != "WIKI_LLM_LOCAL_MODEL"}
        with mock.patch.dict(os.environ, env, clear=True):
            got = get_local_model(cfg)
        assert got == DEFAULT_LOCAL_MODELS.get(sys.platform, DEFAULT_LOCAL_MODELS["default"])

    def test_env_override(self):
        from fabric_config import get_local_model
        cfg = {"llm": {}}
        with mock.patch.dict(os.environ, {"WIKI_LLM_LOCAL_MODEL": "org/env-model"}):
            assert get_local_model(cfg) == "org/env-model"


class TestGetStageRouteLocal(unittest.TestCase):
    def test_local_uses_llm_local_model(self):
        from fabric_config import get_stage_route
        cfg = {
            "llm": {"compiler_model": "cloud-model", "local_model": "mlx-community/my-local"},
            "repos": {"p": {"extract": "local"}},
        }
        with mock.patch.dict(os.environ, {"WIKI_MLX_MODEL": ""}):
            os.environ.pop("WIKI_MLX_MODEL", None)
            assert get_stage_route(cfg, "p", "extract") == "mlx-community/my-local"

    def test_local_wiki_mlx_model_env_still_wins(self):
        from fabric_config import get_stage_route
        cfg = {
            "llm": {"compiler_model": "cloud-model", "local_model": "mlx-community/my-local"},
            "repos": {"p": {"extract": "local"}},
        }
        with mock.patch.dict(os.environ, {"WIKI_MLX_MODEL": "explicit/env-model"}):
            assert get_stage_route(cfg, "p", "extract") == "explicit/env-model"

    def test_cloud_default_unchanged(self):
        from fabric_config import get_stage_route
        cfg = {"llm": {"compiler_model": "cloud-model"}, "repos": {"p": {}}}
        assert get_stage_route(cfg, "p", "extract") == "cloud-model"


class TestFindLocalModelPath(unittest.TestCase):
    def test_local_dir(self, tmp_path=None):
        import tempfile
        from fabric_config import find_local_model_path
        with tempfile.TemporaryDirectory() as d:
            assert find_local_model_path(d) == __import__("pathlib").Path(d)

    def test_missing_hf_id(self):
        from fabric_config import find_local_model_path
        assert find_local_model_path("org/definitely-not-a-real-model-xyz") is None


class TestLooksLikeLocalModel(unittest.TestCase):
    def test_hf_ondevice_ids(self):
        from fabric_config import looks_like_local_model
        assert looks_like_local_model("mlx-community/gemma-4-e4b-it-4bit")
        assert looks_like_local_model("unsloth/gemma-4-e4b-it-GGUF")
        assert looks_like_local_model("ISTA-DASLab/some-gguf-model")

    def test_provider_namespaced_rejected(self):
        from fabric_config import looks_like_local_model
        assert not looks_like_local_model("openai/gpt-4o")
        assert not looks_like_local_model("anthropic/claude-x")
        assert not looks_like_local_model("deepseek/deepseek-r1")

    def test_ollama_style_rejected(self):
        from fabric_config import looks_like_local_model
        assert not looks_like_local_model("qwen2.5-coder:7b")
        assert not looks_like_local_model("deepseek-v4.1-flash:cloud")
        assert not looks_like_local_model("plain-model-name")

    def test_gguf_and_mlx_substrings(self):
        from fabric_config import looks_like_local_model
        assert looks_like_local_model("model.Q4_K_M.gguf")
        assert looks_like_local_model("mlx-model-4bit")
        assert not looks_like_local_model("http://localhost:8080/v1")

    def test_local_path(self):
        import tempfile
        from fabric_config import looks_like_local_model
        with tempfile.TemporaryDirectory() as d:
            assert looks_like_local_model(d)


class TestLocalLlmBackendSelection(unittest.TestCase):
    def test_backend_for_shapes(self):
        from local_llm import backend_for
        assert backend_for("mlx-community/gemma-4-e4b-it-4bit") == "mlx"
        assert backend_for("unsloth/gemma-4-e4b-it-GGUF") == "gguf"
        assert backend_for("model.Q4_K_M.gguf") == "gguf"

    def test_resolve_gguf_in_dir(self):
        import tempfile
        from pathlib import Path
        from local_llm import _resolve_gguf_path
        with tempfile.TemporaryDirectory() as d:
            gguf = Path(d) / "model.Q4_K_M.gguf"
            gguf.write_bytes(b"x")
            other = Path(d) / "model.F16.gguf"
            other.write_bytes(b"y")
            assert _resolve_gguf_path(d) == gguf  # Q4_K_M preferred over F16

    def test_generate_unresolvable_raises(self):
        from local_llm import generate
        try:
            generate("x", "org/definitely-not-a-real-model-xyz-12345", max_tokens=1)
        except Exception:
            pass  # RuntimeError (load failure) is the expected contract
        else:
            # missing model should not silently succeed; hf may still be installed
            import importlib
            if importlib.util.find_spec("mlx_lm") or importlib.util.find_spec("llama_cpp"):
                raise AssertionError("expected failure for unresolvable model id")


class TestIsLocalRouteCrossPlatform(unittest.TestCase):
    def test_local_no_darwin_warning(self):
        from fabric_config import get_stage_route
        cfg = {
            "llm": {"compiler_model": "cloud-model", "local_model": "unsloth/gemma-4-e4b-it-GGUF"},
            "repos": {"p": {"extract": "local"}},
        }
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # any warning = fail
            assert get_stage_route(cfg, "p", "extract") == "unsloth/gemma-4-e4b-it-GGUF"


class TestLintLlmConfig(unittest.TestCase):
    def _check(self, cfg):
        from lint import check_llm_config
        return check_llm_config(cfg)

    def test_reject_ollama_tag(self):
        probs = self._check({"llm": {"local_model": "qwen2.5-coder:7b"}})
        assert probs and "LLM-CONFIG" in probs[0]

    def test_reject_provider_namespaced(self):
        probs = self._check({"llm": {"local_model": "openai/gpt-4o"}})
        assert probs

    def test_accept_hf_id(self):
        assert self._check({"llm": {"local_model": "mlx-community/gemma-4-e4b-it-4bit"}}) == []

    def test_unset_ok(self):
        assert self._check({"llm": {}}) == []
        assert self._check({}) == []


class TestEnsureLocalModel(unittest.TestCase):
    """These mock the huggingface_hub import points, so they need the module
    importable. Skip as a group when huggingface_hub isn't installed (CI fast
    venv); the guarded-import path in fabric_config is exercised instead."""

    @classmethod
    def setUpClass(cls):
        try:
            import huggingface_hub  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("huggingface_hub not installed (fast venv)")

    def test_non_tty_no_prompt_no_download(self):
        from fabric_config import ensure_local_model
        # missing model + non-tty (mocked) -> returns (None, False), never downloads
        with mock.patch("fabric_config.find_local_model_path", return_value=None), \
             mock.patch("fabric_config.sys.stdin.isatty", return_value=False, create=True), \
             mock.patch("fabric_config.sys.stdout.isatty", return_value=False, create=True), \
             mock.patch("builtins.input") as inp, \
             mock.patch("huggingface_hub.snapshot_download") as dl:
            path, downloaded = ensure_local_model("org/not-downloaded-xyz")
        assert path is None and downloaded is False
        inp.assert_not_called()
        dl.assert_not_called()

    def test_assume_yes_downloads_single_gguf_split(self):
        from fabric_config import ensure_local_model
        with mock.patch("fabric_config.find_local_model_path", return_value=None), \
             mock.patch("fabric_config.gguf_preferred_file",
                        return_value="gemma-4-E4B-it-Q4_K_M.gguf"), \
             mock.patch("huggingface_hub.hf_hub_download") as dl, \
             mock.patch("huggingface_hub.snapshot_download") as snap:
            path, downloaded = ensure_local_model("unsloth/gemma-4-e4b-it-GGUF", assume_yes=True)
        assert downloaded is True
        dl.assert_called_once_with("unsloth/gemma-4-e4b-it-GGUF", "gemma-4-E4B-it-Q4_K_M.gguf")
        snap.assert_not_called()  # never pulls every quantization split

    def test_assume_yes_downloads_mlx_repo(self):
        from fabric_config import ensure_local_model
        with mock.patch("fabric_config.find_local_model_path", return_value=None), \
             mock.patch("huggingface_hub.snapshot_download") as snap:
            path, downloaded = ensure_local_model("mlx-community/gemma-4-e4b-it-4bit", assume_yes=True)
        assert downloaded is True
        snap.assert_called_once_with("mlx-community/gemma-4-e4b-it-4bit")

    def test_user_declines(self):
        from fabric_config import ensure_local_model
        with mock.patch("fabric_config.find_local_model_path", return_value=None), \
             mock.patch("fabric_config.sys.stdin.isatty", return_value=True, create=True), \
             mock.patch("fabric_config.sys.stdout.isatty", return_value=True, create=True), \
             mock.patch("builtins.input", return_value="n"):
            path, downloaded = ensure_local_model("org/declined-model")
        assert path is None and downloaded is False

    def test_present_model_noop(self):
        import tempfile
        from fabric_config import ensure_local_model
        with tempfile.TemporaryDirectory() as d:
            with mock.patch("huggingface_hub.snapshot_download") as dl:
                resolved, downloaded = ensure_local_model(d)
        assert resolved == d and downloaded is False


# === Live backend tests ===
# GGUF (llama-cpp-python) runs everywhere -> always exercised.
# MLX is darwin-only -> gated on sys.platform == "darwin" AND mlx_lm importable
# AND the cached model present; skipped cleanly otherwise.
#
# These run real models (seconds to minutes per test) — marked "live" so slow
# machines / CI can deselect:  pytest -m "not live"


def _gguf_available():
    try:
        import llama_cpp  # noqa: F401
        from local_llm import _resolve_gguf_path
        return _resolve_gguf_path("unsloth/gemma-4-e4b-it-GGUF") is not None
    except Exception:
        return False


def _mlx_available():
    if sys.platform != "darwin":
        return False
    try:
        import mlx_lm  # noqa: F401
        from fabric_config import find_local_model_path
        return find_local_model_path("mlx-community/gemma-4-e4b-it-4bit") is not None
    except Exception:
        return False


_GGUF_REASON = "gguf backend (llama-cpp-python + cached unsloth/gemma-4-e4b-it-GGUF)"
_MLX_REASON = "mlx backend (darwin + mlx-lm + cached mlx-community/gemma-4-e4b-it-4bit)"


class TestGgufBackendLive(unittest.TestCase):
    """Real GGUF generation — universal backend, always on when model cached."""
    pytestmark = pytest.mark.live

    @unittest.skipUnless(_gguf_available(), _GGUF_REASON)
    def test_pong(self):
        from local_llm import generate
        out = generate("Reply with exactly: PONG", "unsloth/gemma-4-e4b-it-GGUF",
                       max_tokens=32)
        assert "PONG" in out.upper()

    @unittest.skipUnless(_gguf_available(), _GGUF_REASON)
    def test_chat_tuned_model_returns_nonempty_for_prompt(self):
        # regression: raw create_completion returns '' for gemma; the chat path
        # must be used so a non-trivial instruction prompt yields text.
        from local_llm import generate
        out = generate("Summarize in one short sentence: The sky is blue.",
                       "unsloth/gemma-4-e4b-it-GGUF", max_tokens=64)
        assert len(out.strip()) > 0


@unittest.skipUnless(_mlx_available(), _MLX_REASON)
class TestMlxBackendLive(unittest.TestCase):
    """Real MLX generation — darwin-gated (skips on any other platform)."""
    pytestmark = pytest.mark.live

    _MODEL = "mlx-community/gemma-4-e4b-it-4bit"

    def test_pong(self):
        from local_llm import generate
        out = generate("Reply with exactly: PONG", self._MODEL, max_tokens=32)
        assert "PONG" in out.upper()

    def test_backend_for_mlx_id(self):
        from local_llm import backend_for
        assert backend_for(self._MODEL) == "mlx"

    def test_extraction_produces_claims(self):
        import tempfile
        from ingest import extract_claims_mlx
        src = Path(tempfile.gettempdir()) / "wf-mlx-test-doc.md"
        src.write_text(
            "# Retry With Backoff\n\n"
            "The payment service retries failed webhook deliveries up to 5 times.\n"
            "Retries use exponential backoff starting at 1 second.\n"
            "After 5 failures the event is written to the dead-letter queue.\n")
        claims = extract_claims_mlx(src.read_text(), src, self._MODEL)
        assert len(claims) >= 1, f"expected >=1 claim, got {claims}"
        assert any("retry" in str(c.get("statement", "")).lower() for c in claims)

    def test_synth_json_roundtrip(self):
        import json
        import re as _re
        from local_llm import generate
        from synthesize import SYNTH_PROMPT
        claims_text = ("- [claim-a] Retries use exponential backoff starting at 1 "
                       "second. (status=confirmed, conf=high)\n"
                       "- [claim-b] After 5 failures the event is written to the "
                       "dead-letter queue. (status=confirmed, conf=high)")
        prompt = SYNTH_PROMPT.replace("{claims_block}", claims_text)
        out = generate(prompt, self._MODEL, max_tokens=4096)
        m = _re.search(r"\{.*\}", out, _re.DOTALL)
        assert m, f"no JSON in mlx output: {out[:200]!r}"
        parsed = json.loads(m.group())
        assert parsed.get("title")


class TestGetConfigMemoization(unittest.TestCase):
    def test_defaults_not_mutated_by_get_config(self):
        """Regression: get_config() shallow-copied _DEFAULTS and .update()'d
        nested dicts in place, leaking user config (integrations.graphify,
        llm keys) into the defaults for the rest of the process.

        Uses a synthetic user config rather than this repo's (gitignored)
        fabric.yaml so it holds in CI too."""
        from fabric_config import get_config, get_config_clear_cache, _DEFAULTS
        import copy as _copy
        snapshot = _copy.deepcopy(_DEFAULTS)
        cfg = get_config()  # warm cache with the real config first
        user_cfg = {"integrations": {"graphify": {"enabled": True, "graph_dir": "x"}}}
        # simulate a config load with user data merged (what get_config does)
        import copy as _copy2
        import fabric_config as fc
        test_cfg = fc._merge_user_config(_copy2.deepcopy(fc._DEFAULTS), user_cfg)
        assert test_cfg["integrations"]["graphify"]["enabled"] is True
        assert _DEFAULTS["integrations"]["graphify"]["graph_dir"] == snapshot[
            "integrations"]["graphify"]["graph_dir"], "_DEFAULTS mutated by merge"
        assert _DEFAULTS == snapshot, "_DEFAULTS mutated by get_config()"
        get_config_clear_cache()

    def test_cache_invalidation_on_env_change(self):
        import os
        from fabric_config import get_config
        base = get_config()["llm"]["model"]
        with mock.patch.dict(os.environ, {"WIKI_LLM_MODEL": "env-test-model"}):
            assert get_config()["llm"]["model"] == "env-test-model"
        assert get_config()["llm"]["model"] == base

    def test_repeated_calls_return_same_object(self):
        from fabric_config import get_config
        assert get_config() is get_config()


if __name__ == "__main__":
    unittest.main()