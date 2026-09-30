#!/usr/bin/env python3
# paths.py — the single home for "where is the fabric / vault / harness?"
#
# Arch-debt audit (#152): root resolution was implemented seven times
# (fabric_config, dispatch, wiki-fabric.sh, rebuild-index, sync, mcp_server,
# hooks) and "where is the vault?" four times (get_vault_path, dispatch
# _vault_dir, bash vault_dir, vault-refresh) — the copies disagreed (missing
# corpus/ marker, ignored WIKI_FABRIC_VAULT, different fallback chains), so
# status/doctor/refresh could audit DIFFERENT trees on the same machine.
#
# This module ships PURE, parameterized primitives (markers + chain walkers
# that take their anchor as an argument). Import cost: stdlib only — the
# packaged dispatcher may use it without paying the config load. Consumers:
#   - scripts/lib/fabric_config.py  — composes the canonical chain at import
#     (FABRIC_ROOT/CORPUS_ROOT constants); markers are thin aliases of ours
#   - src/wiki_fabric/dispatch.py   — same chain, but its dev-sibling anchor
#     stays its own harness_root() (tests monkeypatch it)
#   - mcp_server / hooks / sync / rebuild-index — thin callers
# Chain semantics live HERE and in fabric_config — one definition, twice
# composed, never re-derived ad hoc.

import os
from pathlib import Path


def is_harness_tree(d):
    """A harness checkout (the tool): runner + cmd scripts. Never a fabric —
    its fabric.yaml is a dev convenience and must not hijack resolution."""
    d = Path(d)
    return (d / "scripts" / "wiki-fabric.sh").exists() and (d / "scripts" / "cmd").is_dir()


def is_fabric_dir(d):
    """A directory that can serve as the fabric root: fabric.yaml, or content
    sitting at its root, or the nested corpus layout. The corpus/ marker is
    load-bearing (dispatch's copy once dropped it — #152)."""
    d = Path(d)
    return ((d / "fabric.yaml").exists()
            or (d / "evidence").exists()
            or (d / "projects").exists()
            or (d / "corpus").exists())


def walk_for_fabric(cwd, skip_harness=True):
    """cwd-walk loop of the fabric chain: nearest ancestor that looks like a
    fabric, breaking on harness trees (their dev fabric.yaml must not
    hijack resolution — sim finding #11)."""
    for d in (Path(cwd), *Path(cwd).parents):
        if skip_harness and is_harness_tree(d):
            break
        if is_fabric_dir(d):
            return d.resolve()
    return None


def xdg_fabric_root():
    """$XDG_DATA_HOME/wiki-fabric (the default install target = the vault)."""
    xdg_data = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    default = Path(xdg_data) / "wiki-fabric"
    return default if default.is_dir() else None


def env_fabric_root():
    """$WIKI_FABRIC_DIR when set AND has content — an empty dir is a pending
    install target, not a fabric (resolving it made status audit an empty
    tree and invent "structure drift"; parity with the bash chain)."""
    env = os.environ.get("WIKI_FABRIC_DIR")
    if env and Path(env).expanduser().is_dir():
        d = Path(env).expanduser().resolve()
        if is_fabric_dir(d) and not _dir_is_empty(d):
            return d
    return None


def _dir_is_empty(d):
    return not any(d.iterdir())


def sibling_vault_of(harness_dir):
    """Dev layout: a vault/ sibling of the harness repo that holds content."""
    sibling = Path(harness_dir).parent / "vault"
    if (sibling / "corpus").exists() or (sibling / "evidence").exists():
        return sibling
    return None


_HAS_CONTENT = ("*.md", "*.json", "*.yaml")


def _dir_has_files(d):
    """A directory holding real content (not a gitkeeped skeleton)."""
    d = Path(d)
    if not d.is_dir():
        return False
    return any(tuple(d.rglob(pat)) for pat in _HAS_CONTENT)


def find_corpus_root(fabric_dir):
    """CORPUS_ROOT resolution: nested corpus/ when it holds content, the
    fabric root itself for the pre-corpus layout (real page files, not an
    empty skeleton — #e2e finding: the harness's gitkeeped evidence/raw made
    the legacy branch match and detached the catalog), else the fresh nested
    path."""
    fabric_dir = Path(fabric_dir)
    corpus = fabric_dir / "corpus"
    if (corpus / "fabric.yaml").exists() or _dir_has_files(corpus / "evidence"):
        return corpus.resolve()
    if _dir_has_files(fabric_dir / "evidence") or _dir_has_files(fabric_dir / "projects"):
        return fabric_dir.resolve()
    return corpus.resolve()


def find_vault_dir_for_fabric(fabric_dir):
    """Vault for a known fabric dir without loading config (dispatch's
    _vault_dir): env override first, then fabric.yaml vault.path, then the
    fabric root itself (the vault IS the fabric — get_vault_path's rule 3)."""
    fabric_dir = Path(fabric_dir)
    env = os.environ.get("WIKI_FABRIC_VAULT")
    if env and env.strip():
        return Path(env.strip()).expanduser().resolve()
    try:
        import yaml
        vp = ((yaml.safe_load((fabric_dir / "fabric.yaml").read_text()) or {})
              .get("vault") or {}).get("path")
        if vp:
            p = Path(str(vp)).expanduser()
            return p if p.is_absolute() else (fabric_dir / p).resolve()
    except Exception:
        pass  # no/invalid vault.path → the layout-aware default (below)
    # layout-aware default — parity with fabric_config._default_vault_root:
    # nested corpus → the generated wiki at corpus/wiki; legacy → sibling vault
    corpus = find_corpus_root(fabric_dir)
    if corpus is not None and corpus.name == "corpus":
        return corpus / "wiki"
    return Path(fabric_dir).parent / "vault"


def find_harness_root():
    """The shipped tool tree. A packaged install carries the harness next to
    this package (src/wiki_fabric/_harness/scripts/...); a dev checkout is
    the repo root (paths.py lives in scripts/lib/, two levels up)."""
    here = Path(__file__).resolve()
    lib = here.parent                              # .../scripts/lib (both layouts)
    if (lib.parent / "wiki-fabric.sh").exists() and (lib.parent / "cmd").is_dir():
        return lib.parent.parent                   # _harness/scripts/lib → _harness
    return here.parent.parent.parent               # dev: the repo root


def find_harness_asset(rel):
    """Resolve a shipped asset relative to the harness tree, packaged or dev."""
    return find_harness_root() / rel