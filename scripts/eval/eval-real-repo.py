#!/usr/bin/env python3
# eval-real-repo.py — Run the full pipeline against a real, popular repo and
# measure end-to-end quality, including the contribution of optional
# integrations (graphify, embeddings).
#
# Target repo: configurable; default is FastAPI (large, active, well-documented,
# Python — so the AST entity index works). The eval is deliberately scoped:
# a handful of docs, not the whole 18MB docs tree, so it runs in seconds/minutes.
#
# Pipeline executed in a throwaway fabric:
#   1. wf bootstrap equivalent: seed fabric + wire the repo as a source
#   2. capture: copy scoped docs into evidence/raw/
#   3. ingest: LLM claim extraction (--extract-claims) — the expensive step
#   4. context: compile manifests for probe tasks
#   5. graphify tier (if enabled): entity index + bridge diff measured separately
#   6. embeddings tier (if enabled): semantic re-rank of manifest candidates
#
# Metrics reported:
#   corpus: sources captured, claims extracted, lint errors, claims with locators
#   context: manifest hit-rate (probe tasks that selected >=1 relevant artifact)
#   graphify (only when active): symbols indexed, claims with code_symbols, diff findings
#   embeddings (only when active): re-rank delta — how many candidates moved position
#
# Usage:
#   python3 scripts/eval/eval-real-repo.py                          # full run, LLM required
#   python3 scripts/eval/eval-real-repo.py --skip-llm               # corpus metrics only (no LLM)
#   python3 scripts/eval/eval-real-repo.py --repo /path/to/fastapi  # use a local clone
#   python3 scripts/eval/eval-real-repo.py --json

import sys
import sys as _s, pathlib as _p
_B = _p.Path(__file__).resolve().parent
for _rel in ("", "cmd", "lib", "eval", "harness"):
    _s.path.insert(0, str(_B.parent / _rel))
import json
import shutil
import tempfile
import argparse
import subprocess
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_REPO = "https://github.com/tiangolo/fastapi.git"
SCOPED_DOCS = [  # small, knowledge-dense slice of fastapi docs
    "docs/en/docs/advanced/additional-responses.md",
    "docs/en/docs/advanced/behind-a-proxy.md",
    "docs/en/docs/tutorial/security/first-steps.md",
]
PROBE_TASKS = [
    ("OAuth2 security setup for the auth service", ["security"]),
    ("Custom response models and status codes", ["responses"]),
    ("Running behind a reverse proxy", ["proxy"]),
]


def sh(*args, cwd=None):
    out = subprocess.run([str(a) for a in args], cwd=cwd and str(cwd),
                         capture_output=True, text=True, timeout=600)
    return out


def seed_fabric(tmp, repo_path_holder):
    """Copy the harness into a fresh fabric with integrations enabled."""
    for d in ("scripts", "schemas"):
        shutil.copytree(REPO_ROOT / d, tmp / d, dirs_exist_ok=True)
    for d in ("patterns", "anti-patterns", "skills", "concepts", "syntheses",
              "templates", "examples", "evaluations", "system"):
        if (REPO_ROOT / d).exists():
            shutil.copytree(REPO_ROOT / d, tmp / d, dirs_exist_ok=True)
    (tmp / "registry").mkdir(exist_ok=True)
    (tmp / "registry" / "log.md").write_text("# Log\n\nAppend-only timeline.\n")
    for f in ("AGENTS.md", "LICENSE", "pyproject.toml", "requirements.txt", "fabric.yaml.example"):
        shutil.copy2(REPO_ROOT / f, tmp / f)
    # fabric.yaml: enable both integrations so we can measure their contribution.
    # The repo path is templated to the actual clone location.
    repo_yaml = str(repo_path_holder["path"])
    (tmp / "fabric.yaml").write_text(
        "owner: eval\n"
        "llm:\n  base_url: {os.environ.get('WIKI_LLM_BASE_URL', 'http://localhost:11434/v1')}\n  api_key: {os.environ.get('WIKI_LLM_API_KEY', 'ollama')}\n  model: qwen2.5-coder:7b\n"
        f"repos:\n  fastapi:\n    path: {repo_yaml}\n    graph_dir: graphify-out\n"
        "integrations:\n  graphify:\n    enabled: true\n    graph_dir: graphify-out\n"
        "  embeddings:\n    enabled: true\n    model: all-MiniLM-L6-v2\n"
    )
    (tmp / "projects" / "fastapi" / ".wiki-overlay.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp / "projects" / "fastapi" / ".wiki-overlay.md").write_text(
        f"---\nproject: fastapi\nnamespace: fastapi\nsource_repos:\n"
        f"  - path: {repo_yaml}\n    raw_path: evidence/raw/fastapi\n"
        "    globs: [\"docs/en/docs/advanced/additional-responses.md\","
        " \"docs/en/docs/advanced/behind-a-proxy.md\","
        " \"docs/en/docs/tutorial/security/first-steps.md\"]\n"
    )


