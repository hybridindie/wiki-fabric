"""Shim ↔ python-dispatch verb parity (#170): every verb the python dispatch
registers must be reachable through `scripts/wiki-fabric.sh` — the bash shim is
a documented surface (AGENTS.md rows, onboarding docs, Windows-less installs),
so a python-only verb silently breaks the shim users.

The test parses the shim's main dispatcher `case` labels (no bash execution —
static, 0 tokens) and diffs against dispatch.VERBS. Dispatch-native verbs the
shim intentionally implements in bash carry its own case label — that counts.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import wiki_fabric.dispatch as dispatch

_SHIM = Path(__file__).resolve().parent.parent / "scripts" / "wiki-fabric.sh"

# dispatch verbs the shim deliberately does NOT offer (pure bash-side or
# alias-covered — each needs a comment in the shim when added)
SHIM_EXEMPT = set()


def shim_dispatch_labels():
    """Top-level verb labels: `case ... in` blocks at 4-space indent in the
    shim's MAIN dispatcher (verb labels are the 4-indent `foo)` lines; nested
    subcommand cases indent deeper and are skipped)."""
    labels = set()
    depth_ok = False
    for line in _SHIM.read_text().splitlines():
        if line.startswith("case "):
            depth_ok = True  # main dispatcher (first top-level case in file order among dispatchers)
            continue
        if depth_ok and line == "esac":
            break
        if not depth_ok:
            continue
        m = re.fullmatch(r'    "?([a-z][a-z0-9_|-]+)"?\)', line)
        if m:
            for part in m.group(1).split("|"):
                part = part.strip().strip('"')
                if re.fullmatch(r"[a-z][a-z0-9_-]*", part):
                    labels.add(part)
    return labels


def test_every_dispatch_verb_reachable_from_shim():
    labels = shim_dispatch_labels()
    # dispatch-native verbs with no subprocess script: implemented in the shim
    # as bash flows (status/version/install/update) or covered by aliases
    # (claude→harness case label). Anything else must have a label.
    covered = {"install", "update", "status", "version", "help", "harness",
               "claude", "vault", "wiki-generate", "publish"}
    missing = sorted(v for v in dispatch.VERBS
                     if v not in labels and v not in covered and v not in SHIM_EXEMPT)
    assert not missing, (
        f"verbs registered in the python dispatch but NOT dispatchable through "
        f"scripts/wiki-fabric.sh: {missing} — add a shim case (see freshness, #170)"
    )


def test_shim_labels_are_real_verbs():
    """Inverse: a shim label that matches no verb and no bash command is a
    typo / dead branch (kept conservative: only flag known-command typos)."""
    labels = shim_dispatch_labels()
    known_bash = {"install", "update", "status", "help", "version", "vault",
                  "wiki-generate", "publish", "claude", "harness"}
    unknown = sorted(l for l in labels
                     if l not in dispatch.VERBS and l not in known_bash)
    assert not unknown, f"shim dispatches unknown verbs: {unknown}"