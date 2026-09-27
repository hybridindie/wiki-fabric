"""wf console-script — full-python dispatch (phase 2 of #118).

The bash orchestrator is retired: every verb lives in dispatch.py. The
packaged harness tree still ships the underlying scripts (they are the
verbs' implementations); install/update are owned by uv.
"""
import os
import sys

# stamp the packaged invocation BEFORE dispatch (update/status key off it)
os.environ.setdefault("WF_PACKAGED", "1") if getattr(sys, "frozen", False) else None

from .dispatch import main


def run():
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    run()
