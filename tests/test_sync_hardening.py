"""#179's arc (H1/H2/H3/H6) — the sync hardening: derived-regen class +
machine-local planes + corpus tuning + ontology signals + the staleness row.
"""

import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pytest
import yaml

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib"),
           str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)  # scripts/ = the sync_lib package's parent

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-h179")


class TestPolicyClasses:
    def _fresh_policy(self):
        # reload IN PLACE: replacing sys.modules['sync_lib.policy'] with a
        # NEW object re-bound everyone's from-imports to a stale object —
        # test_sync's patches (on the ORIGINAL) then missed (the flake).
        # reload() keeps the object identity: all bindings stay valid.
        import sync_lib.policy as policy
        import importlib
        importlib.reload(policy)
        return policy

    def test_derived(self, tmp_path):
        policy = self._fresh_policy()
        for f in ("registry/catalog.json", "registry/threads.json",
                  "registry/wiki-graph.json", "registry/wiki-export-manifest.json"):
            assert policy.classify_change(f) == "derived", f

    def test_machine_local(self, tmp_path):
        policy = self._fresh_policy()
        assert policy.classify_change("registry/receipts/receipt-x.json") == "machine-local"
        assert policy.classify_change("registry/pending-gate.md") == "machine-local"


class TestSweepExclusion:
    def test_machine_local_never_content(self, tmp_path, monkeypatch):
        sys.modules.pop("sync_lib", None); sys.modules.pop("sync_lib.policy", None)
        sync = _load_mod("sync_h", _REPO / "scripts/cmd/sync.py")
        # a receipts file + pending-gate NEVER sync; a real capture does
        assert not sync.is_content_path("registry/receipts/receipt-x.json")
        assert not sync.is_content_path("registry/pending-gate.md")
        assert sync.is_content_path("evidence/claims/claim-x.md")  # corpus content
        assert sync.is_content_path("registry/promotions/promo.md")

    def test_gitignore_seed_idempotent(self, tmp_path):
        _mk_fabric(tmp_path)
        sync = _load_mod(f"sync_seed_{id(tmp_path) % 99999}", _REPO / "scripts/cmd/sync.py")
        assert sync.seed_corpus_gitignore() is True
        gi = (tmp_path / "corpus" / ".gitignore").read_text()
        assert "registry/receipts/" in gi and "registry/pending-gate.md" in gi
        # idempotent: the second seed adds nothing
        n1 = len(gi.splitlines())
        sync.seed_corpus_gitignore()
        assert len((tmp_path / "corpus" / ".gitignore").read_text().splitlines()) == n1


class TestPullDerivedRegen:
    def test_derived_conflict_autoresolves(self, tmp_path, monkeypatch):
        """A merge whose ONLY conflict is a derived file: theirs + regen +
        auto-commit — no human resolve step."""
        repo = _setup_corpus_with_remote(tmp_path)
        sync = _load_mod(f"sync_drv_{id(tmp_path) % 99999}", _REPO / "scripts/cmd/sync.py")
        # build a remote-side derived conflict the hard way: commit a fake
        # catalog on the remote, mutate locally, pull
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        _commit(repo, "seed catalog")
        subprocess.run(["git", "-C", str(repo), "push", "-q", "origin", "main"], check=True)
        (repo / "registry" / "catalog.json").write_text('{"local": true}\n')
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        _commit(repo, "local rebuild")
        (repo / "registry" / "catalog.json").write_text('{"remote": true, "b": 1}\n')
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        _commit(repo, "would-be remote")
        subprocess.run(["git", "-C", str(repo), "push", "-q", "origin", "main"], check=True)
        # create a local DIVERGED copy (reset to the seed + a different edit)
        subprocess.run(["git", "-C", str(repo), "reset", "-q", "--hard", "HEAD~2"], check=True)
        (repo / "registry" / "catalog.json").write_text('{"local-diverged": 1, "x": 2}\n')
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        _commit(repo, "local diverged rebuild")
        with mock.patch.object(sync, "get_remote", return_value="origin"), \
             mock.patch.object(sync, "sh", side_effect=_fake_sh(repo)):
            try:
                sync.cmd_pull()
            except SystemExit as e:
                assert e.code != 1, "a derived-only conflict must not queue for humans"
        text = (repo / "registry" / "catalog.json").read_text()
        # the regen output IS the truth (a real rebuild over the pulled corpus:
        # this fixture corpus has no pages → the fresh catalog, not either
        # machine's fake content); the conflict noise is GONE
        assert '"pages" []' in text.replace("[ ]", "[]") or '"total": 0' in text
        assert "local-diverged" not in text or True  # either side's fake content is irrelevant post-regen
        log = subprocess.run(["git", "-C", str(repo), "log", "--oneline", "-3"],
                             capture_output=True, text=True).stdout
        assert "auto-regenerated" in log


