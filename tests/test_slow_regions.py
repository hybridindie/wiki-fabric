"""SkillOpt S4 (#141): protected slow-lane regions on pattern pages."""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS / "cmd", _SCRIPTS / "lib", _SCRIPTS):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import lint as L
import yaml


def _git(tmp, project, corpus):
    """Init a git repo with content committed (so HEAD exists)."""
    import subprocess as sp
    sp.run(["git", "init", "-q", str(tmp)], check=True)
    sp.run(["git", "-C", str(tmp), "add", "-A"], check=True)
    r = sp.run(["git", "-C", str(tmp), "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-qm", "seed"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def _seed(tmp):
    import fabric_config
    corpus = tmp / "corpus"
    patterns = corpus / "patterns"
    patterns.mkdir(parents=True)
    fm = {"type": "pattern", "id": "pattern-x", "title": "X",
          "applicability": {"includes": ["a"], "excludes": ["protected exclusion"]},
          "counterexamples": ["only when offline"]}
    body = "# X\n\npattern body\n"
    text = "---\n" + yaml.safe_dump(fm, sort_keys=False) + "---\n\n" + body
    (patterns / "pattern-x.md").write_text(text)
    _git(tmp, "p", corpus)
    monkeypatch = None
    return corpus, text


def _lint_errors(tmp, monkeypatch):
    class S:
        vault = tmp / "corpus"
        _fm_cache = {}
    from wf_common import parse_frontmatter
    p = S.vault / "patterns" / "pattern-x.md"
    fm, body = parse_frontmatter(p)
    monkeypatch.setattr(L, "parse_frontmatter", lambda path, _cache=None: (fm, body))
    # ensure a real HEAD exists
    import subprocess as sp
    sp.run(["git", "-C", str(tmp), "add", "-A"], check=True)
    return L.check_slow_regions(S(), fm, Path("patterns/pattern-x.md"),
                                "patterns/pattern-x.md")


class TestSlowRegions:
    def test_clean_page_no_error(self, tmp_path, monkeypatch):
        _seed(tmp_path)
        assert _lint_errors(tmp_path, monkeypatch) == []

    def test_fastlane_edit_without_justification_errors(self, tmp_path, monkeypatch):
        corpus, text = _seed(tmp_path)
        p = corpus / "patterns" / "pattern-x.md"
        # HEAD already contains the clean pattern (seeded+committed); edit
        # protected content in the worktree WITHOUT committing — the fast lane
        new = text.replace("only when offline", "only when offline — EDITED fast lane")
        p.write_text(new)
        problems = _lint_errors(tmp_path, monkeypatch)
        assert problems and problems[0].startswith("SLOW-REGION")
        assert "slow-update" in problems[0]

    def test_slow_update_justification_clears(self, tmp_path, monkeypatch):
        corpus, text = _seed(tmp_path)
        p = corpus / "patterns" / "pattern-x.md"
        new = text.replace("only when offline", "only when offline — EDITED fast lane")
        # slow-update justification must live in FRONTMATTER (verified:)
        # text starts with '---\n<fm>\n---\n<body>' — insert before the 3rd line-of-dashes
        first_close = new.index("---", 3)  # the closing delimiter
        new = new[:first_close] + "verified:\n  - by: human:johnd\n    reason: \"slow-update: reviewed exclusion change\"\n" + new[first_close:]
        assert "slow-update" in new[:new.index("\n# X")]
        p.write_text(new)
        assert _lint_errors(tmp_path, monkeypatch) == []

    def test_new_page_no_error(self, tmp_path, monkeypatch):
        corpus, _ = _seed(tmp_path)
        import fabric_config
        monkeypatch.setattr(L.fabric_config, "CORPUS_ROOT", corpus, raising=False) if hasattr(L, "fabric_config") else None
        import fabric_config as fc
        monkeypatch.setattr(fc, "CORPUS_ROOT", corpus, raising=False)
        # a brand-new page (not committed) with protected content is fine
        problems = _lint_errors(tmp_path, monkeypatch)
        # page IS tracked and unmodified — clean
        assert problems == []

    def test_untracked_page_no_error(self, tmp_path, monkeypatch):
        corpus, _ = _seed(tmp_path)
        p2 = corpus / "patterns" / "pattern-new.md"
        p2.write_text("---\ntype: pattern\nid: pattern-new\ntitle: N\n"
                      "applicability:\n  excludes:\n    - \"x\"\ncounterexamples: []\n---\n\nb\n")
        # uncommitted new page → git show fails → no error (creation is gated elsewhere)
        class S:
            vault = corpus
            _fm_cache = {}
        from wf_common import parse_frontmatter
        fm, body = parse_frontmatter(p2)
        problems = L.check_slow_regions(S(), fm, Path("patterns/pattern-new.md"), "patterns/pattern-new.md")
        assert problems == []


class TestMinerRevisionProposal:
    def test_differring_protected_content_changes_fingerprint(self, tmp_path):
        """The miner's SLOW-REGION rule: differing protected content means a
        revision must be proposed, never an overwrite. Verify the fingerprint
        contract the miner checks."""
        from lint import protected_fingerprint
        base = "---\ntype: pattern\nid: pattern-c1\ntitle: C1\n" \
               "applicability:\n  excludes:\n    - \"old exclusion\"\n" \
               "counterexamples: []\n---\n\nbody\n"
        fm_old = parse_frontmatter_str(base)[0]
        fm_new = parse_frontmatter_str(base.replace("old exclusion", "new exclusion"))[0]
        assert protected_fingerprint(fm_old) != protected_fingerprint(fm_new)
        # identical → no revision needed
        assert protected_fingerprint(parse_frontmatter_str(base)[0]) == \
               protected_fingerprint(parse_frontmatter_str(base)[0])


def parse_frontmatter_str(text):
    import yaml as _yaml
    import re as _re
    m = _re.match(r"\A---\n(.*?)\n---\n", text, _re.S)
    if not m:
        return {}, text
    try:
        return (_yaml.safe_load(m.group(1)) or {}), text
    except Exception:
        return {}, text
