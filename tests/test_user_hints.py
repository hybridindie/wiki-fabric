"""Hint-drift guard: runtime user-facing hints must name wf VERBS, not
python3 script paths (the gate.py 'Resolve:' class — script spellings rot
when verbs move; verbs are the stable surface).

Run: python3 -m pytest tests/test_user_hints.py -v
"""
import ast
import re
from pathlib import Path

import pytest

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
_CMD = _SCRIPTS / "cmd"

# docstring usage headers are file-documentation (acceptable); PRINTED hints
# are user-facing and must use the verb surface.
_SCRIPT_PATH_RE = re.compile(
    r"python3 scripts/(?:cmd|harness|eval)/[\w-]+\.py")

# files whose ENTIRE purpose is documented by header only
ALLOWED_HINTS = set()


def _print_strings(tree):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "print" and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.append((node.lineno, a.value))
    return out


def test_runtime_hints_use_verbs():
    offenders = []
    for f in sorted(_CMD.glob("*.py")):
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for lineno, text in _print_strings(tree):
            for m in _SCRIPT_PATH_RE.finditer(text):
                offenders.append(f"{f.name}:{lineno}: {m.group(0)}")
    # known-good: none expected (fixed 2026-10-02; gate.py was the origin)
    assert not offenders, ("runtime hint names a script path — use the wf verb "
                           "(docs/site/cli.md):\n" + "\n".join(offenders))