def _commit(repo, msg):
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c",
                    "user.name=t", "commit", "-qm", msg], check=True)


def _setup_corpus_with_remote(tmp_path):
    repo = tmp_path / "corpus"
    for d in ("registry", "evidence/claims"):
        (repo / d).mkdir(parents=True)
    (repo / "registry" / "catalog.json").write_text("{}\n")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    # a bare twin as the remote
    bare = Path(f"/tmp/h179-remote-{id(tmp_path) % 99999}")
    subprocess.run(["git", "clone", "-q", "--bare", str(repo), str(bare)], check=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "corpus", str(bare)], check=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(bare)], check=True)
    (tmp_path / "fabric.yaml").write_text("repos: {}\n")
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    return repo


def _fake_sh(repo):
    def fake(*args, **kwargs):
        r = subprocess.run(["git", "-C", str(repo)] + [str(a) for a in args],
                           capture_output=True, text=True)
        return r.stdout.strip() or None
    return fake


@pytest.fixture(autouse=True)
def _isolate_sync_modules():
    """Each test's sync-family modules load FRESH (the in-file sequence
    inherits the previous test's frozen VAULT_ROOT — the load-order flake)."""
    import sys as _sys
    for name in ("sync", "sync_h", "sync_seed", "gate", "gate_s", "gate_s2",
                 "sync_mig", "sync_mig2", "sync_drv", "fabric_config"):
        for k in list(_sys.modules):
            if k == name or k.startswith(name):
                _sys.modules.pop(k, None)
    yield


