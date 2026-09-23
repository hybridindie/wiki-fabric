#!/usr/bin/env python3
# ensure-local-model.py — Check the configured local model; offer to download.
#
# Usage:
#   python3 scripts/cmd/ensure-local-model.py              # check llm.local_model / platform default
#   python3 scripts/cmd/ensure-local-model.py --model <hf-id> [--yes]
#   python3 scripts/cmd/ensure-local-model.py --check      # exit 0 present / 1 missing (no prompt)
#
# Resolution order (see fabric_config.get_local_model):
#   --model flag > llm.local_model in fabric.yaml > WIKI_LLM_LOCAL_MODEL > platform default
#   (mlx-community/gemma-4-e4b-it-4bit on Apple Silicon, GGUF elsewhere).

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
from pathlib import Path

from fabric_config import get_config, get_local_model, find_local_model_path, ensure_local_model


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ensure the local LLM model is available")
    parser.add_argument("--model", default=None, help="HuggingFace model id (default: llm.local_model)")
    parser.add_argument("--yes", "-y", action="store_true", help="Download without prompting")
    parser.add_argument("--check", action="store_true",
                        help="Exit 0 if present, 1 if missing (never prompts or downloads)")
    args = parser.parse_args()

    model_id = args.model or get_local_model(get_config())

    if find_local_model_path(model_id) or Path(model_id).expanduser().is_dir():
        print(f"OK: {model_id} (cached)")
        return 0

    if args.check:
        print(f"MISSING: {model_id} — download with: wf models ensure")
        return 1

    resolved, downloaded = ensure_local_model(model_id, assume_yes=args.yes)
    if resolved:
        if downloaded:
            print(f"OK: {model_id} (downloaded)")
        return 0
    print(f"NOT AVAILABLE: {model_id}")
    return 1


if __name__ == "__main__":
    sys.exit(main())