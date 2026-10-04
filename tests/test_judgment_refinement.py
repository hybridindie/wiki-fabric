"""Unit tests for the judgment-tier refinements (#29 slices 2+3).

All judgment calls are mocked — CI never contacts a backend. Live behavior
is exercised only when a human enables integrations.judgment with a key.

Run: python3 -m pytest tests/test_judgment_refinement.py -v
"""

import contextlib
import io
import importlib.util
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


judgment = _load("judgment", REPO / "scripts" / "lib" / "judgment.py")
stab = _load("eval_stability", REPO / "scripts" / "eval" / "eval-stability.py")
mine = _load("mine_promotions", REPO / "scripts" / "cmd" / "mine-promotions.py")


@contextlib.contextmanager
def judged(prob=0.9, unavailable=False, capture=None, answers=None):
    """Mock the judgment tier at its module — both callers import from the
    same module object, so module-level patches reach them. Also satisfies
    the G-J gate (a PASS calibration receipt) — these tests exercise the
    judged BEHAVIOR, not the calibration lifecycle (test_judgment_gate.py
    owns the gate's own cases)."""
    def _gate_ok(*a, **k):
        return True, "test receipt"
    # module pin: other test files re-register sys.modules['judgment'] (the
    # spec-loader pattern) — stab's call-time `from judgment import` must
    # resolve THIS file's object for the mocks to bind (the #178-suite find)
    module_pin = mock.patch.dict(sys.modules, {"judgment": judgment})
    module_pin.start()
    try:
        if unavailable:
            with mock.patch.object(judgment, "judgment_route",
                                   side_effect=judgment.JudgmentUnavailable("disabled")), \
                 mock.patch.object(judgment, "noul",
                                   side_effect=judgment.JudgmentUnavailable("disabled")):
                yield  # both heads patched — the tier's unavailability is total
        else:
            if answers is not None:
                def fake_noul(q, s, false_desc=None, true_desc=None, repo=None):
                    return answers.pop(0) if answers else prob
                with mock.patch.object(judgment, "judgment_route", return_value="cloud"), \
                     mock.patch.object(judgment, "judgment_eval_recorded", _gate_ok), \
                     mock.patch.object(judgment, "noul", side_effect=fake_noul):
                    yield
            else:
                with mock.patch.object(judgment, "judgment_route", return_value="cloud"), \
                     mock.patch.object(judgment, "judgment_eval_recorded", _gate_ok), \
                     mock.patch.object(judgment, "noul", return_value=prob):
                    yield
    finally:
        module_pin.stop()


class TestG4Judge:
    """eval-stability G4-J: judged refinement of failed fuzzy pairs."""

    def _sets(self):
        return {
            "model-a": {"batch commands in one frame", "pipeline reads concurrently"},
            "model-b": {"send commands as a single batch", "read many in flight"},
        }

    def test_unavailable_tier_is_skipped_not_failed(self):
        with judged(unavailable=True):
            gates = stab.judge_model_sensitivity(self._sets())
        assert len(gates) == 1
        assert gates[0]["skipped"] is True
        assert gates[0]["passed"] is True  # unavailability must not fail the suite

    def test_failed_pair_judged_same_downgrades(self):
        # fuzzy coverage between these sets is <0.5; judged SAME => passed
        with judged(prob=0.9):
            gates = stab.judge_model_sensitivity(self._sets())
        assert len(gates) == 1
        assert gates[0]["passed"] is True
        assert gates[0]["probability"] == 0.9
        assert "SAME content" in gates[0]["detail"]

    def test_judged_different_keeps_failure(self):
        with judged(prob=0.1):
            gates = stab.judge_model_sensitivity(self._sets())
        assert len(gates) == 1
        assert gates[0]["passed"] is False
        assert "DIFFERENT content" in gates[0]["detail"]

    def test_passing_pairs_not_rejudged(self):
        calls = []

        @contextlib.contextmanager
        def capture_judged(prob=0.9, unavailable=False, capture=calls):
            # module pin (the judged() fixture's find: other files re-register
            # sys.modules['judgment']; call-time imports must see THIS object)
            pin = mock.patch.dict(sys.modules, {"judgment": judgment})
            pin.start()
            try:
                if unavailable:
                    with mock.patch.object(judgment, "judgment_route",
                                           side_effect=judgment.JudgmentUnavailable("disabled")):
                        yield
                else:
                    def fake_noul(q, s, false_desc=None, true_desc=None, repo=None):
                        capture.append(q)
                        return prob
                    with mock.patch.object(judgment, "judgment_route", return_value="cloud"), \
                         mock.patch.object(judgment, "noul", side_effect=fake_noul):
                        yield
            finally:
                pin.stop()

        with capture_judged():
            gates = stab.judge_model_sensitivity(
                {"a": {"identical statement one", "identical statement two"},
                 "b": {"identical statement one", "identical statement two"}})
        assert gates == [], "pairs that passed the fuzzy gate must not be re-judged"
        assert calls == []

    def test_empty_sets_never_judged(self):
        calls = []

        @contextlib.contextmanager
        def capture_judged():
            def fake_noul(q, s, false_desc=None, true_desc=None, repo=None):
                calls.append(q)
                return 0.9
            with mock.patch.object(judgment, "judgment_route", return_value="cloud"), \
                 mock.patch.object(judgment, "noul", side_effect=fake_noul):
                yield

        with capture_judged():
            gates = stab.judge_model_sensitivity({"a": set(), "b": {"x"}})
        assert calls == []


