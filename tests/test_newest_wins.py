"""#175 — newest-wins contradiction sweep: mechanically demote claims a
strictly-newer supported claim contradicts; restore when the contradictor
loses support; idempotent re-runs; hand relations + effects verdicts as
carriers.
"""

import os
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-newestwins")


def _seed_pair(corpus, old_date, new_date, older_st="supported"):
    _claim(corpus, "claim-old-a", '"old phrasing of the rule"',
           generated_at=f"{old_date}T00:00:00Z", status=older_st)
    _claim(corpus, "claim-new-b", '"new phrasing that contradicts"',
           generated_at=f"{new_date}T00:00:00Z")
    fx = corpus / "registry" / "effects" / "claim-new-b.effects.json"
    fx.write_text(f'''{{
 "claim": "claim-new-b",
 "judged_effects": {{"claim-old-a": "contradicts"}},
 "route": "test"
}}''')


def _mk_fabric(tmp_path):
    corpus = tmp_path / "corpus"
    for d in ("evidence/claims", "registry/effects"):
        (corpus / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "fabric.yaml").write_text("repos: {}\n")
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    import fabric_config
    import importlib
    importlib.reload(fabric_config)
    return corpus


def _rv(tmp_path):
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(f"rv_{id(tmp_path) % 99999}",
                                       _REPO / "scripts" / "cmd" / "review.py")
    rv = ilu.module_from_spec(spec)
    sys.modules[f"rv_{id(tmp_path) % 99999}"] = rv
    spec.loader.exec_module(rv)
    return rv


def _claim(corpus, stem, statement, captured=None, generated_at=None, status="supported"):
    p = corpus / "evidence" / "claims" / f"{stem}.md"
    gen = generated_at or (f"{captured}T12:00:00Z" if captured else None)
    gen_block = f'generated: {{ by: "test", at: "{gen}" }}' if gen else ""
    p.write_text(f"""---
type: claim
id: {stem}
statement: {statement}
resource: "[[src-x]]"
{gen_block}
status: {status}
last_verified: {date.today().isoformat()}
relations: []
---

# t

""")
    return p


