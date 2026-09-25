#!/usr/bin/env python3
# okf_import.py — Ingest a conformant OKF bundle as EXTERNAL evidence.
#
# Usage:
#   python3 scripts/cmd/okf_import.py <bundle-dir> [--scope <name>] [--extract-claims]
#
# Trust tiers are recorded, never inherited: imported concepts land under
# evidence/raw/<scope>-okf/ as immutable captures with a source record each
# (kind: okf-bundle). Unknown types tolerated (§11). Promotion still requires
# the human-gated pipeline — imported tiers inform, never grant authority.
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import json
import os
import hashlib
import shutil
import yaml
import argparse
from pathlib import Path
from datetime import date, datetime, timezone

from fabric_config import CORPUS_ROOT

VAULT_ROOT = CORPUS_ROOT
RESERVED = {"index.md", "log.md"}

# Hidden/injected-content screen (okf-guard-lite, deterministic):
# zero-width chars, control chars, suspicious directive patterns.
INJECTION_PATTERNS = [
    re.compile(r"[\u200b\u200c\u200d\u2060\ufeff]"),          # zero-width
    re.compile(r"ignore (?:all )?(?:previous|prior) instructions", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"disregard .{0,20}(?:rules|instructions)", re.I),
]
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def screen_body(path, body):
    """Return verdict: pass | quarantine. Deterministic pattern scan."""
    hits = [p.pattern[:40] for p in INJECTION_PATTERNS if p.search(body)]
    ctrl = CONTROL_RE.search(body)
    if ctrl:
        hits.append(f"control-char U+{ord(ctrl.group()):04X}")
    return ("quarantine", hits) if hits else ("pass", [])


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def import_bundle(bundle, scope, extract_claims=False, dry_run=False):
    bundle = Path(bundle).resolve()
    if not bundle.is_dir():
        print(f"Error: bundle not found: {bundle}", file=sys.stderr)
        return 1

    raw_dest = VAULT_ROOT / "evidence" / "raw" / f"{scope}-okf"
    raw_dest.mkdir(parents=True, exist_ok=True)

    # 1. Inventory + trust-tier distribution
    concept_files, skipped_reserved = [], []
    for p in sorted(bundle.rglob("*.md")):
        rel = p.relative_to(bundle)
        if rel.name in RESERVED:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
        if not m:
            # verbatim mirror material (references/ etc) — copy, no source record
            dest = raw_dest / "references" / rel
            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            fm = {}
        concept_files.append((p, rel, fm, m.group(2)))

    tiers = {"unverified": 0, "machine-confirmed": 0, "human-reviewed": 0}
    for _, _, fm, _ in concept_files:
        v = fm.get("verified")
        if isinstance(v, dict):
            v = [v]
        if any(isinstance(x, dict) and str(x.get("by", "")).startswith("human:") for x in (v or [])):
            tiers["human-reviewed"] += 1
        elif v:
            tiers["machine-confirmed"] += 1
        else:
            tiers["unverified"] += 1

    print(f"=== Importing OKF bundle: {bundle.name} ===")
    print(f"concepts: {len(concept_files)}, trust tiers: {tiers}")

    # 2. Screen + capture each concept
    imported, quarantined, screen_hits = 0, 0, []
    for p, rel, fm, _ in concept_files:
        body = p.read_text(encoding="utf-8", errors="replace")
        verdict, hits = screen_body(p, body)
        rel_dest = raw_dest / rel
        if verdict == "quarantine":
            q_dest = VAULT_ROOT / "evidence" / "_inbox" / f"{scope}-okf" / rel
            if not dry_run:
                q_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, q_dest)
            quarantined += 1
            screen_hits.append((str(rel), hits))
            continue
        if not dry_run:
            rel_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, rel_dest)
        imported += 1

    if dry_run:
        print(f"[DRY RUN] would import {imported}, quarantine {quarantined}")
        return 0

    # 3. Source record per imported concept (hash-anchored, immutable)
    src_dir = VAULT_ROOT / "evidence" / "sources"
    src_dir.mkdir(parents=True, exist_ok=True)
    created_sources = 0
    for p, rel, fm, _ in concept_files:
        if p.name in {x.name for x in [raw_dest / rel] } and not (raw_dest / rel).exists():
            continue
        if not (raw_dest / rel).exists():
            continue
        raw_file = raw_dest / rel
        h = sha256(raw_file)
        slug = re.sub(r"[^a-z0-9-]+", "-", rel.as_posix().lower())[:80]
        rec = src_dir / f"src-{slug}.md"
        if rec.exists() and sha256(rec).split("sha256")[0] and str(h) in rec.read_text():
            continue
        v = fm.get("verified")
        tier = ("human-reviewed" if any(isinstance(x, dict) and str(x.get("by", "")).startswith("human:") for x in (v if isinstance(v, list) else [v] if isinstance(v, dict) else []))
                else "machine-confirmed" if v else "unverified")
        rec.write_text(f"""---
type: source
title: "{str(fm.get('title') or rel.stem).replace(chr(34), chr(39))}"
description: "Imported OKF concept from {bundle.name} (trust: {tier})"
generated: {{ by: "{fm.get('generated', {}).get('by', 'unknown') if isinstance(fm.get('generated'), dict) else 'unknown'}", at: "{now_iso()}" }}
tags: [okf-import, {scope}]
kind: okf-bundle
resource: "{raw_file.relative_to(VAULT_ROOT).as_posix()}"
source_path: {raw_file.relative_to(VAULT_ROOT).as_posix()}
sha256: {h}
captured: {date.today().isoformat()}
status: pending
imported_trust_tier: {tier}
---

# {fm.get('title') or rel.stem}

Imported from OKF bundle `{bundle}`. Trust tier **recorded, not inherited**
(imported_trust_tier: {tier}); promotion requires the human-gated pipeline.
""")
        created_sources += 1

    # 4. Optional claim extraction via the compiler pipeline
    #     Stage routing applies: a fabric.yaml repo named "<scope>-okf" (or
    #     "<scope>") with extract: local runs extraction on-device.
    if extract_claims and created_sources:
        import subprocess
        ing = VAULT_ROOT / "scripts" / "cmd/ingest.py"
        cmd = [sys.executable, str(ing), "--pending", f"{scope}-okf", "--extract-claims"]
        try:
            from fabric_config import get_config, get_stage_route, is_local_route
            _cfg = get_config()
            for _proj in (f"{scope}-okf", scope):
                if _cfg.get("repos", {}).get(_proj):
                    _m = get_stage_route(_cfg, _proj, "extract")
                    if is_local_route(_cfg, _proj, "extract"):
                        cmd = [sys.executable, str(ing), "--pending", f"{scope}-okf",
                               "--extract-claims", "--model", _m]
                        os.environ["WIKI_LLM_BACKEND"] = "mlx"
                    else:
                        cmd = [sys.executable, str(ing), "--pending", f"{scope}-okf",
                               "--extract-claims", "--model", _m]
                    break
        except Exception:
            pass
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(r.stdout[-500:] if r.stdout else "")

    # 5. Registry log entry (OKF §9 shape)
    log = VAULT_ROOT / "registry" / "log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        log.write_text("---\ntype: log\ntitle: Log\ncreated: %s\nupdated: %s\n---\n\n# Log\n\nAppend-only timeline.\n"
                       % (date.today().isoformat(), date.today().isoformat()))
    with open(log, "a") as f:
        f.write(f"\n## {date.today().isoformat()}\n")
        f.write(f"* **okf-import | {scope}** — bundle {bundle.name}: {imported} concepts "
                f"(quarantine {quarantined}), tiers {tiers}\n")

    print(f"Import summary: {imported} imported, {quarantined} quarantined, {created_sources} source records")
    if quarantined:
        print(f"Quarantined (review at evidence/_inbox/{scope}-okf/):")
        for rel, hits in screen_hits[:5]:
            print(f"  - {rel}: {hits}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Import a conformant OKF bundle as external evidence")
    parser.add_argument("bundle", help="Path to the OKF bundle directory")
    parser.add_argument("--scope", default="external", help="Namespace prefix (default: external -> evidence/raw/external-okf/)")
    parser.add_argument("--extract-claims", action="store_true", help="Run the compiler extraction on imported concepts")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return import_bundle(args.bundle, args.scope, args.extract_claims, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())