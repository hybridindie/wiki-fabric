#!/usr/bin/env python3
# obsidian_status.py — integrations view for the obsidian bridge (#112).
# Deterministic, 0 tokens: server reachability, key source, manifest state,
# pending harvest count.
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))

from obsidian_bridge import (_integration_cfg, _resolve_key, check_server,
                             load_manifest, harvest_before_export)
from fabric_config import get_vault_path


def main():
    cfg = _integration_cfg()
    if cfg is None:
        print("  obsidian: off")
        return 0
    vault = get_vault_path()
    alive = check_server(cfg)
    state = "reachable" if alive else "NOT reachable (is Obsidian running?)"
    print(f"  server: {_integration_cfg_url(cfg)} — {state}")
    key, src = _resolve_key(cfg)
    print(f"  api key: {'found' if key else 'MISSING'} ({src})")
    if vault:
        print(f"  vault: {vault}")
    m = load_manifest()
    if m:
        print(f"  manifest: {len(m.get('files', {}))} note(s) recorded at {m.get('generated', '?')}")
    else:
        print("  manifest: none (first export establishes the baseline)")
    if alive:
        h = harvest_before_export(dry_run=True)
        if h.get("harvested"):
            print(f"  pending harvest: {h['harvested']} human-edited note(s)")
        elif h.get("reason"):
            print(f"  pending harvest: none ({h['reason']})")
        else:
            print("  pending harvest: none")
    return 0


def _integration_cfg_url(cfg):
    return str(cfg.get("api_url") or "").rstrip("/")


if __name__ == "__main__":
    sys.exit(main())