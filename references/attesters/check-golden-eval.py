#!/usr/bin/env python3
"""Deterministic attester: verify the last golden-eval receipt passes gates.

Usage: python3 references/attesters/check-golden-eval.py [--model M]
Exit 0 = attested. Exit 1 = refused (stale/failed/missing).
"""
import sys
import re
import json
from pathlib import Path

FABRIC = Path(__file__).resolve().parent.parent.parent
LOG = FABRIC / "registry" / "log.md"


def main():
    args = sys.argv[1:]
    model = args[args.index("--model") + 1] if "--model" in args else None
    if not LOG.exists():
        print(json.dumps({"verdict": "REFUSED", "reason": "no registry/log.md"}))
        return 1
    text = LOG.read_text()
    # find latest eval block mentioning the model (old or new heading shape)
    blocks = re.findall(r"(?:## \[[\d-]+\] (?:eval|eval-stability) \||## \d{4}-\d{2}-\d{2}\n\* \*\*(?:eval|eval-stability) \|[^\n]*)(.*?)(?=\n## |\Z)", text, re.DOTALL)
    short = (model or "").split(":")[0]
    # Latest block naming the model AND carrying a recall metric
    for b in reversed(blocks):
        named = model is None or model in b or (short and short in b)
        m = re.search(r"[Rr]ecall:?\s*([\d.]+)", b)
        if named and m:
            recall = float(m.group(1))
            verdict = "ATTESTED" if recall >= 0.8 else "REFUSED"
            print(json.dumps({"verdict": verdict, "recall": recall, "threshold": 0.8}))
            return 0 if verdict == "ATTESTED" else 1
    print(json.dumps({"verdict": "REFUSED", "reason": f"no eval receipt with recall for {model or 'compiler model'}"}))
    return 1
    verdict = "ATTESTED" if recall >= 0.8 else "REFUSED"
    print(json.dumps({"verdict": verdict, "recall": recall, "threshold": 0.8}))
    return 0 if verdict == "ATTESTED" else 1


if __name__ == "__main__":
    sys.exit(main())
