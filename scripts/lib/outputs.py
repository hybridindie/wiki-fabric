#!/usr/bin/env python3
"""outputs.py — project outputs discovery (#177 S1, 0 tokens).

\"What this project produces\" has two sources:
  declared:  the overlay's `outputs:` block (curated, human-owned)
  observed:  a deterministic repo-tree scan — package manifests (pyproject/
             package.json/cargo.toml/go.mod), entry-points/console scripts,
             docker-compose services, doc/generated dirs (openwiki/, mkdocs,
             docusaurus), MCP declarations
The union is what the wiki renders as "Produces". Returns a list of
{name, kind, source} dicts (kind: package|cli|image|service|docs|mcp|declared|wiki).
"""

import json
import re
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
from pathlib import Path


DECLARED_KINDS = ("pypi", "npm", "docker", "web", "docs", "mcp", "cli", "binary", "dataset", "other")


def _pyproject_outputs(repo):
    out = []
    pp = repo / "pyproject.toml"
    if not pp.exists():
        return out
    txt = pp.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'^name\s*=\s*"([^"]+)"', txt, re.M)
    if m:
        out.append({"name": m.group(1), "kind": "pypi", "source": "pyproject.toml"})
    # console scripts
    m = re.search(r"\[project\.scripts\]([^\[]*)", txt, re.S)
    if m:
        for line in m.group(1).strip().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                name = line.split("=")[0].strip()
                if name:
                    out.append({"name": name, "kind": "cli", "source": "project.scripts"})
    return out


def _package_json_outputs(repo):
    pj = repo / "package.json"
    if not pj.exists():
        return []
    try:
        d = json.loads(pj.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    out = []
    if d.get("name"):
        out.append({"name": d["name"], "kind": "npm", "source": "package.json"})
    for b in (d.get("bin") or {}):
        out.append({"name": b, "kind": "cli", "source": "package.json bin"})
    return out


def _docker_outputs(repo):
    out = []
    compose = None
    for cand in ("docker-compose.yml", "compose.yml", "docker-compose.yaml", "compose.yaml"):
        if (repo / cand).exists():
            compose = repo / cand
            break
    if compose:
        try:
            import yaml
            d = yaml.safe_load(compose.read_text()) or {}
            for svc in (d.get("services") or {}):
                out.append({"name": svc, "kind": "service", "source": compose.name})
        except Exception:
            pass
    for ff in ("Dockerfile", "Dockerfile.api", "Dockerfile.web"):
        if (repo / ff).exists():
            out.append({"name": ff, "kind": "image", "source": ff})
    return out


def _docs_outputs(repo):
    out = []
    for subdir, label in (("openwiki", "openwiki"), ("docs/site", "docs-site"),
                          ("site", "docs-site"), ("book", "mdbook")):
        if (repo / subdir / "index.md").exists() or (repo / subdir).is_dir() and label == "openwiki" and (repo / subdir / "INSTRUCTIONS.md").exists():
            out.append({"name": subdir, "kind": "docs", "source": subdir + "/"})
    mkdocs = repo / "mkdocs.yml"
    if mkdocs.exists():
        out.append({"name": "mkdocs", "kind": "docs", "source": "mkdocs.yml"})
    return out


def _mcp_outputs(repo):
    """MCP server declarations: pyproject entry-points ending in mcp, the
    fabric's known shape, .mcp.json / mcp.json manifests."""
    out = []
    pp = repo / "pyproject.toml"
    if pp.exists():
        txt = pp.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\[project\.scripts\]([^\[]*)", txt, re.S)
        if m:
            for line in m.group(1).strip().splitlines():
                if re.search(r"mcp", line, re.I) and "=" in line:
                    out.append({"name": line.split("=")[0].strip(), "kind": "mcp", "source": "project.scripts"})
    for cand in (".mcp.json", "mcp.json"):
        if (repo / cand).exists():
            out.append({"name": cand, "kind": "mcp", "source": cand})
    return out


def observed_outputs(repo):
    repo = Path(repo)
    if not repo.is_dir():
        return []
    out = []
    for fn in (_pyproject_outputs, _package_json_outputs, _docker_outputs,
               _docs_outputs, _mcp_outputs):
        try:
            out.extend(fn(repo))
        except Exception:
            pass  # unreadable manifests → skip gracefully
    # dedupe by (name, kind) keeping the first source
    seen = set()
    deduped = []
    for o in out:
        k = (o["name"], o["kind"])
        if k not in seen:
            seen.add(k)
            deduped.append(o)
    return deduped


def declared_outputs(repofm):
    outs = repofm.get("outputs") or []
    if isinstance(outs, dict):
        outs = [{"name": k, **({"kind": v.get("kind", "declared")} if isinstance(v, dict) else {"kind": "declared"})}
                for k, v in outs.items()]
    norm = []
    for o in outs:
        if isinstance(o, str):
            norm.append({"name": o, "kind": "declared", "source": "overlay"})
        elif isinstance(o, dict) and o.get("name"):
            norm.append({**o, "kind": o.get("kind") or "declared", "source": o.get("source") or "overlay"})
    return norm


def effective_outputs(repo, repofm):
    """Declared WINS over observed on name collisions — declared entries are
    curated; the observed scan never clobbers human intent."""
    observed = observed_outputs(repo)
    decl = declared_outputs(repofm)
    by_name = {d["name"]: d for d in decl}
    merged = list(decl)
    for o in observed:
        # the same name with a different kind still renders (observed row)
        if o["name"] not in by_name:
            merged.append(o)
    return merged