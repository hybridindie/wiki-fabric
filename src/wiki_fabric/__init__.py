"""wiki-fabric — evidence-first knowledge base that compounds across projects.

Phase 2 (#118): the dispatcher is pure python (no bash dependency) — every
verb maps to the shipped script it always ran, executed with the right
interpreter. The harness tree ships as package data; install/update are
owned by uv (no script-copy, no CLI/harness drift). Windows-first-class.
"""
from pathlib import Path

try:
    from importlib.metadata import version as _version
    __version__ = version("wiki-fabric")
except Exception:  # dev checkout without install — keep in sync with pyproject
    __version__ = "0.3.1"

# Packaged-install detection (phase 2): the _harness tree beside this package
# means wf runs from a uv tool install — update/status key off WF_PACKAGED.
import os as _os
_here = Path(__file__).resolve().parent
if (_here / "_harness" / "scripts").exists():
    _os.environ.setdefault("WF_PACKAGED", "1")


def package_root() -> Path:
    """Root of the shipped harness tree (scripts/, system/, templates/...).

    In an editable/checkout install this is the repo root; in a wheel install
    the harness tree is packaged data under wiki_fabric/_harness/."""
    here = Path(__file__).resolve().parent
    harness = here / "_harness"
    if (harness / "scripts" / "wiki-fabric.sh").exists():
        return harness
    # editable/dev install: the repo root is two levels up
    return here.parent.parent


def runner_script() -> Path:
    """The bash orchestrator shipped inside the package."""
    return package_root() / "scripts" / "wiki-fabric.sh"