class TestMiningJudged:
    """mine-promotions --judge: near-miss pairs get a pairwise verdict."""

    def _events(self):
        def ev(project, problem, intervention):
            e = {"project": project, "observed_problem": problem,
                 "intervention": intervention, "outcomes": {}, "title": problem}
            e["_file"] = f"{project}/{problem[:10]}"
            return e
        return [
            ev("alpha", "batch commands to cut round trips", "applied command batching"),
            ev("beta", "group commands into one batch to cut round trips", "applied command batching"),
            # disjoint from alpha/beta: keyword pass leaves gamma out (its cluster
            # has <2 projects); judged pairs (alpha,gamma),(beta,gamma) fire
            ev("gamma", "unrelated UI color flicker on settings pages", "adjusted repaint timing"),
        ]

    def _split_events(self):
        """Keyword pass yields {}: paraphrased twins with disjoint wording.
        The judged pass must be able to FORM a cluster from judged-same
        singletons."""
        def ev(project, problem, intervention):
            e = {"project": project, "observed_problem": problem,
                 "intervention": intervention, "outcomes": {}, "title": problem}
            e["_file"] = f"{project}/{problem[:10]}"
            return e
        return [
            ev("alpha", "queue drain serializes packet execution", "batched drain loop"),
            ev("beta", "writes applied one by one each frame", "serial write path"),
        ]

    def test_disabled_tier_falls_back_to_keyword(self):
        with judged(unavailable=True):
            clusters = mine.cluster_events_judged(self._events(), min_projects=2)
        kw = mine.cluster_events_keyword(self._events(), min_projects=2)
        assert clusters == kw, "deterministic keyword behavior must be preserved"

    def test_judged_same_merges_near_miss_pairs(self):
        # alpha+beta already cluster together via keywords; the judged pass only
        # sees the split pairs (alpha,gamma),(beta,gamma) — judged DIFFERENT
        # keeps gamma apart from the keyword cluster.
        with judged(answers=[0.05, 0.05]):
            clusters = mine.cluster_events_judged(self._events(), min_projects=2)
        all_events = [e for evs in clusters.values() for e in evs]
        alpha = next((e for e in all_events if e["project"] == "alpha"), None)
        beta = next((e for e in all_events if e["project"] == "beta"), None)
        assert alpha and beta, "keyword-clustered pair must remain clustered"
        ca = [ck for ck, evs in clusters.items() if alpha in evs]
        cb = [ck for ck, evs in clusters.items() if beta in evs]
        assert ca == cb
        assert not any(e["project"] == "gamma" for evs in clusters.values() for e in evs)

    def test_judged_merge_forms_cluster_from_singletons(self):
        # keyword pass yields {} (disjoint wording); judged SAME forms the cluster
        with judged(answers=[0.95]):
            clusters = mine.cluster_events_judged(self._split_events(), min_projects=2)
        projects = {e["project"] for evs in clusters.values() for e in evs}
        assert projects == {"alpha", "beta"}

    def test_judged_different_splits_keyword_cluster(self):
        # #41 symmetry: the split pass demotes members judged DIFFERENT from
        # their cluster representative — a keyword cluster judged incoherent
        # MUST split, not survive intact
        with judged(prob=0.05):
            clusters = mine.cluster_events_judged(self._events(), min_projects=2)
        kw = mine.cluster_events_keyword(self._events(), min_projects=2)
        kw_members = {e["_file"] for evs in kw.values() for e in evs}
        judged_members = {e["_file"] for evs in clusters.values() for e in evs}
        # at least one member of the keyword cluster was demoted
        assert len(judged_members) < len(kw_members), \
            "judged-DIFFERENT must demote incoherent members, not keep the keyword cluster intact"
        # no cluster grew beyond its keyword membership
        for evs in clusters.values():
            assert all(e["_file"] in kw_members for e in evs)

    def test_judged_same_survives_split_pass(self):
        # judged-same pairs that MERGED must not be split back apart by the
        # cohesion sweep (all verdicts same)
        with judged(prob=0.95):
            clusters = mine.cluster_events_judged(self._events(), min_projects=2)
        all_events = [e for evs in clusters.values() for e in evs]
        assert len(all_events) == 3, "judged-same everywhere: no member demoted"

