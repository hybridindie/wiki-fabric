#!/usr/bin/env python3
# obsidian_bridge.py — Obsidian Local REST API bridge (#112)
#
# The two-way vault: export writes through the Local REST API when active
# (better transport than file-copy across sync boundaries) and
# harvest_before_export() lands human edits as evidence BEFORE regeneration
# overwrites them (the spike's core finding: wiki/ is regenerated wholesale,
# so unprotected human edits are clobbered).
#
# Gating (graphify pattern): every entry point refuses loudly when the
# integration is off; with it off, export behaves exactly as core docs
# describe. Never load-bearing.
#
# API: https://127.0.0.1:27124 (Local REST API 5.x). Auth: Bearer key from
# the env var named by api_key_env, or the plugin's data.json (inside the
# vault's .obsidian/plugins/obsidian-local-rest-api/ — gitignored content).

import json
import shutil
import urllib.request
import ssl
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from fabric_config import CORPUS_ROOT, get_config

import layout

MANIFEST_PATH = layout.registry(CORPUS_ROOT) / "wiki-export-manifest.json"
HARVEST_DIR_NAME = "obsidian"

# files inside the vault that are generated outputs (export targets)
MANIFEST_SCHEMA = "wiki-fabric/wiki-export-manifest-v1"


def _integration_cfg():
    """The obsidian integration block with defaults applied; None when off."""
    try:
        cfg = get_config()
    except Exception:
        return None
    from fabric_config import get_integrations
    obs = (get_integrations(cfg) or {}).get("obsidian") or {}
    if not obs.get("enabled"):
        return None
    return obs


def _api_url(cfg):
    return str(cfg.get("api_url") or "https://127.0.0.1:27124").rstrip("/")


def _resolve_key(cfg):
    """API key: env var first, then the plugin's data.json in the vault."""
    import os
    key_env = str(cfg.get("api_key_env") or "OBSIDIAN_REST_KEY")
    key = os.environ.get(key_env)
    if key:
        return key, key_env
    # fallback: read from the vault's plugin data (the spike's auth story)
    from fabric_config import get_vault_path
    vault = get_vault_path()
    if vault:
        data = vault / ".obsidian" / "plugins" / "obsidian-local-rest-api" / "data.json"
        if data.exists():
            try:
                k = (json.loads(data.read_text(encoding="utf-8")) or {}).get("apiKey")
                if k:
                    return k, f"data.json:{data}"
            except Exception:
                pass  # data.json absent/corrupt → fall through to env-var key
    return None, key_env


def _request(method, path, api_url, key, body=None, content_type="text/markdown"):
    """One HTTPS request to the Local REST API. Returns (status, text)."""
    url = f"{api_url}/vault/{path}"
    data = body.encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": content_type})
    ctx = ssl._create_unverified_context()  # the plugin's self-signed CA
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:  # TIMEOUT_API tier
        return resp.status, resp.read().decode("utf-8", errors="replace")


def check_server(cfg):
    """Health check (no auth): the server answers / with status OK."""
    try:
        url = f"{_api_url(cfg)}/"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            return data.get("status") == "OK"
    except Exception:
        return False


# === Harvest-before-export (#112c) ========================================

def load_manifest():
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_manifest(manifest):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest["$schema"] = MANIFEST_SCHEMA
    manifest["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")


def harvest_before_export(dry_run=False, project=None):
    """Diff live-vault notes against the last export manifest (#112c).

    A note whose content hash differs from its recorded export-time hash was
    edited by a human after export. Those notes land in
    evidence/raw/<project>/obsidian/ (sha256-gated) BEFORE regeneration —
    the corpus keeps the human edit as evidence; the wiki stays generated
    truth. Returns dict(counts, harvested_paths)."""
    from fabric_config import get_vault_path
    from wf_common import sha256_file
    vault = get_vault_path()
    if not vault:
        return {"harvested": 0, "orphans": 0, "reason": "no vault"}
    wiki_dir = vault / "wiki"
    if not wiki_dir.is_dir():
        return {"harvested": 0, "orphans": 0, "reason": "no wiki"}
    manifest = load_manifest()
    if not manifest:
        # first run with the manifest: baseline it, harvest nothing (the
        # pre-manifest state was machine-generated)
        if not dry_run:
            write_manifest({"files": _hash_wiki(wiki_dir), "orphans": []})
        return {"harvested": 0, "orphans": 0, "reason": "baseline established"}

    recorded = manifest.get("files") or {}
    harvested = []
    orphans = []
    live = _hash_wiki(wiki_dir)
    for rel, h in sorted(live.items()):
        recorded_hash = recorded.get(rel)
        if recorded_hash is None:
            orphans.append(rel)  # in wiki/ but no export step claims it
            continue
        if recorded_hash != h:
            harvested.append(rel)
    if not dry_run:
        if harvested:
            out_dir = layout.evidence_raw(CORPUS_ROOT) / (project or "vault") / HARVEST_DIR_NAME
            out_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            for rel in harvested:
                src = wiki_dir / rel
                dest_name = f"{stamp}-{rel.replace('/', '-')}"
                dest = out_dir / dest_name
                if not dest.exists():
                    shutil.copy(src, dest)
        # re-record whenever the live map differs from the manifest (drift or
        # orphans) — the next diff starts from here
        if live != recorded:
            write_manifest({"files": live, "orphans": orphans})
    return {"harvested": len(harvested), "orphans": len(orphans),
            "harvested_paths": harvested}


