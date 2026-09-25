"""Unit tests for the judgment-tier refinements (#29 slices 2+3).

All judgment calls are mocked — CI never contacts a backend. Live behavior
is exercised only when a human enables integrations.judgment with a key.

Run: python3 -m pytest tests/test_judgment_refinement.py -v
"""

import contextlib
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
    same module object, so module-level patches reach them."""
    if unavailable:
        with mock.patch.object(judgment, "judgment_route",
                               side_effect=judgment.JudgmentUnavailable("disabled")):
            yield
    else:
        if answers is not None:
            def fake_noul(q, s):
                return answers.pop(0) if answers else prob
            with mock.patch.object(judgment, "judgment_route", return_value="cloud"), \
                 mock.patch.object(judgment, "noul", side_effect=fake_noul):
                yield
        else:
            with mock.patch.object(judgment, "judgment_route", return_value="cloud"), \
                 mock.patch.object(judgment, "noul", return_value=prob):
                yield


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
            if unavailable:
                with mock.patch.object(judgment, "judgment_route",
                                       side_effect=judgment.JudgmentUnavailable("disabled")):
                    yield
            else:
                def fake_noul(q, s):
                    capture.append(q)
                    return prob
                with mock.patch.object(judgment, "judgment_route", return_value="cloud"), \
                     mock.patch.object(judgment, "noul", side_effect=fake_noul):
                    yield

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
            def fake_noul(q, s):
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

    def test_judged_different_keeps_clusters_split(self):
        with judged(prob=0.05):
            clusters = mine.cluster_events_judged(self._events(), min_projects=2)
        kw = mine.cluster_events_keyword(self._events(), min_projects=2)
        assert clusters == kw

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