class TestNewestWinsDemotion:
    """Older claim demoted when a strictly-newer supported claim contradicts
    it (the effects-verdict carrier — verify-effects' judged_effects map)."""


    def test_demotes_older(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        demoted, restored, detail = rv.contradiction_sweep()
        assert demoted == 1 and restored == 0
        s = (corpus / "evidence" / "claims" / "claim-old-a.md").read_text()
        assert "status: contested" in s
        assert "contradicted-by:" in s and "claim-new-b" in s
        assert "stale_after:" in s

    def test_newer_claim_never_demoted(self, tmp_path):
        """Direction-free pairs normalize by DATE: the newer side is the
        contradictor — the effects file names it as demotee (new claim's
        perspective), the date logic still demotes the OLD one."""
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        rv.contradiction_sweep()
        s = (corpus / "evidence" / "claims" / "claim-new-b.md").read_text()
        assert "status: supported" in s  # the newest survives

    def test_equal_clocks_skip(self, tmp_path):
        """Same-batch extraction (identical generated.at) never demotes —
        the human pool review owns intra-batch reads (spike finding)."""
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-01")
        rv = _rv(tmp_path)
        demoted, _, detail = rv.contradiction_sweep()
        assert demoted == 0 and "clocks unknown or equal" in detail[0]

    def test_idempotent_rerun(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        assert rv.contradiction_sweep()[:2] == (1, 0)
        assert rv.contradiction_sweep()[:2] == (0, 0)  # already demoted

    def test_dry_run_touches_nothing(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        demoted, _, detail = rv.contradiction_sweep(dry_run=True)
        assert demoted == 1 and "[dry] DEMOTE" in detail[0]
        assert "status: supported" in (corpus / "evidence" / "claims" / "claim-old-a.md").read_text()

    def test_relation_carrier(self, tmp_path):
        """Hand-declared type: contradicts relations blocks feed the sweep."""
        corpus = _mk_fabric(tmp_path)
        old = _claim(corpus, "claim-rel-old", '"the old claim"', generated_at="2026-09-01T00:00:00Z")
        _claim(corpus, "claim-rel-new", '"the new contradictor"', generated_at="2026-09-20T00:00:00Z")
        s = old.read_text()
        old.write_text(s.replace("relations: []",
                                 'relations:\n  - type: contradicts\n    target: "[[claim-rel-new]]"'))
        rv = _rv(tmp_path)
        demoted, _, _ = rv.contradiction_sweep()
        assert demoted == 1
        # normalization: the OLD claim declared a contradicts toward the NEWER
        # one — the date logic still demotes the older side
        assert "status: contested" in old.read_text()

    def test_only_live_claims_demoted(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        _claim(corpus, "claim-sup-old", '"superseded already"', generated_at="2026-09-01T00:00:00Z", status="superseded")
        _claim(corpus, "claim-sup-new", '"the contradictor"', generated_at="2026-09-15T00:00:00Z")
        fx = corpus / "registry" / "effects" / "claim-sup-new.effects.json"
        fx.write_text('{"claim": "claim-sup-new", "judged_effects": {"claim-sup-old": "contradicts"}, "route": "t"}')
        rv = _rv(tmp_path)
        assert rv.contradiction_sweep()[:2] == (0, 0)


class TestRestore:
    def test_restore_when_contradictor_loses_support(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        assert rv.contradiction_sweep()[:2] == (1, 0)
        # contradictor becomes contested (e.g. its own drift)
        con = corpus / "evidence" / "claims" / "claim-new-b.md"
        con.write_text(con.read_text().replace("status: supported", "status: contested"))
        demoted, restored, detail = rv.contradiction_sweep()
        assert restored == 1 and "RESTORE" in detail[0]
        s = (corpus / "evidence" / "claims" / "claim-old-a.md").read_text()
        assert "status: supported" in s
        assert "contradicted-by:" not in s
        assert "stale_after:" not in s

    def test_restore_dry_run(self, tmp_path):
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        rv.contradiction_sweep()
        con = corpus / "evidence" / "claims" / "claim-new-b.md"
        con.write_text(con.read_text().replace("status: supported", "status: contested"))
        demoted, restored, detail = rv.contradiction_sweep(dry_run=True)
        assert restored == 1
        assert "status: contested" in (corpus / "evidence" / "claims" / "claim-old-a.md").read_text()


class TestCliFlags:
    def test_demoted_listing(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        rv.contradiction_sweep()
        import io
        import contextlib
        with mock.patch.object(sys, "argv", ["review.py", "--demoted"]):
            try:
                rc = rv.main()
            except SystemExit:
                rc = 0
        out = capsys.readouterr().out
        assert "claim-old-a.md" in out and "1 contradiction-demoted" in out

    def test_restore_flag(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        rv.contradiction_sweep()
        with mock.patch.object(sys, "argv", ["review.py", "--restore-demoted", "claim-old-a"]):
            try:
                rc = rv.main()
            except SystemExit:
                rc = 0
        out = capsys.readouterr().out
        assert "restored" in out
        assert "status: supported" in (corpus / "evidence" / "claims" / "claim-old-a.md").read_text()

    def test_sweep_json(self, tmp_path, capsys):
        corpus = _mk_fabric(tmp_path)
        _seed_pair(corpus, "2026-09-01", "2026-09-15")
        rv = _rv(tmp_path)
        with mock.patch.object(sys, "argv", ["review.py", "--contradiction-sweep", "--dry-run", "--json"]):
            try:
                rc = rv.main()
            except SystemExit:
                rc = 0
        import json as _json
        cap = capsys.readouterr()
        dec = _json.JSONDecoder()
        best = None
        for i, ch in enumerate(cap.out):
            if ch == "{":
                try:
                    obj, end = dec.raw_decode(cap.out[i:])
                    cand = cap.out[i:i + end]
                    if best is None or len(cand) > len(best):
                        best = cand
                except _json.JSONDecodeError:
                    continue
        d = _json.loads(best)
        assert d["demoted"] >= 1