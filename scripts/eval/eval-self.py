#!/usr/bin/env python3
# eval-self.py — the self-contained eval: replay wiki-fabric's OWN PRs against
# a fabric seeded ONLY from wiki-fabric. No live corpus, no other projects.
#
# Why this shape (the lesson from the 2026-10-07 runs): an eval that reaches
# into the real corpus measures "do you have a big corpus", not "does the
# fabric help". This one is hermetic:
#
#   for each recent merged wiki-fabric PR:
#     1. clone wiki-fabric at the PR's BASE commit (the tree as it was BEFORE
#        the work) — so the "knowledge" is what existed when the PR was written
#     2. seed a throwaway fabric with ONLY this repo's docs (README + docs/site)
#        + the harness (scripts/schemas/templates) — nothing else
#     3. ingest those docs (the fabric's normal path: docs → claims)
#     4. compile the context manifest for the PR's task (title + body)
#     5. measure: did the manifest deliver ANY artifact? how much of the PR's
#        own vocabulary is covered? (the recall proxy)
#
# A/B: the SAME PR with the manifest (fabric-informed) vs the bare task text —
# measured on (a) manifest hit + term coverage, and (b) an optional --llm probe
# of whether the assembled prompt contains the PR's key concepts.
#
# Everything is this-project-only and deterministic except the ingest/probe
# LLM calls; the recall metrics themselves are 0-token.
#
# Usage:
#   python3 scripts/eval/eval-self.py --auto 5            # 5 recent merged PRs
#   python3 scripts/eval/eval-self.py --prs 134,135 --llm # + model probe
#   python3 scripts/eval/eval-self.py --auto 5 --json

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import os
import re
import json
import shutil
import argparse
import tempfile
import subprocess
from pathlib import Path
from datetime import date

import layout as _lay
from eval_core import tokens

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SELF_REPO = "hybridindie/wiki-fabric"


def gh(*args):
    """gh call → parsed JSON (list/dict) or None on failure."""
    out = subprocess.run(["gh"] + [str(a) for a in args],
                         capture_output=True, text=True, timeout=120)
    if out.returncode != 0 or not out.stdout.strip():
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return None


def _clean_env(tmp=None):
    """Pin child processes to the seeded fabric: the shell's WIKI_FABRIC_DIR
    must never leak in (it re-pointed every child at the live corpus in the
    2026-10-07 runs), and the seeded tmp IS a harness tree, so the cwd-walk
    breaks on it — an explicit root is the only honest answer."""
    env = dict(os.environ)
    env.pop("WIKI_FABRIC_DIR", None)
    if tmp is not None:
        env["WIKI_FABRIC_DIR"] = str(tmp)
    return env


def pick_prs(repo, n):
    """Recent merged PRs with substantive bodies (deps-bumps skipped)."""
    listing = gh("api", f"repos/{repo}/pulls?state=closed&sort=updated&direction=desc&per_page=50") or []
    picked = []
    for pr in listing:
        title = (pr.get("title") or "").lower()
        body = pr.get("body") or ""
        if (pr.get("merged_at") and "bump" not in title and "⬆" not in title
                and 40 <= len(body) <= 8000):
            picked.append(pr["number"])
        if len(picked) >= n:
            break
    return picked


def fetch_pr(repo, number):
    pr = gh("api", f"repos/{repo}/pulls/{number}")
    if not pr:
        return None
    comments = gh("api", f"repos/{repo}/issues/{number}/comments?per_page=20") or []
    files = gh("api", f"repos/{repo}/pulls/{number}/files?per_page=50") or []
    return {
        "number": number,
        "title": pr.get("title", ""),
        "body": pr.get("body") or "",
        "base_sha": (pr.get("base") or {}).get("sha", ""),
        "merged_at": pr.get("merged_at"),
        "comments": [c.get("body", "") for c in comments],
        "files": [f.get("filename", "") for f in files],
    }


