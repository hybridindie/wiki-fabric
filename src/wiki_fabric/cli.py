"""wf console-script: locate the packaged harness and run its bash orchestrator.

Keeps the bash dispatcher as the single source of behavior (1,266 lines of
working UX); the package is the delivery vehicle. `bash` must be present —
POSIX systems and Git-for-Windows both have it.
"""
import os
import shutil
import subprocess
import sys

from . import runner_script


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    script = runner_script()
    if not script.exists():
        raise SystemExit(f"wiki-fabric: harness script not found at {script} (broken install)")
    bash = shutil.which("bash")
    if not bash:
        raise SystemExit("wiki-fabric: `bash` not found on PATH (required by the wf orchestrator)")
    os_env = {**os.environ, "WF_PACKAGED": "1"}
    cmd = [bash, str(script), *argv]
    result = subprocess.run(cmd, env={**os.environ, **os_env})
    raise SystemExit(result.returncode)


def run():
    main(sys.argv[1:])
