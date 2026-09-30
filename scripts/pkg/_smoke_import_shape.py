#!/usr/bin/env python3
"""wheel-smoke helper: verify the packaged shared-lib import shape.

Runs with the WHEEL's venv python against the repo's staging copy
(src/wiki_fabric/_harness) — the anti-drift contract from AGENTS.md:
scripts must import shared lib modules, never local copies.
"""
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
harness = repo / "src" / "wiki_fabric" / "_harness"
sys.path.insert(0, str(harness / "scripts" / "lib"))

import fabric_config
from extract_backends import extract_claims

assert hasattr(fabric_config, "get_config"), "fabric_config.get_config missing"
assert callable(extract_claims), "extract_backends.extract_claims missing"
print("fabric_config + extract_backends import ok from packaged lib")