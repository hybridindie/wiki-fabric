"""Layout guard: corpus-dir names may only be spelled in layout.py.

The single-truth rule (AGENTS.md / docs/site/corpus-layout.md): scripts
compose corpus paths via scripts/lib/layout.py accessors. A re-spelled
CORPUS_ROOT/"evidence"/... join at a call site is exactly how the two-tree
slug bug and the layout-drift class crept in before. This guard is the
mechanical counterpart: scan scripts/ + src/ for path-literal joins over
corpus segment names and fail when they appear outside the sanctioned set.

Run: python3 -m pytest tests/test_layout_guard.py -v
"""

import ast
import re
import sys
from pathlib import Path

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
_SRC = _SCRIPTS.parent / "src"

SCAN_ROOTS = [_SCRIPTS, _SRC] if _SRC.exists() else [_SCRIPTS]

# Files allowed to spell corpus segments as path literals:
#  - layout.py itself (the declaration)
#  - fabric_config.py (roots; cannot import layout — cycle)
#  - paths.py (fabric-root primitives, pre-corpus resolution)
ALLOWED = {
    "scripts/lib/layout.py",
    "scripts/lib/fabric_config.py",
    "scripts/lib/paths.py",
}

# Synthetic-corpus builders: evals/tests construct THROWAWAY trees (tmp/...)
# with the same shape — not the live corpus. Their root name marks intent.
SYNTHETIC_ROOT_NAMES = {"tmp", "fake", "syn", "seed", "fixture", "stage"}
# Base names that are NOT corpus roots (harness assets, output vaults, scaffold
#-time roots) — layout guards the corpus; these trees have different owners.
NON_CORPUS_BASES = {"harness_root", "fabric_root", "fabric_dir", "wiki_root",
                    "own", "HARNESS_ROOT"}

# The corpus segment names guarded by layout.SEGMENTS
SEGMENTS = (
    "evidence", "patterns", "anti-patterns", "skills", "concepts", "domains",
    "projects", "registry", "global", "syntheses", "questions",
)

JOIN_RE = re.compile(
    r"\b(?:CORPUS_ROOT|VAULT_ROOT|CORPUS|vault|corpus_root|state\.vault|"
    r"fabric_config\.CORPUS_ROOT)\s*/\s*"
    r"['\"](?:" + "|".join(re.escape(s) for s in SEGMENTS) + r")['\"]"
)

# Path.joinpath / __truediv__ via ast: catch composed joins too
def _ast_join_sites(tree):
    """Yield (line, root_name, first_segment) for BinOp path joins."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            root = None
            seg = None
            names = []
            if isinstance(node.left, ast.Name):
                root = node.left.id
            elif isinstance(node.left, ast.Attribute):
                root = node.left.attr
            elif isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                seg = node.left.value
                root = "<literal-first>"
            if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
                seg = node.right.value
            names.append(root)
            out.append((node.lineno, root, seg))
    return out


def _candidate_files():
    for root in SCAN_ROOTS:
        for f in sorted(root.rglob("*.py")):
            # the packaging STAGING copy (src/wiki_fabric/_harness) is a build
            # artifact of scripts/ — never scan it (the real tree is scanned)
            if "_harness" in f.parts or "site-packages" in f.parts:
                continue
            rel = f.relative_to(_SCRIPTS.parent).as_posix()
            if rel in ALLOWED:
                continue
            if "/tests/" in "/" + rel:
                continue
            yield f, rel


def _offender(rel, line, base, segs):
    """Whitelist logic: synthetic-corpus builders (tmp/...) and harness-asset
    joins are not corpus-path re-spells."""
    b = (base or "").lower().lstrip("_")
    if b in SYNTHETIC_ROOT_NAMES or b in {n.lower() for n in NON_CORPUS_BASES}:
        return None
    if b.startswith(("tmp", "fake", "syn", "seed", "fixture", "stage")):
        return None
    return f"{rel}:{line}: {base or '?'} / " + " / ".join(segs)


def test_no_respelled_corpus_joins():
    offenders = []
    for f, rel in _candidate_files():
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in JOIN_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            offenders.append(f"{rel}:{line}: {m.group(0)[:60]}")
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                cur = node
                segs = []
                while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
                    if isinstance(cur.right, ast.Constant) and isinstance(cur.right.value, str):
                        segs.append(cur.right.value)
                    cur = cur.left
                base = cur
                if segs and segs[0] in SEGMENTS and isinstance(base, ast.Name):
                    o = _offender(rel, node.lineno, base.id, list(reversed(segs)))
                    if o:
                        offenders.append(o)
    assert not offenders, (
        "corpus path re-spelled outside layout.py (compose via layout, "
        "docs/site/corpus-layout.md):\n" + "\n".join(offenders))


def test_layout_seg_rejects_undeclared():
    sys.path.insert(0, str(_SCRIPTS / "lib"))
    for stale in [k for k in list(sys.modules) if k == "layout"]:
        del sys.modules[stale]
    import layout
    import pytest
    with pytest.raises(KeyError):
        layout.seg("evidence/claims")