#!/usr/bin/env python3
"""Deterministic attester: run the profile lint and confirm 0 errors."""
import subprocess
import json
import sys
from pathlib import Path

FABRIC = Path(__file__).resolve().parent.parent.parent
vault = sys.argv[1] if len(sys.argv) > 1 else str(FABRIC)
import subprocess as sp
out = sp.run([sys.executable, str(FABRIC / "scripts" / "lint.py"), "--format", "json", vault],
             capture_output=True, text=True)
d = json.loads(out.stdout)
receipt = {"errors": d["counts"]["errors"], "warnings": d["counts"]["warnings"],
           "ok": d["counts"]["errors"] == 0, "okf": d["okf_conformance"]["conformant"]}
print(json.dumps({"verdict": "ATTESTED" if receipt["errors"] == 0 else "REFUSED", **receipt}))
sys.exit(0 if receipt["errors"] == 0 else 1)
