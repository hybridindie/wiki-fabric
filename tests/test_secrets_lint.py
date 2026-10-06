"""#188 — the SECRETS lint rule (Memory Defense, minus the server).

Deterministic scan of corpus content planes for credential-shaped strings;
ERROR tier (blocks the commit gate); matches masked in output; evidence/raw/
 exempt (immutable capture plane); tombstones exempt (they quote rejected
content by design).

Run: python3 -m pytest tests/test_secrets_lint.py -v
"""
import sys
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import os
os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-secrets")


def _lint_module():
    import importlib
    for mod in list(sys.modules):
        if mod == "lint":
            del sys.modules[mod]
    spec = importlib.util.spec_from_file_location(
        f"lint_secrets_{id(dict()) % 99999}", _REPO / "scripts" / "cmd" / "lint.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lint"] = mod
    spec.loader.exec_module(mod)
    return mod


class _State:
    def __init__(self, vault):
        self.vault = Path(vault)
        self.errors = []
        self.warnings = []
        self.pages = {}
        self.INDEX = set()
        self._fm_cache = {}


class TestSecretPatterns:
    """Each pattern class fires on its own shape, nowhere else."""

    def _seed(self, tmp_path, body, rel="patterns/pattern-x.md"):
        p = Path(tmp_path) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"---\ntype: pattern\nstatus: candidate\n---\n\n{body}\n")
        return p

    def _errors(self, tmp_path):
        L = _lint_module()
        st = _State(tmp_path)
        L.check_secrets(st)
        return st.errors

    def _masked(self, errors):
        return all("…" not in e or "****" in e for e in errors) and \
            all("AGHJ" not in e for e in errors)  # the middle chars never print

    def test_github_token(self, tmp_path):
        self._seed(tmp_path, 'use token ghp_AGHJklmnopqrstuvwxyzABCDEFGHIJ1234567890abcd')
        errs = self._errors(tmp_path)
        assert any("github_token" in e for e in errs)
        assert all("AGHJklmnop" not in e for e in errs)  # masked
        assert all("ghp_AGHJ" not in e for e in errs)    # full value never prints

    def test_openai_key(self, tmp_path):
        self._seed(tmp_path, "key: sk-proj-abcdefghij0123456789ABCDEFGHIJ")
        assert any("openai" in e for e in self._errors(tmp_path))

    def test_aws_key(self, tmp_path):
        self._seed(tmp_path, "AKIAIOSFODNN7EXAMPLE")
        assert any("aws" in e for e in self._errors(tmp_path))

    def test_slack_token(self, tmp_path):
        self._seed(tmp_path, "xoxb-123456789012-abcdef")
        assert any("slack" in e for e in self._errors(tmp_path))

    def test_private_key_block(self, tmp_path):
        self._seed(tmp_path, "-----BEGIN RSA PRIVATE KEY-----")
        assert any("private key" in e for e in self._errors(tmp_path))

    def test_frontmatter_assignment_backstop(self, tmp_path):
        p = Path(tmp_path) / "patterns/pattern-y.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('---\ntype: pattern\napi_key: "abcdefghij0123456789ABCDEFGHIJKLMN"\n---\n\nbody\n')
        errs = self._errors(tmp_path)
        assert any("credential-shaped assignment" in e for e in errs)

    def test_plain_prose_is_clean(self, tmp_path):
        self._seed(tmp_path, "Set TYPESAFE_API_KEY in secrets.env; the judge reads it at runtime.")
        assert self._errors(tmp_path) == []

    def test_short_strings_not_flagged(self, tmp_path):
        self._seed(tmp_path, "token: sk-short")  # under the length floor
        assert self._errors(tmp_path) == []

    def test_evidence_raw_exempt(self, tmp_path):
        self._seed(tmp_path, "captured doc mentions ghp_AGHJklmnopqrstuvwxyzABCDEFGHIJ1234567890abcd",
                   rel="evidence/raw/proj/docs/readme-md.md")
        assert self._errors(tmp_path) == []  # immutable capture plane

    def test_tombstone_exempt(self, tmp_path):
        p = Path(tmp_path) / "patterns" / "_rejected" / "tombstone-x.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("---\ntype: rejection-tombstone\nid: tombstone-x\n---\n\n"
                     "rejected for: ghp_AGHJklmnopqrstuvwxyzABCDEFGHIJ1234567890abcd\n")
        assert self._errors(tmp_path) == []

    def test_error_tier_and_masked_remediation(self, tmp_path):
        self._seed(tmp_path, 'ghp_AGHJklmnopqrstuvwxyzABCDEFGHIJ1234567890abcd')
        errs = self._errors(tmp_path)
        assert all(e.startswith("SECRETS") for e in errs)
        assert any("rotate the credential" in e for e in errs)


class TestWiring:
    def test_section_ran_in_full_lint(self, tmp_path, capsys):
        """The section is wired into run()'s section chain."""
        src = (_REPO / "scripts" / "cmd" / "lint.py").read_text()
        assert "_section_secrets(state)" in src
        assert "def check_secrets(state)" in src

    def test_machine_contract_rows(self):
        mc = (_REPO / "docs" / "site" / "machine-contract.md").read_text()
        assert "SECRETS" in mc


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])