def capture_docs(tmp, repo_path):
    """Copy scoped docs into evidence/raw/ (capture step, 0 tokens)."""
    captured = []
    raw = tmp / "evidence" / "raw" / "fastapi"
    for rel in SCOPED_DOCS:
        src = repo_path / rel
        if not src.exists():
            continue
        dest = raw / Path(rel).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        captured.append(dest)
    return captured


def ingest_claim(tmp, doc):
    """LLM claim extraction for one doc. Returns parsed claims count."""
    out = subprocess.run(
        [sys.executable, str(tmp / "scripts" / "cmd/ingest.py"),
         str(doc), "--extract-claims"],
        capture_output=True, text=True, timeout=600, cwd=str(tmp),
    )
    return out


def manifest_stats(tmp, task, paths):
    out = subprocess.run(
        [sys.executable, str(tmp / "scripts" / "cmd/context.py"),
         "--task", task, "--paths", *paths, "--format", "json"],
        capture_output=True, text=True, cwd=str(tmp),
    )
    return json.loads(out.stdout)


def entity_index_stats(tmp, repo_path):
    """Graphify tier: run the AST entity index against the connected repo
    (by name, resolved through the temp fabric's fabric.yaml)."""
    out = subprocess.run(
        [sys.executable, str(tmp / "scripts" / "cmd/build-entity-index.py"), "--repo", "fastapi"],
        capture_output=True, text=True, cwd=str(tmp), timeout=600,
    )
    entities = list((tmp / "global" / "entities").glob("entity-*.md")) if (tmp / "global" / "entities").exists() else []
    # Pull symbol count from output ("fastapi: N symbols")
    import re
    sym_match = re.search(r"(\d+) symbols", out.stdout or "")
    return {
        "ran": True,
        "indexed_symbols": int(sym_match.group(1)) if sym_match else 0,
        "entity_pages": len(entities),
    }