def seed_fabric(tmp, base_sha, repo_clone):
    """A throwaway fabric holding ONLY wiki-fabric: the harness tree + the
    repo's markdown docs at the base commit. The nested-corpus layout the
    resolver expects (config at root, atoms under corpus/)."""
    import layout as _lay
    C = tmp / "corpus"
    # the harness (scripts/schemas/templates/system) so wf runs at all
    for d in ("scripts", "schemas", "templates", "system", "references"):
        if (REPO_ROOT / d).exists():
            shutil.copytree(REPO_ROOT / d, tmp / d, dirs_exist_ok=True)
    for seg in ("patterns", "anti_patterns", "skills", "concepts"):
        _lay.make(C, seg).mkdir(parents=True, exist_ok=True)
    _lay.registry(C).mkdir(parents=True, exist_ok=True)
    (_lay.registry(C) / "log.md").write_text("# Log\n\nAppend-only timeline.\n")
    # the fabric.yaml: wiki-fabric is the ONLY repo
    (tmp / "fabric.yaml").write_text(
        "owner: eval\nllm:\n  base_url: http://localhost:11434/v1\n"
        "  api_key: ollama\n  ops_model: qwen2.5-coder:7b\n"
        "  compiler_model: qwen2.5-coder:7b\n"
        f"repos:\n  wiki-fabric:\n    path: {repo_clone}\n")
    # capture ONLY this repo's docs at the base commit (README + docs/site)
    raw = _lay.evidence_raw(C) / "wiki-fabric"
    raw.mkdir(parents=True, exist_ok=True)
    # the knowledge-dense core only: the ingest is one LLM call per doc, so
    # 40 docs = ~an hour; the eval needs the CONCEPTS, and this handful carries
    # the project's conventions (found timing the 2026-10-07 run: 40min/15docs)
    core = ["README.md", "AGENTS.md",
            "docs/site/architecture.md", "docs/site/why.md",
            "docs/site/configuration.md", "docs/site/cli.md",
            "docs/site/governance.md", "docs/site/machine-contract.md",
            "docs/site/core-workflows.md", "docs/site/context.md"]
    doc_count = 0
    for rel in core:
        doc = repo_clone / rel
        if doc.exists() and doc.stat().st_size < 80_000:
            dest = raw / rel.replace("/", "-")
            if not dest.exists():
                shutil.copy2(doc, dest)
                doc_count += 1
    return doc_count


FIXTURE = REPO_ROOT / "evaluations" / "self" / "fixture"


def install_fixture(C):
    """Install the PRE-INGESTED wiki-fabric knowledge (85 claims from this
    repo's own docs, committed once) into the throwaway fabric. This is the
    whole speed fix: the docs→claims ingest is one LLM call per doc (~5min
    each locally), so it runs ONCE to build the fixture and never again —
    every replay is 0-token after this."""
    if not FIXTURE.exists():
        return 0
    import layout as _lay
    for seg, dest in (("claims", _lay.claims(C)),
                      ("sources", _lay.sources(C)),
                      ("source-summaries", _lay.source_summaries(C))):
        src = FIXTURE / seg
        if not src.exists():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        for f in src.glob("*.md"):
            shutil.copy2(f, dest / f.name)
    return len(list(_lay.claims(C).glob("claim-*.md")))


def ingest_docs(tmp):
    """The fabric's own path: docs → claims (LLM, sha-gated). Only runs on
    the throwaway fabric — this is what the manifest is built from."""
    sp = subprocess.run(
        [sys.executable, str(tmp / "scripts" / "cmd" / "ingest.py"),
         "--changed", "wiki-fabric", "--budget", "40", "--extract-claims"],
        capture_output=True, text=True, cwd=str(tmp), env=_clean_env(tmp),
        timeout=3600)
    claims = list((tmp / "corpus" / "evidence" / "claims").glob("claim-*.md"))
    return len(claims), sp.returncode == 0


def compile_manifest(tmp, task, paths):
    """The fabric's context compiler over the seeded fabric (0 tokens)."""
    cmd = [sys.executable, str(tmp / "scripts" / "cmd" / "context.py"),
           "--task", task, "--project", "wiki-fabric", "--format", "json"]
    for pp in paths:
        cmd += ["--paths", pp]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp),
                         env=_clean_env(tmp), timeout=120)
    try:
        return json.loads(out.stdout)
    except Exception:
        return {"selected": [], "excluded": [], "error": (out.stderr or "")[-160:]}


