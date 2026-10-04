"""#178 — the multi-project rules layer: A0 harvest (rule files → gated
candidates), twin-merge (G-J guarded), B export (paths-derived), the parity
guard, promotion retiring the hand file.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-rules")


def _load_mod(name, path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mk_fabric(tmp_path, repos=("pa", "pb")):
    corpus = tmp_path / "corpus"
    (corpus / "patterns" / "_inbox").mkdir(parents=True)
    for r in repos:
        repo = tmp_path / r
        (repo / ".claude" / "rules").mkdir(parents=True)
    (tmp_path / "fabric.yaml").write_text(
        "repos:\n" + "".join(f"  {r}:\n    path: {r}\n" for r in repos))
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    sys.modules.pop("fabric_config", None)
    import fabric_config
    import importlib
    importlib.reload(fabric_config)
    return corpus


def _promote_one(corpus, pid="pattern-rule-abc", body="the rule body", project=None, includes=None):
    p = corpus / "patterns" / f"{pid}.md"
    app = f"applicability:\n  includes:\n" + "".join(f'  - "{i}"\n' for i in (includes or []))
    p.write_text(f"""---
type: pattern
id: {pid}
title: "The rule"
status: recommended
project: {project or ""}
{app}---

# The rule

{body}
""")
    return p


def _rule(repo, name, title, bullets, paths=None):
    fm = ""
    if paths is not None:
        fm = "---\npaths:\n" + "".join(f'  - "{p}"\n' for p in paths) + "---\n"
    body = fm + f"\n# {title}\n\n" + "\n".join(f"{i+1}. {b}" for i, b in enumerate(bullets)) + "\n"
    p = repo / ".claude" / "rules" / name
    p.write_text(body)
    return p


class TestHarvest:
    def test_stages_candidates(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        _rule(tmp_path / "pa", "testing.md", "Testing: TDD Mandate",
              ["tests written failing-first", "preflight runs the whole suite"])
        rules = _load_mod("rules_h", _REPO / "scripts/cmd/rules.py")
        staged, merged, skipped = rules.harvest("pa")
        assert (staged, merged, skipped) == (1, 0, 0)
        cand = next(iter((corpus / "patterns" / "_inbox").glob("pattern-rule-*.md")))
        text = cand.read_text()
        assert "origin: rules-file" in text
        assert "tests written failing-first" in text  # the rule body carried

    def test_idempotent(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        _rule(tmp_path / "pa", "testing.md", "Testing: TDD Mandate",
              ["tests written failing-first"])
        rules = _load_mod("rules_h2", _REPO / "scripts/cmd/rules.py")
        assert rules.harvest("pa")[:2] == (1, 0)
        assert rules.harvest("pa") == (0, 0, 1)  # already staged

    def test_paths_carried_as_locator(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        _rule(tmp_path / "pa", "api.md", "API contract", ["pydantic only"],
              paths=["src/api/**/*.py"])
        rules = _load_mod("rules_h3", _REPO / "scripts/cmd/rules.py")
        rules.harvest("pa")
        cand = next(iter((corpus / "patterns" / "_inbox").glob("pattern-rule-*.md")))
        assert "paths: src/api/**/*.py" in cand.read_text()

    def test_dry_run(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        _rule(tmp_path / "pa", "t.md", "T rules", ["one"])
        rules = _load_mod("rules_h4", _REPO / "scripts/cmd/rules.py")
        assert rules.harvest("pa", dry_run=True)[:2] == (1, 0)
        assert list((corpus / "patterns" / "_inbox").glob("*.md")) == []

    def test_twin_merge_judged_same(self, tmp_path):
        """pa's rule and pb's SAME-TOPIC twin → ONE candidate (provenance
        +1 repo, divergence recorded)."""
        corpus = _mk_fabric(tmp_path)
        _rule(tmp_path / "pa", "workflow.md", "Workflow pipeline (canonical)",
              ["changes delivered by the pipeline", "no direct pushes to main"])
        _rule(tmp_path / "pb", "workflow.md", "Workflow pipeline rules",
              ["changes flow through the delivery pipeline", "pushes to main are direct and forbidden"])
        rules = _load_mod("rules_h5", _REPO / "scripts/cmd/rules.py")
        with mock.patch("judgment.judgment_eval_recorded", return_value=(True, "ok")), \
             mock.patch("judgment.same_recurrence", return_value=(True, 0.92)) as sr:
            staged, merged, _s = rules.harvest("pa")
            s2, m2, k2 = rules.harvest("pb")
        assert staged == 1 and m2 == 1 and staged and s2 == 0
        assert (staged, m2) == (1, 1)
        cand = next(iter((corpus / "patterns" / "_inbox").glob("pattern-rule-*.md")))
        text = cand.read_text()
        assert "Merged twin" in text or "Merged (judged)" in text
        # the twin merge recorded the judged probability + the source repo
        assert "judged p=0.92" in text

    def test_twin_judged_different_stages_separately(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        _rule(tmp_path / "pa", "workflow.md", "Workflow pipeline (canonical)",
              ["changes delivered by the pipeline", "no direct pushes to main"])
        _rule(tmp_path / "pb", "deploy.md", "Deployment cadence",
              ["canary deploys weekly to staging"])
        rules = _load_mod("rules_h6", _REPO / "scripts/cmd/rules.py")
        with mock.patch("judgment.judgment_eval_recorded", return_value=(True, "ok")):
            # first call = same (0.92) for pa's own harvest (no twins yet);
            # second = different for pb's deploy rule
            with mock.patch("judgment.same_recurrence",
                            side_effect=[(True, 0.92), (False, 0.2)]):
                rules.harvest("pa")
                staged2, _, _ = rules.harvest("pb")
        assert staged2 == 1  # staged separately (no twin merge)
        cands = sorted((corpus / "patterns" / "_inbox").glob("pattern-rule-*.md"))
        assert len(cands) == 2

    def test_gj_refused_no_merge(self, tmp_path):
        """G-J: uncalibrated judge → twins NEVER silent-merge (stage apart)."""
        corpus = _mk_fabric(tmp_path)
        _rule(tmp_path / "pa", "workflow.md", "Workflow pipeline (canonical)", ["the pipeline delivers"])
        _rule(tmp_path / "pb", "workflow.md", "Workflow pipeline rules", ["the pipeline delivers changes"])
        rules = _load_mod("rules_h7", _REPO / "scripts/cmd/rules.py")
        with mock.patch("judgment.judgment_eval_recorded",
                        return_value=(False, "no PASS receipt")):
            rules.harvest("pa")
            r2 = rules.harvest("pb")
        assert r2[0] == 1 and r2[1] == 0  # staged separately, no judged merge
        assert len(list((corpus / "patterns" / "_inbox").glob("pattern-rule-*.md"))) == 2


class TestExport:

    def test_renders_recommended_with_paths(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        _promote_one(corpus, includes=["src/api/**/*.py"])
        repo = tmp_path / "pa" / ".claude" / "rules"
        (repo / "wiki-fabric").mkdir(parents=True)
        rules = _load_mod("rules_e", _REPO / "scripts/cmd/rules.py")
        written, _ = rules.export_rules("pa")
        assert written == 1
        out = sorted((repo / "wiki-fabric").glob("*.md"))[0]
        text = out.read_text()
        assert 'paths:\n  - "src/api/**/*.py"' in text
        assert "wiki-fabric managed" in text

    def test_candidates_never_render(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        _promote_one(corpus, body="x")
        # change its status to candidate
        p = next(corpus.glob("patterns/pattern-rule-*.md"))
        p.write_text(p.read_text().replace("status: recommended", "status: candidate"))
        rules = _load_mod("rules_e2", _REPO / "scripts/cmd/rules.py")
        written, _ = rules.export_rules("pa")
        assert written == 0  # candidates stay pull-only

    def test_declined_pattern_skipped(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        p = _promote_one(corpus, pid="pattern-rule-dec", body="x")
        (tmp_path / "fabric.yaml").write_text(
            "repos:\n  pa:\n    path: pa\n    rules:\n"
            "      pattern-rule-dec: declined\n")
        sys.modules.pop("fabric_config", None)
        import fabric_config, importlib
        importlib.reload(fabric_config)
        rules = _load_mod("rules_e3", _REPO / "scripts/cmd/rules.py")
        written, _ = rules.export_rules("pa")
        assert written == 0

    def test_idempotent_render(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        _promote_one(corpus, body="stable body")
        rules = _load_mod("rules_e4", _REPO / "scripts/cmd/rules.py")
        assert rules.export_rules("pa")[0] == 1
        assert rules.export_rules("pa") == (0, 1)  # unchanged skip


class TestPromotionRetires:
    def test_rules_harvest_apply_retires_source(self, tmp_path):
        corpus = _mk_fabric(tmp_path, ("pa",))
        rule = _rule(tmp_path / "pa", "testing.md", "Testing: TDD Mandate",
                     ["tests written failing-first"])
        # harvest + apply via promote-patterns
        rules = _load_mod("rules_pr", _REPO / "scripts/cmd/rules.py")
        rules.harvest("pa")
        cand = next(iter((corpus / "patterns" / "_inbox").glob("pattern-rule-*.md")))
        pp = _load_mod("promote_patterns_pr", _REPO / "scripts/cmd/promote-patterns.py")
        assert pp.apply_candidate(cand) is True
        text = rule.read_text()
        assert "RETIRED" in text and "corpus" in text  # the tombstone pointer
        # and the canonical pattern exists
        assert next(corpus.glob("patterns/pattern-rule-*.md")).exists()


class TestParityGuard:
    def test_handedit_detected_subprocess_isolated(self, tmp_path):
        """The parity guard in FULL isolation (subprocess): the module-state
        flake (module-resolution under shared sys.modules with other files'
        fixtures) kept flipping this test captured-vs-not — isolation is the
        deterministic contract; the FLAKE ITSELF is recorded in the report."""
        corpus = _mk_fabric(tmp_path, ("pa",))
        _promote_one(corpus, body="stable")
        repo = tmp_path / "pa"
        rules = _load_mod("rules_pg", _REPO / "scripts/cmd/rules.py")
        rules.export_rules("pa")
        managed = repo / ".claude" / "rules" / "wiki-fabric" / "pattern-rule-abc.md"
        managed.write_text(managed.read_text() + "\nHAND EDIT\n")
        # hand-run the parity check in a FRESH interpreter bound to THIS fabric
        r = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r); "
             "import lint; print(repr(lint.check_rules_parity(None)))"
             % (str(_REPO / "scripts/cmd"), str(_REPO / "scripts/lib"))],
            capture_output=True, text=True,
            env={**os.environ, "WIKI_FABRIC_DIR": str(tmp_path)}, cwd=str(tmp_path))
        assert "HAND-EDITED" in r.stdout and "RULES-PARITY pa" in r.stdout, r.stdout + r.stderr
