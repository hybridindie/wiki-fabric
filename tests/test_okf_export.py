"""Tests for okf_export.py (Story 5 — wf okf export)."""
import sys
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent


class TestExport:
    def _seeded_fabric(self, tmp_path):
        """Copy the harness into tmp, then seed one source + one claim there.
        Never touches the real checkout — CI-safe."""
        import shutil
        fabric = tmp_path / "fabric"
        shutil.copytree(REPO, fabric, ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", ".okflint", ".pytest_cache",
            ".obsidian", ".opencode", "node_modules"))
        (fabric / "evidence" / "raw" / "seeded").mkdir(parents=True, exist_ok=True)
        (fabric / "evidence" / "raw" / "seeded" / "doc.md").write_text(
            "Seeded raw doc with no frontmatter.\n")
        (fabric / "evidence" / "sources").mkdir(parents=True, exist_ok=True)
        (fabric / "evidence" / "sources" / "src-seeded-doc-md.md").write_text(
            "---\ntype: source\ntitle: Seeded Doc\nkind: doc\ntags: []\n"
            "resource: 'evidence/raw/seeded/doc.md'\n"
            "source_path: evidence/raw/seeded/doc.md\n"
            "sha256: 0000000000000000000000000000000000000000000000000000000000000000\n"
            "captured: 2026-09-18\nstatus: pending\n---\n\n# Seeded Doc\n")
        (fabric / "evidence" / "claims").mkdir(parents=True, exist_ok=True)
        (fabric / "evidence" / "claims" / "claim-seeded-doc-md-000.md").write_text(
            "---\ntype: claim\nid: claim-seeded-doc-md-000\n"
            'statement: "Seeded claim for export testing."\n'
            "status: supported\n"
            "source_refs:\n"
            "  - source: \"[[src-seeded-doc-md]]\"\n"
            "    locator: \"L1\"\n"
            '    quote: "Seeded claim for export testing."\n'
            "    supports: true\n---\n\n# claim\nBody.\n")
        return fabric

    def _export(self, tmp_path, scope="all", fabric_root=None):
        out = tmp_path / "bundle"
        cmd = [sys.executable, str(REPO / "scripts" / "okf_export.py"),
               "--out", str(out), "--scope", scope]
        if fabric_root:
            cmd += ["--root", str(fabric_root)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        return out

    def test_root_index_has_okf_version(self, tmp_path):
        fabric = self._seeded_fabric(tmp_path)
        out = self._export(tmp_path, scope="global", fabric_root=fabric)
        text = (out / "index.md").read_text()
        assert 'okf_version: "0.2"' in text

    def test_claim_source_refs_rendered_as_sources(self, tmp_path):
        fabric = self._seeded_fabric(tmp_path)
        out = self._export(tmp_path, scope="global", fabric_root=fabric)
        claims = list((out / "evidence" / "claims").glob("*.md"))
        assert claims, "expected exported claims"
        with_frontmatter_sources = [c for c in claims if "sources:" in c.read_text()]
        assert with_frontmatter_sources, "claims should carry OKF sources[]"

    def test_footnotes_keyed(self, tmp_path):
        fabric = self._seeded_fabric(tmp_path)
        out = self._export(tmp_path, scope="global", fabric_root=fabric)
        claims = list((out / "evidence" / "claims").glob("*.md"))
        with_footnotes = [c for c in claims if "\n[^wf-" in c.read_text()]
        assert with_footnotes

    def test_no_wikilinks_in_export(self, tmp_path):
        fabric = self._seeded_fabric(tmp_path)
        out = self._export(tmp_path, scope="global", fabric_root=fabric)
        import re
        sample = list((out / "evidence" / "claims").glob("*.md"))[:20]
        LINK = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
        # placeholders (<slug>) may remain; real links must resolve
        bad = [c.name for c in sample for m in LINK.findall(c.read_text())
               if "<" not in m[0] and "..." not in m[0]]
        assert not bad, f"unresolved wikilinks in export: {bad}"

    def test_deterministic(self, tmp_path):
        fabric = self._seeded_fabric(tmp_path)
        out1 = self._export(tmp_path / "a", scope="global", fabric_root=fabric)
        out2 = self._export(tmp_path / "b", scope="global", fabric_root=fabric)
        d1 = sorted(p.relative_to(out1).as_posix() + "|" + p.read_text()
                    for p in out1.rglob("*.md"))
        d2 = sorted(p.relative_to(out2).as_posix() + "|" + p.read_text()
                    for p in out2.rglob("*.md"))
        assert d1 == d2

    def test_raw_in_references(self, tmp_path):
        fabric = self._seeded_fabric(tmp_path)
        out = self._export(tmp_path, scope="global", fabric_root=fabric)
        refs = out / "references"
        assert refs.exists() and any(refs.rglob("*.md"))