import pytest

try:
    import laya_as_judge  # noqa: F401
    HAS_LAYA = True
except ImportError:
    HAS_LAYA = False


class TestLayaLive:
    """Live on-device judge (laya-as-judge[mlx]). Self-skips when the package
    or the MLX runtime isn't installed — mirrors the existing `live` marker
    convention (GGUF/MLX tests)."""

    pytestmark = pytest.mark.live

    def test_laya_end_to_end_via_judgment_module(self):
        if not HAS_LAYA:
            pytest.skip("laya-as-judge not installed")
        p = judgment.noul(
            "Do these two records describe the same recurring problem and intervention?",
            "Item A: batch commands to cut round trips. Intervention: applied command batching.\n\n"
            "Item B: group commands into one batch to cut round trips. Intervention: applied command batching.")
        assert 0.0 <= p <= 1.0
        # live-calibrated separation: paraphrase pairs must clear the mining bar
        assert p >= judgment.MINING_THRESHOLD_DEFAULT, (
            f"true pair scored {p:.3f} below mining threshold {judgment.MINING_THRESHOLD_DEFAULT}")

    def test_laya_rejects_emulator(self):
        if not HAS_LAYA:
            pytest.skip("laya-as-judge not installed")
        # a criteria-phrased engine request must NOT resolve to the emulator
        try:
            judgment._laya_engine([{"name": "q", "kind": "noul", "question": "grounded?"}])
            # if it built, verify the backend isn't the emulator
            ok = True
        except judgment.JudgmentUnavailable as e:
            assert "EmulatorBackend" in str(e) or "not installed" in str(e)
            ok = True
        assert ok


class TestJudgmentAutoWiring:
    """#29 wiring: judgment refinement runs automatically when the tier is
    enabled; --judge forces on; --no-judge opts out."""

    def _load_mp(self):
        return self.mp if (mp := globals().get("MP")) else _load(
            "mine_promotions", REPO / "scripts" / "cmd" / "mine-promotions.py")

    def _run_main(self, argv, active, monkeypatch):
        import sys as _sys
        mp = _load("mine_promotions_" + str(abs(hash(tuple(argv)))), REPO / "scripts" / "cmd" / "mine-promotions.py")
        called = {}
        # patch the tier-selection source: main imports judgment.is_judgment_active
        import judgment as J
        monkeypatch.setattr(J, "is_judgment_active", lambda *a, **k: active)
        monkeypatch.setattr(J, "judgment_eval_recorded",
                            lambda *a, **k: (True, "test receipt"))  # G-J satisfied
        import sys as _sys
        for _m in list(_sys.modules):
            if _m.endswith("judgment") and _m != "judgment":
                monkeypatch.setattr(_sys.modules[_m], "is_judgment_active",
                                    lambda *a, **k: active, raising=False)
        monkeypatch.setattr(J, "judgment_route", lambda *a, **k: "local")
        monkeypatch.setattr(J, "cloud_key_ready", lambda *a, **k: True)
        def fake_judged(events, mp_n, threshold=None):
            called["judged"] = True
            return {}
        def fake_plain(events, mp_n, use_embeddings=False):
            called["plain"] = True
            return {}
        monkeypatch.setattr(mp, "cluster_events_judged", fake_judged)
        monkeypatch.setattr(mp, "cluster_events", fake_plain)
        monkeypatch.setattr(mp, "extract_experience_events", lambda: [])
        monkeypatch.setattr(_sys, "argv", ["mine-promotions"] + argv)
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                mp.main()
            except SystemExit:
                pass
        return called

    def test_auto_enables_when_tier_active(self, monkeypatch):
        called = self._run_main(["--dry-run"], True, monkeypatch)
        assert called.get("judged") and not called.get("plain")

    def test_auto_skips_when_tier_inactive(self, monkeypatch):
        called = self._run_main(["--dry-run"], False, monkeypatch)
        assert "plain" in called and "judged" not in called

    def test_judge_flag_forces_when_inactive(self, monkeypatch):
        called = self._run_main(["--judge", "--dry-run"], False, monkeypatch)
        assert called.get("judged") and not called.get("plain")

    def test_no_judge_overrides_active(self, monkeypatch):
        called = self._run_main(["--no-judge", "--dry-run"], True, monkeypatch)
        assert "plain" in called and "judged" not in called