def score(pr, manifest, fabric):
    """Recall proxy: PR vocabulary covered by the selected artifacts, plus
    the manifest hit (>=1 artifact) and the paths it was asked about."""
    pr_text = f"{pr['title']} {pr['body']} {' '.join(pr.get('comments', [])[:3])}"
    pr_toks = {t for t in tokens(pr_text) if len(t) >= 5}
    croot = (fabric / "corpus") if (fabric / "corpus").exists() else fabric
    sel_text = ""
    for s in manifest.get("selected", []):
        p = croot / s["path"]
        if p.exists():
            sel_text += p.read_text(encoding="utf-8", errors="replace").lower()
    sel_toks = tokens(sel_text)
    covered = pr_toks & sel_toks
    return {
        "selected": [s["stem"] for s in manifest.get("selected", [])][:6],
        "n_selected": len(manifest.get("selected", [])),
        "term_coverage": round(len(covered) / max(len(pr_toks), 1), 3),
        "manifest_hit": bool(manifest.get("selected")),
    }


def llm_probe(task, pr, manifest, fabric, model=None):
    """A/B second half: ask the model the PR's task WITH the assembled manifest
    (fabric-informed) vs bare, and score the PR's key terms in the answer.
    One call per arm. Returns the compliance pair + usage."""
    from fabric_config import get_llm_config, get_config
    import openai
    cfg = get_llm_config(get_config())
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                           timeout=600.0)
    mdl = model or cfg["model"]

    def _ask(prompt):
        # the probe model is the ops model (a coder model) — no reasoning
        # parameter (qwen rejects reasoning_effort; glm accepts it). Send the
        # bare request; if the endpoint is a reasoning model it thinks anyway.
        resp = client.chat.completions.create(
            model=mdl, temperature=0.0, max_tokens=1200,
            messages=[{"role": "user", "content": prompt}])
        msg = resp.choices[0].message
        u = getattr(resp, "usage", None)
        return (msg.content or "", {
            "prompt": int(getattr(u, "prompt_tokens", 0) or 0),
            "completion": int(getattr(u, "completion_tokens", 0) or 0)})

    # the key terms the PR's own diff introduces (symbols + notable nouns)
    key = {t for t in tokens(pr["title"] + " " + " ".join(pr["files"])) if len(t) >= 5}
    croot = (fabric / "corpus") if (fabric / "corpus").exists() else fabric
    ctx = ""
    for s in manifest.get("selected", []):
        p = croot / s["path"]
        if p.exists():
            ctx += p.read_text(encoding="utf-8", errors="replace")[:1500] + "\n"
    q = f"Task: {task}\n\nSummarize the approach you would take, citing the project's own conventions by name."
    fabric_ans, ftok = _ask(f"# Project knowledge\n{ctx}\n\n{q}" if ctx else q)
    bare_ans, btok = _ask(q)
    fit = len(key & tokens(fabric_ans)) / max(len(key), 1)
    bit = len(key & tokens(bare_ans)) / max(len(key), 1)
    return {"fabric_term_hit": round(fit, 3), "bare_term_hit": round(bit, 3),
            "fabric_tokens": ftok, "bare_tokens": btok}


