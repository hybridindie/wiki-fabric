"""#172 — the scheduled chat-mining cadence: scaffold (workflow yml written
on sync init/setup, opt-in var), template shape (gated, heuristic-only,
never auto-promotes — promote-patterns --auto is a HUMAN command surface,
never a CI verb, #190), and the idempotence contract (never overwrites).
"""

import sys
from pathlib import Path
import yaml

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os_env = None  # placeholder (module-level import hygiene)
import os as _os
_os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-mining")


def _load_sync(name):
    """sync.py freezes VAULT_ROOT at import — env (set by _mk_fabric) must
    land before the module loads."""
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(name, _REPO / "scripts/cmd/sync.py")
    sync = ilu.module_from_spec(spec)
    sys.modules[name] = sync
    spec.loader.exec_module(sync)
    return sync


def _mk_fabric(tmp_path):
    corpus = tmp_path / "corpus"
    (corpus / "evidence").mkdir(parents=True)
    (tmp_path / "fabric.yaml").write_text("repos: {}\n")
    _os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    import fabric_config
    import importlib
    importlib.reload(fabric_config)
    return corpus


class TestScaffold:
    def test_init_scaffolds_mining(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        sync = _load_sync("sync_init_t")
        assert sync.scaffold_mining_workflow() is True
        wf = corpus / ".github" / "workflows" / "mining.yml"
        assert wf.exists()

    def test_never_overwrites(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        wf_dir = corpus / ".github" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)
        (wf_dir / "mining.yml").write_text("# custom human workflow\n")
        sync = _load_sync("sync_overwrite_t")
        assert sync.scaffold_mining_workflow() is False
        assert (wf_dir / "mining.yml").read_text() == "# custom human workflow\n"


class TestTemplateShape:
    """The workflow's CONTRACTS, parsed from the shipped template (not a
    copy in the test): gated, heuristic-only, non-promoting, idempotent."""

    def _template(self):
        return yaml.safe_load((_REPO / "system" / "corpus" /
                               "mining-workflow.yml").read_text())

    def test_valid_yaml_single_job(self):
        d = self._template()
        assert "jobs" in d and list(d["jobs"]) == ["mine"]

    def test_gated_on_optin_var(self):
        d = self._template()
        cond = d["jobs"]["mine"]["if"]
        assert "WIKI_FABRIC_MINING" in cond and "'1'" in cond

    def test_heuristic_only_no_llm_flag(self):
        d = self._template()
        run = str(d["jobs"]["mine"]["steps"])
        assert "--llm" not in run  # CI stays 0-token
        assert "--propose" in run  # staged candidates are the point
        assert "--dry-run" not in run  # the cadence WRITES (inbox drift commits)

    def test_no_promote_verb_in_pipeline(self):
        d = self._template()
        run = str(d["jobs"]["mine"]["steps"])
        # 'promote' appears only in HUMAN-review notices, never as an
        # executed verb. #190: the judged auto-apply tier is a HUMAN command
        # (promote-patterns --auto) — the CI pipeline stays promotion-free.
        assert "promote-patterns --auto" not in run
        assert "--unapply" not in run
        assert "run: wf promote" not in run

    def test_weekly_cron(self):
        d = self._template()
        assert d[True]["schedule"][0]["cron"] if False else \
            d["on"]["schedule"][0]["cron"].endswith("* * 1")  # Mondays

    def test_commit_planes_cover_inbox(self):
        d = self._template()
        run = str(d["jobs"]["mine"]["steps"])
        assert "patterns/_inbox/" in run  # the candidate plane is what commits
        assert "evidence/insights/" in run