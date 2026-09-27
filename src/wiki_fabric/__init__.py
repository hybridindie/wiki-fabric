"""wiki-fabric — evidence-first knowledge base that compounds across projects.

Package layout (phase-1 spike, #118): the harness tree ships as package data.
The console script locates it at runtime and runs the bash orchestrator with
bash — 100% of today's behavior, delivered as an installable package.
"""
from pathlib import Path


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