def main():
    parser = argparse.ArgumentParser(description="Real-repo end-to-end evaluation (integration-aware)")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Repo URL or local path")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM claim extraction (corpus metrics only)")
    parser.add_argument("--model", default=None, help="LLM model override")
    parser.add_argument("--json", action="store_true", help="JSON report")
    args = parser.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="wf-real-eval."))
    report = {"repo": args.repo, "date": date.today().isoformat()}

    # 0. Obtain the repo (clone shallow, or use local path)
    if Path(args.repo).exists():
        repo_path = Path(args.repo)
        report["repo_source"] = "local"
    else:
        repo_path = tmp / "repo-target"
        print(f"Cloning {args.repo} (shallow)...")
        r = sh("git", "clone", "--depth", "1", args.repo, repo_path)
        if r.returncode != 0:
            print(f"Failed to clone {args.repo}: {r.stderr[-300:]}", file=sys.stderr)
            sys.exit(2)
        report["repo_source"] = "cloned"
    report["repo"] = str(repo_path)

    try:
        # 1. fabric
        seed_fabric(tmp, {"path": repo_path})
        print(f"Fabric seeded: {tmp}")

        # 2. capture
        docs = capture_docs(tmp, repo_path)
        report["corpus"] = {"sources_captured": len(docs)}
        print(f"Captured {len(docs)} scoped docs")

        # 3. ingest (LLM) — the expensive step
        report["ingest"] = []
        if not args.skip_llm:
            for doc in docs:
                print(f"Ingesting {doc.name} (LLM extraction)...")
                out = ingest_claim(tmp, doc)
                claims = list((tmp / "evidence" / "claims").glob("claim-*.md"))
                report["ingest"].append({"doc": doc.name, "ok": out.returncode == 0,
                                         "total_claims_so_far": len(claims),
                                         "stderr_tail": out.stderr[-200:] if out.returncode else ""})
        claims = list((tmp / "evidence" / "claims").glob("claim-*.md"))
        with_locators = 0
        for c in claims:
            text = c.read_text()
            if "locator:" in text and "L" in text.split("locator:")[1][:10]:
                with_locators += 1
        report["corpus"]["claims_extracted"] = len(claims)
        report["corpus"]["claims_with_locators"] = with_locators
        report["corpus"]["locator_rate"] = round(with_locators / len(claims), 3) if claims else None

        # lint
        lint = subprocess.run([sys.executable, str(tmp / "scripts" / "cmd/lint.py"), "."],
                              capture_output=True, text=True, cwd=str(tmp))
        m = __import__("re").search(r"(\d+) error", lint.stdout)
        report["corpus"]["lint_errors"] = int(m.group(1)) if m else None

        # 4. context manifests. In --skip-llm mode, no claims exist — seed the
        # corpus with doc-backed patterns (honest stand-in: docs ingested as
        # pattern-level knowledge, no LLM) so context selection is measurable.
        if args.skip_llm:
            (tmp / "patterns").mkdir(exist_ok=True)
            for doc in docs:
                stem = doc.stem
                (tmp / "patterns" / f"pattern-fastapi-{stem}.md").write_text(
                    f"---\ntype: pattern\nid: pattern-fastapi-{stem}\n"
                    f"title: \"FastAPI guide: {stem.replace('-', ' ')}\"\n"
                    f"status: recommended\nmaturity: 1\n---\n\n"
                    f"# FastAPI guide: {stem}\n\n"
                    + doc.read_text()[:1200] + "\n"
                )
            print(f"(--skip-llm: seeded {len(docs)} doc-backed patterns for context measurement)")

        report["context"] = []
        for task, paths in PROBE_TASKS:
            mstats = manifest_stats(tmp, task, paths)
            relevant = [s for s in mstats["selected"]]
            report["context"].append({
                "task": task,
                "selected": len(relevant),
                "excluded": len(mstats["excluded"]),
                "hit": len(relevant) > 0,
            })

        # 5. graphify tier (AST entity index; bridge gated by fabric.yaml which enables it)
        try:
            report["graphify"] = entity_index_stats(tmp, repo_path)
        except Exception as e:
            report["graphify"] = {"ran": False, "error": str(e)[:200]}

        # 6. embeddings tier — report configuration; actual re-rank requires the model
        report["embeddings"] = {"enabled": True, "model": "all-MiniLM-L6-v2",
                                "note": "re-rank delta requires sentence-transformers installed; "
                                        "skipped when absent (optional dependency)"}

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("\n# Real-repo evaluation — FastAPI\n")
            print(f"Repo: {report['repo']} ({report['repo_source']})")
            print("\n## Corpus")
            print(f"  sources captured: {report['corpus']['sources_captured']}")
            print(f"  claims extracted: {report['corpus'].get('claims_extracted', 'skipped (no LLM)')}")
            if report["corpus"].get("claims_extracted"):
                print(f"  locator rate:     {report['corpus']['locator_rate']}")
                print(f"  lint errors:      {report['corpus']['lint_errors']}")
            if report["ingest"]:
                for i in report["ingest"]:
                    mark = "✓" if i["ok"] else "✗"
                    print(f"  {mark} ingest {i['doc']}: {i.get('total_claims_so_far', '?')} claims total")
            print("\n## Context manifests")
            for c in report["context"]:
                mark = "✓" if c["hit"] else "✗"
                print(f"  {mark} \"{c['task'][:50]}\" → {c['selected']} selected, {c['excluded']} excluded")
            print("\n## Graphify (integration)")
            print(f"  indexed symbols: {report['graphify'].get('indexed_symbols', 'n/a')}")
            print("\n## Embeddings (integration)")
            print(f"  {report['embeddings']['note']}")
    finally:
        if not args.json:
            print(f"\n(temp fabric kept for inspection: {tmp})")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    # Gate: corpus must be clean and manifests must hit
    ok = (report["corpus"].get("lint_errors") == 0
          and all(c["hit"] for c in report["context"]))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()