def _hash_wiki(wiki_dir):
    """path → sha256 for every md file under wiki/ (sorted, deterministic)."""
    from wf_common import sha256_file
    out = {}
    for p in sorted(wiki_dir.rglob("*.md")):
        out[p.relative_to(wiki_dir).as_posix()] = sha256_file(p)[:16]
    return out


def record_export(wiki_dir):
    """Called after export completes: the manifest now reflects fresh output.
    content_hash (#146): a single digest over all wiki files — the CI no-op
    gate compares it between runs; unchanged ⇒ clean no-op (zero commits)."""
    files = _hash_wiki(wiki_dir)
    content_hash = ""
    if files:
        from hashlib import sha256 as _sha
        blob = "\n".join(f"{k}:{v}" for k, v in sorted(files.items()))
        content_hash = _sha(blob.encode()).hexdigest()[:16]
    write_manifest({"files": files,
                    "orphans": (load_manifest() or {}).get("orphans", []),
                    "content_hash": content_hash})


# === REST write path (#112d) ==============================================

def push_note(rel_path, content, dry_run=False):
    """Write one note through the REST API (204 on success)."""
    cfg = _integration_cfg()
    if cfg is None:
        raise RuntimeError("integrations.obsidian disabled")
    key, _ = _resolve_key(cfg)
    if not key:
        raise RuntimeError(f"no API key: set {cfg.get('api_key_env')} or enable the plugin")
    if dry_run:
        return 204
    status, _ = _request("PUT", rel_path, _api_url(cfg), key, body=content)
    return status


def push_notes(notes, dry_run=False):
    """notes: [(rel_path, content)] — export's write path via REST.
    rel_path is relative to the wiki output dir (fabric's vault:/wiki/), but
    the Obsidian REST API resolves paths relative to the Obsidian vault root
    (#147). When the vault root differs from the wiki dir, prefix the wiki
    dir's name so pushed notes land beside the file-copy tree.
    Returns (written, failed)."""
    prefix = _rest_prefix()
    written = failed = 0
    for rel, content in notes:
        try:
            st = push_note(f"{prefix}/{rel}" if prefix else rel, content, dry_run=dry_run)
            if st in (204, 200):
                written += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  REST write failed for {rel}: {e}", file=sys.stderr)
            failed += 1
    return written, failed


def _rest_prefix(wiki_root=None):
    """Path prefix (relative to the Obsidian vault root) for pushed notes.
    The Obsidian vault root is the dir containing .obsidian (walk up from the
    wiki output dir); if the wiki dir IS the vault root, no prefix. Falls back
    to 'wiki' when fabric.yaml sets a vault: path."""
    vault = get_vault_path()
    wiki = Path(wiki_root) if wiki_root else None
    if wiki is None:
        return "wiki" if vault else ""
    obsidian_ancestor = None
    for anc in [wiki, *wiki.parents]:
        if (anc / ".obsidian").is_dir():
            obsidian_ancestor = anc
            break
    if obsidian_ancestor is None or obsidian_ancestor == wiki:
        return ""  # wiki dir is the vault root — paths are already relative
    return wiki.relative_to(obsidian_ancestor).as_posix()


def get_vault_path(*a, **k):
    """Module-level indirection (tests patch this)."""
    import fabric_config
    return fabric_config.get_vault_path(*a, **k)