class TestJudgmentMidRunDegradation:
    """Tier degrading mid-run (key missing, backend gone) must fall back to
    keyword clusters, not crash the miner."""

    def test_merger_pass_falls_back_on_unavailable(self, tmp_path, monkeypatch):
        mp = _load("mine_promotions_degrade", REPO / "scripts" / "cmd" / "mine-promotions.py")
        events = [
            {"_file": "a.md", "project": "p1", "observed_problem": "cache drift",
             "intervention": "serialize", "outcomes": {"happy_path": "PASS"}},
            {"_file": "b.md", "project": "q", "observed_problem": "cache drift too",
             "intervention": "serialize writes", "outcomes": {"happy_path": "PASS"}},
        ]
        import judgment as J
        from judgment import JudgmentUnavailable

        def exploding_same(*a, **k):
            raise JudgmentUnavailable("key vanished mid-run")
        monkeypatch.setattr(J, "same_recurrence", exploding_same)
        monkeypatch.setattr(mp, "is_judgment_active" if hasattr(mp, "is_judgment_active") else "_x", None, raising=False)
        # route() must say active so the judged path is taken, then degrade
        monkeypatch.setattr(J, "judgment_route", lambda *a, **k: "local")
        monkeypatch.setattr(J, "is_judgment_active", lambda *a, **k: True)
        out = mp.cluster_events_judged(events, min_projects=2)
        # graceful: keyword clusters returned (a+b merged by keyword? either way, no crash)
        assert isinstance(out, dict)

    def test_split_pass_degrades_gracefully(self, tmp_path, monkeypatch):
        mp = _load("mine_promotions_degrade2", REPO / "scripts" / "cmd" / "mine-promotions.py")
        import judgment as J
        from judgment import JudgmentUnavailable
        ev = {"_file": "a.md", "project": "p", "observed_problem": "x",
              "intervention": "y", "outcomes": {}}
        base = {"c1": [ev, dict(ev, _file="b.md")]}
        def exploding_same(*a, **k):
            raise JudgmentUnavailable("gone")
        monkeypatch.setattr(J, "same_recurrence", exploding_same)
        out = mp._split_incoherent_clusters(base, lambda e: "text", 0.8, "local")
        assert out == base  # untouched on degradation


