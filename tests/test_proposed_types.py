"""Proposed asset types (#64): governed middle path between closed and open.

proposed_types: in fabric.yaml → unknown type = PROPOSED-TYPE warning
(not a TYPE error); adoption = adding to VALID_TYPES via PR.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent


def _lint(tmp):
    out = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "cmd/lint.py"), "--format", "json", str(tmp)],
        capture_output=True, text=True)
    r = json.loads(out.stdout)
    return r, out.returncode


class TestProposedTypes:
    def _page(self, tmp, ptype):
        (tmp / "page.md").write_text(f"---\ntype: {ptype}\ntitle: X\n---\n\nbody\n")

    def test_adopted_type_no_warning(self, tmp_path):
        self._page(tmp_path, "pattern")
        r, _ = _lint(tmp_path)
        assert not [e for e in r["errors"] if e["code"] == "TYPE"]
        assert not [w for w in r["warnings"] if w["code"] == "PROPOSED-TYPE"]

    def test_unknown_type_is_error(self, tmp_path):
        self._page(tmp_path, "bananas")
        r, _ = _lint(tmp_path)
        assert any(e["code"] == "TYPE" for e in r["errors"])

    def test_proposed_type_is_warning_not_error(self, tmp_path):
        (tmp_path / "fabric.yaml").write_text("proposed_types: [spec]\n")
        self._page(tmp_path, "spec")
        r, rc = _lint(tmp_path)
        assert not [e for e in r["errors"] if e["code"] == "TYPE"], "proposed type must not be a TYPE error"
        assert any(w["code"] == "PROPOSED-TYPE" for w in r["warnings"])
        assert any("adopt" in w["message"] for w in r["warnings"])