def main():
    ap = argparse.ArgumentParser(description="Self-contained wiki-fabric PR-replay eval")
    ap.add_argument("--repo", default=SELF_REPO)
    ap.add_argument("--prs", default=None, help="comma list of PR numbers")
    ap.add_argument("--auto", type=int, help="pick N recent merged PRs")
    ap.add_argument("--clone", default=None, help="local wiki-fabric clone (default: this repo)")
    ap.add_argument("--llm", action="store_true", help="+ model probe (A/B prompt)")
    ap.add_argument("--ingest", action="store_true",
                    help="re-run the doc ingest to refresh the frozen fixture "
                         "(slow, one LLM call per doc); default uses the fixture")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    nums = ([int(x) for x in args.prs.split(",")] if args.prs
            else (pick_prs(args.repo, args.auto) if args.auto else []))
    if not nums:
        print("No PRs to replay (pass --prs or --auto N)", file=sys.stderr)
        sys.exit(2)

    src_repo = Path(args.clone) if args.clone and Path(args.clone).exists() else REPO_ROOT
    report = {"repo": args.repo, "prs": nums, "replays": []}

    # ONE fabric, seeded from this repo, ingested ONCE. The docs barely change
    # across adjacent PRs, so re-seeding per PR was pure waste (the 2026-10-07
    # 30-min-per-PR runs). The base commit is the OLDEST PR's base — the most
    # conservative "what was known" snapshot — and every PR is scored against it.
    prs = [fetch_pr(args.repo, n) for n in nums]
    prs = [p for p in prs if p]
    if not prs:
        print("No PRs fetched", file=sys.stderr)
        sys.exit(2)
    # the OLDEST PR's base (earliest merged) = the most conservative snapshot
    base = min(prs, key=lambda p: (p.get("merged_at") or ""))["base_sha"]
    tmp = Path(tempfile.mkdtemp(prefix="wf-self."))
    clone = tmp / "repo"
    try:
        subprocess.run(["git", "worktree", "add", "--detach", str(clone), base],
                       cwd=src_repo, capture_output=True)
        if not clone.exists():
            subprocess.run(["git", "clone", "-q", "--no-checkout",
                            f"https://github.com/{args.repo}.git", str(clone)],
                           capture_output=True, timeout=300)
            subprocess.run(["git", "-C", str(clone), "checkout", "-q", base],
                           capture_output=True)
        docs = seed_fabric(tmp, base, clone)
        if args.ingest:
            n_claims, ok = ingest_docs(tmp)      # refresh the fixture (slow)
        else:
            n_claims = install_fixture(tmp / "corpus")  # the frozen 0-token path
            ok = True
        report["fabric"] = {"base_sha": base, "docs": docs, "claims": n_claims}
        for pr in prs:
            try:
                manifest = compile_manifest(tmp, pr["title"], pr["files"])
                scored = score(pr, manifest, tmp)
                entry = {"pr": pr["number"], "task": pr["title"][:90],
                         "docs": docs, "claims": n_claims, "ingest_ok": ok,
                         "files_touched": len(pr["files"]), **scored}
                if args.llm:
                    try:
                        entry["ab"] = llm_probe(pr["title"], pr, manifest, tmp)
                    except Exception as e:
                        entry["ab"] = {"error": str(e)[:160]}
                report["replays"].append(entry)
            except Exception as e:
                report["replays"].append({"pr": pr["number"], "error": str(e)[:200]})
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        subprocess.run(["git", "worktree", "prune"], cwd=src_repo,
                       capture_output=True)

    valid = [r for r in report["replays"] if "error" not in r]
    report["metrics"] = {
        "manifest_hit_rate": round(sum(1 for r in valid if r["manifest_hit"]) / len(valid), 3) if valid else 0,
        "avg_term_coverage": round(sum(r["term_coverage"] for r in valid) / len(valid), 3) if valid else 0,
        "avg_claims": round(sum(r["claims"] for r in valid) / len(valid), 1) if valid else 0,
    }
    if args.llm:
        ab = [r["ab"] for r in valid if "ab" in r and "error" not in r["ab"]]
        if ab:
            report["metrics"]["avg_fabric_term_hit"] = round(sum(x["fabric_term_hit"] for x in ab) / len(ab), 3)
            report["metrics"]["avg_bare_term_hit"] = round(sum(x["bare_term_hit"] for x in ab) / len(ab), 3)

    if args.json:
        print(json.dumps(report, indent=1))
    else:
        print(f"# Self-Eval — {args.repo} (fabric seeded from this repo only)\n")
        for r in report["replays"]:
            if "error" in r:
                print(f"✗ PR #{r['pr']}: {r['error']}")
                continue
            print(f"✓ PR #{r['pr']}: {r['task'][:70]}")
            print(f"    docs {r['docs']} → {r['claims']} claims | "
                  f"manifest: {r['n_selected']} selected | term coverage {r['term_coverage']} "
                  f"| touched-file paths {r['files_touched']}")
            if "ab" in r and "error" not in r["ab"]:
                a = r["ab"]
                print(f"    A/B: term-hit with-fabric {a['fabric_term_hit']} vs bare {a['bare_term_hit']} "
                      f"| tokens {a['fabric_tokens']['prompt']}+{a['fabric_tokens']['completion']} "
                      f"vs {a['bare_tokens']['prompt']}+{a['bare_tokens']['completion']}")
        m = report["metrics"]
        print(f"\nManifest hit rate: {m['manifest_hit_rate']} | avg term coverage: {m['avg_term_coverage']} "
              f"| avg claims: {m['avg_claims']}")
        if "avg_fabric_term_hit" in m:
            print(f"A/B term-hit — with-fabric {m['avg_fabric_term_hit']} vs bare {m['avg_bare_term_hit']}")


if __name__ == "__main__":
    main()