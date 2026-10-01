"""Canonical project-slug seam (wf_common.project_slug) + join-fix regressions.

Background: project names flow in two forms — underscore repo-dir names
(comfyui_mcp, from overlay namespace / fabric.yaml repos keys) and kebab
(wf_common.slugify). Claim file slugs are ALWAYS kebab (ingest slugifies the
raw rel path). Producers/consumers that glob claim-{project} or key wiki
nodes on the raw form used to fork: the wiki grew both comfyui_mcp/ and
comfyui-mcp/ deep-dive trees from different graph revs.

Run: python3 -m pytest tests/test_slug_canon.py -v
"""

import sys
import importlib.util
from pathlib import Path

import pytest

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "harness", ""):
    _d = _SCRIPTS / _rel if _rel else _SCRIPTS
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from wf_common import slugify, project_slug, claim_prefix_for_project
import layout


class TestProjectSlug:
    def test_underscore_folds_to_kebab(self):
        assert project_slug("comfyui_mcp") == "comfyui-mcp"

    def test_idempotent(self):
        assert project_slug("comfyui-mcp") == "comfyui-mcp"
        assert project_slug("godot-agents") == "godot-agents"
        assert project_slug("wiki-fabric") == "wiki-fabric"

    def test_matches_slugify_for_clean_names(self):
        for n in ("alpaca-agents", "aperiodic", "Godot Agents", "my_repo2"):
            assert project_slug(n) == slugify(n)

    def test_empty_safe(self):
        assert project_slug("") == ""
        assert project_slug(None) == ""


class TestClaimPrefixJoin:
    """claim-<raw-rel-slug> stems are kebab (ingest slugifies), so a project
    glob must canonicalize BEFORE composing — the underscore form matched
    nothing (generators.py old :527 glob could never hit)."""

    def test_prefix_is_kebab_for_underscore_project(self):
        assert claim_prefix_for_project("comfyui_mcp") == "claim-comfyui-mcp"

    def test_layout_glob_matches_ingest_reality(self, tmp_path):
        claims = tmp_path / "evidence" / "claims"
        claims.mkdir(parents=True)
        # what ingest writes for a capture under evidence/raw/comfyui_mcp/
        stem = "claim-comfyui-mcp-comfyui-mcp-agents-md-000"
        (claims / f"{stem}.md").write_text("---\ntype: claim\n---\n")
        g = layout.claims_for_project(tmp_path, "comfyui_mcp")
        hits = list(g.parent.glob(g.name))
        assert hits and hits[0].stem == stem
        # and the kebab spelling finds the same files
        assert list(layout.claims_for_project(tmp_path, "comfyui-mcp").parent.glob(
            layout.claims_for_project(tmp_path, "comfyui-mcp").name)) == hits


def _load(name, rel="cmd"):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / rel / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestGeneratorsProjectArticle:
    """_generate_project_article: old code globbed claim-{project}-*.md (raw
    form → 0 hits for underscore projects → article silently suppressed) plus
    a dead claim-{project.replace('-','_')}* variant (matched nothing ever)."""

    def test_underscore_project_finds_claims(self, tmp_path, monkeypatch):
        spec = importlib.util.spec_from_file_location(
            "generators_real", _SCRIPTS / "wiki_lib" / "generators.py")
        gen = importlib.util.module_from_spec(spec)
        sys.modules["generators_real"] = gen
        spec.loader.exec_module(gen)

        monkeypatch.setattr(gen, "get_repo_config", lambda c, p: {"path": str(tmp_path / "repo")})
        corpus = tmp_path / "corpus"
        claims = corpus / "evidence" / "claims"
        claims.mkdir(parents=True)
        (claims / "claim-comfyui-mcp-agents-md-000.md").write_text(
            "---\ntype: claim\nstatement: it works\nstatus: supported\n"
            "review_after: 2999-01-01\n---\n")
        monkeypatch.setattr(gen.fabric_config, "CORPUS_ROOT", corpus)
        gen._CORPUS = corpus
        out, n = gen._generate_project_article("comfyui_mcp", {}, dry_run=True)
        assert out is not None and n == 1


class TestJudgmentRelatedPool:
    """related_claim_pool: the src- stem join dropped the src- prefix
    correctly (was: src_slug.replace('-md','') — a stem containing '-md'
    elsewhere corrupted the join), and the project regex truncated at the
    first dash ('comfyui' of comfyui-mcp)."""

    def test_same_source_join_uses_raw_rel_slug(self, tmp_path, monkeypatch):
        jd = _load_judgment()
        corpus = tmp_path / "corpus"
        claims = corpus / "evidence" / "claims"
        claims.mkdir(parents=True)
        same_src = claims / "claim-comfyui-mcp-agents-md-001.md"
        other = claims / "claim-godot-agents-readme-md-001.md"
        new_claim = claims / "claim-comfyui-mcp-agents-md-000.md"
        for p in (same_src, other, new_claim):
            p.write_text("---\ntype: claim\n---\n")
        pool = jd.related_claim_pool(new_claim, _claims_root=corpus)
        assert any(p.stem == "claim-comfyui-mcp-agents-md-001" for p in pool)
        assert not any("godot" in p.stem for p in pool)

    def test_project_neighbors_not_truncated(self, tmp_path, monkeypatch):
        jd = _load_judgment()
        corpus = tmp_path / "corpus"
        claims = corpus / "evidence" / "claims"
        claims.mkdir(parents=True)
        (claims / "claim-comfyui-mcp-ui-md-000.md").write_text("---\ntype: claim\n---\n")
        (claims / "claim-comfyui-mcp-ui-md-001.md").write_text("---\ntype: claim\n---\n")
        (claims / "claim-comfyu-other-x-md-000.md").write_text("---\ntype: claim\n---\n")
        (claims / "claim-comfyui-mcp-ui-md-002.md").write_text("---\ntype: claim\n---\n")
        # new claim cites no source; project neighborhood must include the
        # comfyui-mcp claim, not the comfyu- one (old regex: 'comfyui')
        pool = jd.related_claim_pool(claims / "claim-comfyui-mcp-ui-md-002.md",
                                     _claims_root=corpus)
        stems = {p.stem for p in pool}
        assert "claim-comfyui-mcp-ui-md-000" in stems
        assert not any(s.startswith("claim-comfyu-other") for s in stems)


def _load_judgment():
    spec = importlib.util.spec_from_file_location(
        f"judgment_real{id(_load_judgment)}", _SCRIPTS / "lib" / "judgment.py")
    jd = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = jd
    spec.loader.exec_module(jd)
    return jd


class TestMineChatsSourceStem:
    """mine-chats propose: the source_chat wikilink was f'{project}-chats-…'
    (raw form) — for underscore projects it pointed at a stem ingest never
    created; now slugify(project + /chats/ + stem) reproduces ingest's stem."""

    def test_underscore_project_link_matches_ingest(self, tmp_path, monkeypatch):
        import re as _re
        mc = importlib.util.spec_from_file_location(
            "mc_real", _SCRIPTS / "cmd" / "mine-chats.py")
        mc = importlib.util.module_from_spec(mc)
        sys.modules["mc_real"] = mc
        mc.__loader__.exec_module(mc)
        from wf_common import slugify
        # capture: evidence/raw/comfyui_mcp/chats/d1-chat-x.md
        project, transcript_stem = "comfyui_mcp", "2026-09-30-chat-x"
        expected = slugify(f"{project}/chats/{transcript_stem}")
        assert expected == "comfyui-mcp-chats-2026-09-30-chat-x"