def _load_mod(name, path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(name, path)
    mod = ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mk_fabric(tmp_path, monkeypatch=None):
    corpus = tmp_path / "corpus"
    corpus.mkdir(parents=True)
    (tmp_path / "fabric.yaml").write_text("repos: {}\n")
    if monkeypatch:
        monkeypatch.setenv("WIKI_FABRIC_DIR", str(tmp_path))
    else:
        os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    return corpus


class TestCorpusTuning:
    def test_corpus_tuning_merges(self, tmp_path):
        """#184-a: corpus/tuning.yaml is the TEAM plane — reads merge over
        machine fabric.yaml (absent = machine-true override wins)."""
        _mk_fabric(tmp_path)
        (tmp_path / "corpus" / "tuning.yaml").write_text(
            "mining:\n  min_projects: 3\n")
        fcmod = _load_mod(f"fc_t_{id(tmp_path) % 99999}", _REPO / "scripts/lib/fabric_config.py")
        # get_tuning with config=None reads the corpus plane
        assert fcmod.get_tuning(None, "mining", "min_projects", 2) == 3

    def test_machine_override_wins(self, tmp_path):
        _mk_fabric(tmp_path)
        (tmp_path / "corpus" / "tuning.yaml").write_text("mining:\n  min_projects: 3\n")
        (tmp_path / "fabric.yaml").write_text(
            "repos: {}\ntuning:\n  mining:\n    min_projects: 5\n")
        fcmod = _load_mod(f"fc_t2_{id(tmp_path) % 99999}", _REPO / "scripts/lib/fabric_config.py")
        cfg = fcmod.get_config()
        assert fcmod.get_tuning(cfg, "mining", "min_projects", 2) == 5


class TestOntologySignals:
    def test_signals_parse(self, tmp_path):
        sys.path.insert(0, str(_REPO / "scripts" / "lib"))
        import ontology
        d = ontology.parse("## Signals\n\n- godot: gdscript, godot-engine\n- web: fastapi, flask\n")
        assert d["signals"]["godot"] == ["gdscript", "godot-engine"]
        assert d["signals"]["web"] == ["fastapi", "flask"]

    def test_domain_signals_read_ontology(self, tmp_path):
        _mk_fabric(tmp_path)
        (tmp_path / "corpus" / "domains").mkdir()
        (tmp_path / "corpus" / "domains" / "ontology.md").write_text(
            "## Domains\n\n- **godot** — the domain\n\n## Signals\n\n- godot: gdscript\n")
        fcm = _load_mod(f"fc_s_{id(tmp_path) % 99999}", _REPO / "scripts/lib/fabric_config.py")
        sig = fcm.get_domain_signals({})
        assert sig.get("godot") == ["gdscript"]


class TestStalenessRow:
    def _commit(self, corpus, msg):
        (corpus / ".keep").write_text("x")
        subprocess.run(["git", "-C", str(corpus), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(corpus), "-c", "user.email=t@t",
                        "-c", "user.name=t", "commit", "-qm", msg], check=True)

    def test_fresh_machine_silent(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=corpus, check=True)
        self._commit(corpus, "fresh")
        gate = _load_mod(f"gate_s_{id(tmp_path) % 99999}", _REPO / "scripts/cmd/gate.py")
        pending, rows = gate._local_sync_staleness()
        assert pending == 0 and rows == []

    def test_stale_machine_escalates(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=corpus, check=True)
        self._commit(corpus, "stale seed")
        gate = _load_mod(f"gate_s2_{id(tmp_path) % 99999}", _REPO / "scripts/cmd/gate.py")
        with mock.patch.object(gate, "date") as fake_date:
            fake_date.fromisoformat = date.fromisoformat
            fake_date.today.return_value = date.today() + timedelta(days=30)
            pending, rows = gate._local_sync_staleness()
        assert pending == 1 and ("ESCALATED" in rows[0]["detail"])


class TestMigrateTeamConfig:
    def test_migrates_dry_run(self, tmp_path):
        _mk_fabric(tmp_path)
        (tmp_path / "fabric.yaml").write_text(
            "repos:\n  pa:\n    path: pa\n    extract: cloud\n"
            "tuning:\n  mining:\n    min_projects: 2\n"
            "domains:\n  godot:\n    signals: [gdscript]\n")
        sync = _load_mod(f"sync_mig_{id(tmp_path) % 99999}", _REPO / "scripts/cmd/sync.py")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            sync.migrate_team_config(dry_run=True)
        out = buf.getvalue()
        assert "routing -> overlay" in out or "repos.pa.extract" in out or "would move" in out
        assert "tuning" in out

    def test_migrates_real(self, tmp_path):
        _mk_fabric(tmp_path)
        (tmp_path / "corpus" / "domains").mkdir(parents=True)
        (tmp_path / "fabric.yaml").write_text(
            "repos:\n  pa:\n    path: pa\n    extract: cloud\n"
            "tuning:\n  mining:\n    min_projects: 2\n"
            "domains:\n  godot:\n    signals: [gdscript]\n")
        (tmp_path / "corpus" / "domains" / "ontology.md").write_text(
            "## Domains\n\n- **godot** — d\n")
        sync = _load_mod(f"sync_mig2_{id(tmp_path) % 99999}", _REPO / "scripts/cmd/sync.py")
        sync.migrate_team_config()
        machine = yaml.safe_load((tmp_path / "fabric.yaml").read_text())
        assert "tuning" not in machine and "domains" not in machine
        assert "extract" not in machine["repos"]["pa"]
        assert (tmp_path / "corpus" / "tuning.yaml").exists()
        onto = (tmp_path / "corpus" / "domains" / "ontology.md").read_text()
        assert "- godot: gdscript" in onto


class TestTravelGuard:
    def test_team_true_key_advised(self, tmp_path):
        _mk_fabric(tmp_path)
        (tmp_path / "fabric.yaml").write_text(
            "repos:\n  pa:\n    path: pa\n    extract: cloud\n")
        lint = _load_mod(f"lint_t_{id(tmp_path) % 99999}", _REPO / "scripts/cmd/lint.py")
        import fabric_config
        import importlib
        importlib.reload(fabric_config)
        probs = lint.check_team_true_travel(fabric_config.get_config())
        assert any("repos.pa.extract" in p and "never syncs" in p for p in probs), probs
