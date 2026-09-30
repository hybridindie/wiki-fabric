#!/usr/bin/env python3
# render_template.py — bash-side renderer of the ONE config template (#153).
# wiki-fabric.sh ensure_fabric_yaml calls this (python3 render_template.py
# owner=<name> [--graphify] key=value ...) so a fresh bash-path install gets
# the same fabric.yaml shape the python path produces (compiler_model present
# — its absence tripped the G4 gate on promotion).

import sys
import pathlib

_LIB = pathlib.Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from fabric_config import render_config_template


def main(argv=None):
    owner = "you"
    with_graphify = False
    extra_parts = []
    for arg in (argv if argv is not None else sys.argv[1:]):
        if arg == "--graphify":
            with_graphify = True
        elif "=" in arg:
            k, _, v = arg.partition("=")
            if k == "owner":
                owner = v
            else:
                extra_parts.append(f"# {k}: {v}")
    sys.stdout.write(render_config_template(
        owner=owner, with_graphify=with_graphify,
        extra="\n".join(extra_parts) if extra_parts else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())