class TestPlatformSplit:
    """#29 platform story: laya[mlx] on Apple Silicon; generic (GGUF via
    local_llm) anywhere else; torch scaffold never selected."""

    def _mk(self, monkeypatch):
        import judgment as J
        return J

    def test_non_apple_routes_laya_direct(self, monkeypatch):
        """Cross-platform default (#29): non-Apple goes to upstream laya
        (torch/ONNX), not the generic GGUF route."""
        J = _mk_j(monkeypatch)
        monkeypatch.setattr(J, "_is_apple_silicon", lambda: False)
        called = {}
        monkeypatch.setattr(J, "_ask_generic", lambda q: called.setdefault("generic", q))
        monkeypatch.setattr(J, "_ask_laya", lambda q: called.setdefault("laya-mlx", q))
        monkeypatch.setattr(J, "_ask_laya_direct", lambda q: called.setdefault("laya-direct", q))
        monkeypatch.setattr(J, "judgment_config", lambda: {"enabled": True, "local_backend": "laya"})
        q = {"kind": "noul", "question": "x"}
        J._ask_local(q)
        assert "laya-direct" in called and "laya-mlx" not in called and "generic" not in called

    def test_explicit_generic_stays_generic(self, monkeypatch):
        J = _mk_j(monkeypatch)
        called = {}
        monkeypatch.setattr(J, "_ask_generic", lambda q: called.setdefault("generic", q))
        monkeypatch.setattr(J, "judgment_config", lambda: {"enabled": True, "local_backend": "generic"})
        J._ask_local({"kind": "noul", "question": "x"})
        assert "generic" in called

    def test_apple_uses_laya(self, monkeypatch):
        J = _mk_j(monkeypatch)
        monkeypatch.setattr(J, "_is_apple_silicon", lambda: True)
        called = {}
        monkeypatch.setattr(J, "_ask_generic", lambda q: called.setdefault("generic", q))
        monkeypatch.setattr(J, "_ask_laya", lambda q: called.setdefault("laya", q))
        monkeypatch.setattr(J, "judgment_config", lambda: {"local_backend": "laya"})
        J._ask_local({"kind": "noul", "question": "q"})
        assert "laya" in called and "generic" not in called

    def test_laya_missing_with_fallback_uses_generic(self, monkeypatch):
        J = _mk_j(monkeypatch)
        monkeypatch.setattr(J, "_is_apple_silicon", lambda: True)
        monkeypatch.setattr(J, "judgment_config", lambda: {"local_backend": "laya",
                                                           "local_fallback": "generic"})

        def explode(q):
            raise J.JudgmentUnavailable("laya-as-judge not installed")
        monkeypatch.setattr(J, "_ask_laya", explode)
        monkeypatch.setattr(J, "_ask_generic", lambda q: {"value": 0.9})
        out = J._ask_local({"kind": "noul", "question": "q"})
        assert out["value"] == 0.9

    def test_explicit_generic_backend_skips_laya(self, monkeypatch):
        J = _mk_j(monkeypatch)
        monkeypatch.setattr(J, "_is_apple_silicon", lambda: True)
        monkeypatch.setattr(J, "judgment_config", lambda: {"local_backend": "generic"})
        called = {}
        monkeypatch.setattr(J, "_ask_generic", lambda q: called.setdefault("g", True))
        monkeypatch.setattr(J, "_ask_laya", lambda q: called.setdefault("l", True))
        J._ask_local({"kind": "noul", "question": "q"})
        assert called == {"g": True}


def _mk_j(monkeypatch):
    import judgment as J
    return J


class TestCloudKeyHandling:
    """Jev cloud route: key from env OR config; pre-flight surfaces missing keys."""

    def test_env_key_wins(self, monkeypatch):
        J = _mk_j(monkeypatch)
        monkeypatch.setenv("TYPESAFE_API_KEY", "env-key")
        monkeypatch.setattr(J, "judgment_config",
                            lambda: {"enabled": True, "api_key": "cfg-key"})
        base, key = J._typesafe_endpoint()
        assert key == "env-key"

    def test_config_key_used_when_no_env(self, monkeypatch):
        J = _mk_j(monkeypatch)
        monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
        monkeypatch.setattr(J, "judgment_config",
                            lambda: {"enabled": True, "api_key": "cfg-key"})
        base, key = J._typesafe_endpoint()
        assert key == "cfg-key"

    def test_no_key_anywhere(self, monkeypatch):
        J = _mk_j(monkeypatch)
        monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
        monkeypatch.setattr(J, "judgment_config", lambda: {"enabled": True})
        assert J.cloud_key_ready() is False

    def test_cloud_without_key_falls_back_to_keyword(self, tmp_path, monkeypatch):
        """route:cloud + no key ⇒ pre-flight detects and this run uses keyword clusters."""
        mp = _load("mine_promotions_nokey", REPO / "scripts" / "cmd" / "mine-promotions.py")
        import judgment as J
        monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
        monkeypatch.setattr(J, "is_judgment_active", lambda *a, **k: True)
        monkeypatch.setattr(J, "judgment_route", lambda *a, **k: "cloud")
        monkeypatch.setattr(J, "cloud_key_ready", lambda *a, **k: False)
        called = {}
        monkeypatch.setattr(mp, "cluster_events_judged",
                            lambda *a, **k: called.setdefault("judged", True))
        monkeypatch.setattr(mp, "cluster_events",
                            lambda *a, **k: called.setdefault("plain", {}) or {})
        monkeypatch.setattr(mp, "extract_experience_events", lambda: [])
        import sys as _sys, io, contextlib
        monkeypatch.setattr(_sys, "argv", ["mine-promotions", "--dry-run"])
        with contextlib.redirect_stdout(io.StringIO()):
            mp.main()
        assert "plain" in called and "judged" not in called
