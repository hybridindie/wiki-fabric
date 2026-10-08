#!/usr/bin/env python3
# eval-pr-replay.py — Replay real PRs from an active repo and measure whether
# the fabric would have helped at the time the PR was written.
#
# The idea (knowledge-recall eval on real work):
#   For each replayed PR:
#     1. Fetch the PR (title, body, comments, touched files) via gh
#     2. Seed a fabric with knowledge from the repo's docs AS OF BEFORE the PR
#        (approximately: docs on the parent commit)
#     3. Compile a context manifest for the PR's task ("fix X in Y")
#     4. Measure:
#        - manifest hit: did the fabric deliver ANY relevant knowledge?
#        - term coverage: how much of the PR's own vocabulary (title+body)
#          appears in the selected artifacts? (recall proxy)
#        - graphify contribution: did the AST index cover the touched files?
#        - time-to-compile: manifest latency (should be ~0)
#
# This is a *recall* eval: we replay work that already happened and ask whether
# the fabric would have surfaced knowledge relevant to it. It cannot assert the
# agent's final decision (that needs --llm probing), but it measures the
# retrieval layer on real-world vocabulary.
#
# Usage:
#   python3 scripts/eval/eval-pr-replay.py --repo tiangolo/fastapi --prs 16192,15999
#   python3 scripts/eval/eval-pr-replay.py --repo tiangolo/fastapi --auto 3   # pick 3 recent merged PRs
#   python3 scripts/eval/eval-pr-replay.py ... --json

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import os
import json
import shutil
import tempfile
import argparse
import subprocess
from pathlib import Path
from datetime import date
from eval_core import tokens

import layout

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def gh(*args):
    out = subprocess.run(["gh"] + [str(a) for a in args], capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout) if out.stdout.strip() else None
    except json.JSONDecodeError:
        return None


def fetch_pr(repo, number):
    pr = gh("api", f"repos/{repo}/pulls/{number}")
    if not pr:
        return None
    comments = gh("api", f"repos/{repo}/issues/{number}/comments?per_page=20") or []
    files = gh("api", f"repos/{repo}/pulls/{number}/files?per_page=20") or []
    return {
        "number": number,
        "title": pr.get("title", ""),
        "body": pr.get("body") or "",
        "merged_at": pr.get("merged_at"),
        "comments": [c.get("body", "") for c in comments],
        "files": [f.get("filename", "") for f in files],
        "patches": {f.get("filename"): (f.get("patch") or "") for f in files},
    }


def seed_fabric(tmp, repo, pr, repo_clone, graphify=False):
    """Fresh harness + docs captured from the repo clone + PR thread as raw."""
    # the NESTED-CORPUS layout (the resolver's default): config at the root,
    # content atoms under corpus/ — the flat layout died when the resolver
    # moved to vault/corpus (the seed wrote tmp/evidence/raw and the walker
    # read tmp/vault/corpus: selected=0 forever, found in the comfyui replay)
    _C = tmp / "corpus"
    shutil.copytree(REPO_ROOT / "scripts", tmp / "scripts", dirs_exist_ok=True)
    shutil.copytree(REPO_ROOT / "schemas", tmp / "schemas", dirs_exist_ok=True)
    import layout as _lay
    for d in ("patterns", "anti_patterns", "skills", "concepts"):
        _lay.make(_C, d).mkdir(parents=True, exist_ok=True)
    if graphify:
        # enable graphify and index the repo's code (AST entity pages)
        (tmp / "fabric.yaml").write_text(
            f"owner: replay\nrepos:\n  {repo.split('/')[-1]}:\n    path: {repo_clone}\n"
            "integrations:\n  graphify:\n    enabled: true\n"
        )
        subprocess.run(
            [sys.executable, str(tmp / "scripts" / "cmd/build-entity-index.py")],
            capture_output=True, text=True, cwd=str(tmp), timeout=600,
            env=_clean_env(tmp),
        )
    import layout as _lay
    _lay.registry(_C).mkdir(parents=True, exist_ok=True)
    (_lay.registry(_C) / "log.md").write_text("# Log\n\nAppend-only timeline.\n")

    if not (tmp / "fabric.yaml").exists():
        (tmp / "fabric.yaml").write_text(
            f"owner: replay\nrepos:\n  {repo.split('/')[-1]}:\n    path: {repo_clone}\n")
    # capture scoped docs from the clone (fastapi: docs slice)
    raw = _lay.evidence_raw(_C) / repo.split("/")[-1]
    raw.mkdir(parents=True, exist_ok=True)
    doc_count = 0
    for doc in sorted(repo_clone.rglob("*.md")):
        rel = str(doc.relative_to(repo_clone))
        # small, knowledge-dense docs only
        if any(s in rel for s in ("docs/", "README")) and doc.stat().st_size < 30_000:
            dest = raw / rel.replace("/", "-")
            if not dest.exists():
                shutil.copy2(doc, dest)
                doc_count += 1
        if doc_count >= 25:
            break

    # PR thread itself as raw evidence (the replayed work)
    pr_dir = raw / "git"
    pr_dir.mkdir(parents=True, exist_ok=True)
    comments_md = "\n\n".join(f"### comment\n{c}" for c in pr["comments"])
    (pr_dir / f"pr-{pr['number']}.md").write_text(
        f"# PR #{pr['number']}: {pr['title']}\n\n## Description\n\n{pr['body']}\n\n"
        f"## Discussion\n\n{comments_md}\n\n## Files touched\n\n"
        + "\n".join(f"- {f}" for f in pr["files"])
    )
    # corpus claims exist BEFORE the replay measures: a fabric with captured
    # docs but zero claims delivers an empty manifest (found in the comfyui
    # replay: selected=0 everywhere). The PR thread must NOT be in this
    # ingest — the replay's after-ingest tier measures exactly the delta its
    # claims produce. Alphabetical budget ordering did NOT keep git/ last
    # (it landed inside the first 25 in one run — the 0-claims class), so the
    # thread directory is PARKED outside the vault for the corpus ingest and
    # moved back: its record stays absent until ingest_pr_thread creates it.
    import subprocess as _sp
    git_dir = raw / "git"
    git_parked = tmp / "_pr_thread_parked"
    if git_dir.exists():
        shutil.move(str(git_dir), str(git_parked))
    if os.environ.get("WF_REPLAY_INGEST", "") == "1":
        _sp.run([sys.executable, str(tmp / "scripts" / "cmd/ingest.py"),
             "--changed", repo.split("/")[-1], "--budget", "100",
             "--extract-claims"],
            capture_output=True, text=True, cwd=str(tmp), timeout=1800,
            env=_clean_env(tmp))
    if git_parked.exists():
        shutil.move(str(git_parked), str(git_dir))
        return doc_count



def _pr_git_dir(tmp):
    """The slug dir seed_fabric used for this fabric's raw/git (underscore
    fold: comfyui_mcp as captured)."""
    import glob as _g
    cands = _g.glob(str(tmp / "corpus" / "evidence" / "raw" / "*"))
    for c in cands:
        if Path(c).is_dir() and (Path(c) / "git").exists():
            return Path(c).name
    return Path(cands[0]).name if cands else "comfyui_mcp"


def _clean_env(tmp=None):
    """Pin the children to THIS replay's fabric. Two failure classes found
    in the comfyui replay (2026-10-07): (a) a leaked WIKI_FABRIC_DIR from
    the outer shell pointed every child at the LIVE corpus (the alpaca
    claims in the manifests were the give-away), (b) the seeded tmp IS a
    harness tree (scripts/wiki-fabric.sh copied with the seed) so the
    cwd-walk breaks on it — the resolver's fallback (tmp.parent/'vault')
    answered instead. Explicit WIKI_FABRIC_DIR is the only honest answer;
    the corpus lives under tmp/corpus (the nested layout the resolver
    applies to pinned roots)."""
    env = dict(os.environ)
    env.pop("WIKI_FABRIC_DIR", None)
    if tmp is not None:
        env["WIKI_FABRIC_DIR"] = str(tmp)
    return env


def compile_manifest(tmp, task, paths):
    cmd = [sys.executable, str(tmp / "scripts" / "cmd/context.py"),
           "--task", task, "--format", "json"]
    for pp in paths:
        cmd += ["--paths", pp]
    out = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp),
                         env=_clean_env(tmp))
    return json.loads(out.stdout)


def ingest_pr_thread(tmp, pr):
    """--llm tier: LLM-extract claims from the PR thread (the replay's delta
    measurement: the corpus claims exist at seed; the PR thread's claims are
    the AFTER tier). Count scoped to THIS PR's thread claims."""
    src = (tmp / "corpus" / "evidence" / "raw" /
           _pr_git_dir(tmp) / "git") / f"pr-{pr['number']}.md"
    if not src.exists():
        print(f"  (pr-thread source file MISSING: {src})", file=sys.stderr)
        return 0, False
    out = subprocess.run(
        [sys.executable, str(tmp / "scripts" / "cmd/ingest.py"), str(src), "--extract-claims"],
        capture_output=True, text=True, cwd=str(tmp), timeout=900,
        env=_clean_env(tmp),
    )
    if out.returncode != 0:
        print(f"  (pr-thread ingest FAILED: {(out.stderr or '')[-220:]})", file=sys.stderr)
    claims_dir = tmp / "corpus" / "evidence" / "claims"
    pr_new = list(claims_dir.glob("claim-*-git-pr-*.md"))
    all_claims = list(claims_dir.glob("claim-*.md"))
    print(f"  pr-thread ingest: rc={out.returncode} "
          f"pr-claims={len(pr_new)} all-claims={len(all_claims)}")
    return len(pr_new), out.returncode == 0


def score_pr(pr, manifest, fabric):
    """Recall scoring: PR vocabulary vs manifest-selected artifacts."""
    pr_text = f"{pr['title']} {pr['body']} {' '.join(pr['comments'][:3])}"
    pr_toks = tokens(pr_text)

    selected_text = ""
    for s in manifest["selected"]:
        # manifest paths are CORPUS-relative (the layout contract): join the
        # corpus, not the fabric root (flat tmp join → nothing exists →
        # term coverage reads 0.0 forever — the silent scorer-killer)
        _croot = (fabric / "corpus") if (fabric / "corpus").exists() else fabric
        p = _croot / s["path"]
        if p.exists():
            selected_text += p.read_text().lower()
    sel_toks = tokens(selected_text)

    meaningful = {t for t in pr_toks if len(t) >= 5}
    covered = meaningful & sel_toks
    coverage = round(len(covered) / len(meaningful), 3) if meaningful else 0.0

    # graphify tier: did the AST index cover the touched files?
    entities_dir = layout.make(fabric, "global") / "entities"
    entity_pages = list(entities_dir.glob("entity-*.md")) if entities_dir.exists() else []
    touched_covered = 0
    for f in pr["files"]:
        slug_part = Path(f).stem.lower()
        if any(slug_part[:20] in e.name for e in entity_pages):
            touched_covered += 1

    return {
        "pr_terms": len(meaningful),
        "covered_terms": len(covered),
        "term_coverage": coverage,
        "selected": [s["stem"] for s in manifest["selected"]],
        "entity_pages": len(entity_pages),
        "touched_files_covered_by_entities": touched_covered,
    }


def main():
    parser = argparse.ArgumentParser(description="Replay real PRs: would the fabric have helped?")
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--prs", help="Comma-separated PR numbers to replay")
    parser.add_argument("--auto", type=int, help="Auto-pick N recent merged PRs with substantive bodies")
    parser.add_argument("--clone", help="Local clone of the repo (docs source); clones shallowly if omitted")
    parser.add_argument("--llm", action="store_true", help="Also ingest the PR thread with LLM claim extraction and measure coverage delta")
    parser.add_argument("--json", action="store_true", help="JSON report")
    parser.add_argument("--fabric-live", action="store_true",
                        help="Score against the LIVE fabric's existing knowledge "
                             "for this repo (0 tokens, seconds) instead of a "
                             "seeded throwaway fabric")
    args = parser.parse_args()

    # Pick PRs
    pr_numbers = []
    if args.prs:
        pr_numbers = [int(x) for x in args.prs.split(",")]
    elif args.auto:
        listing = gh("api", f"repos/{args.repo}/pulls?state=closed&sort=updated&direction=desc&per_page=40") or []
        picked = []
        for pr in listing:
            title = (pr.get("title") or "").lower()
            is_bump = "bump" in title or "⬆" in title
            if pr.get("merged_at") and not is_bump and (pr.get("body") or "") and 50 <= (pr.get("body") or "").__len__() <= 6000:
                picked.append(pr["number"])
            if len(picked) >= args.auto:
                break
        pr_numbers = picked
    if not pr_numbers:
        print("No PRs to replay (pass --prs or --auto N)", file=sys.stderr)
        sys.exit(2)

    # Clone for docs source
    tmp_repo = None
    if args.clone and Path(args.clone).exists():
        repo_clone = Path(args.clone)
    else:
        tmp_repo = Path(tempfile.mkdtemp(prefix="wf-pr-clone."))
        repo_clone = tmp_repo / "src"
        print(f"Cloning {args.repo} (shallow, docs only context)...")
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"https://github.com/{args.repo}.git", str(repo_clone)],
                       capture_output=True, text=True, timeout=300)
        if not repo_clone.exists():
            print("Clone failed", file=sys.stderr)
            sys.exit(2)

    report = {"repo": args.repo, "prs": pr_numbers, "replays": []}
    try:
        for n in pr_numbers:
            pr = fetch_pr(args.repo, n)
            if not pr:
                report["replays"].append({"pr": n, "error": "fetch failed"})
                continue
            if pr.get("merged_at"):
                report.setdefault("merged", 0)
                report["merged"] += 1

            tmp = Path(tempfile.mkdtemp(prefix="wf-replay."))
            try:
                doc_count = seed_fabric(tmp, args.repo, pr, repo_clone, graphify=True)
                task = pr["title"].lstrip("🐛 ⬆ 📝 ✨ ").strip()

                # base manifest (no claims yet)
                manifest = compile_manifest(tmp, task, pr["files"])
                scored = score_pr(pr, manifest, tmp)
                entry = {
                    "pr": n,
                    "task": task[:80],
                    "docs_captured": doc_count,
                    "files_touched": len(pr["files"]),
                    **scored,
                }

                # --llm tier: ingest the PR thread, re-compile, measure delta
                if args.llm:
                    n_claims, ok = ingest_pr_thread(tmp, pr)
                    manifest2 = compile_manifest(tmp, task, pr["files"])
                    scored2 = score_pr(pr, manifest2, tmp)
                    entry["llm_claims_extracted"] = n_claims
                    entry["ingest_ok"] = ok
                    entry["after_ingest"] = {
                        "selected": scored2["selected"],
                        "term_coverage": scored2["term_coverage"],
                        "coverage_delta": round(scored2["term_coverage"] - scored["term_coverage"], 3),
                    }
                report["replays"].append(entry)
            except Exception as e:
                report["replays"].append({"pr": n, "error": str(e)[:200]})
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

        # aggregate
        valid = [r for r in report["replays"] if "error" not in r]
        llm_runs = [r for r in valid if "after_ingest" in r]
        report["metrics"] = {
            "avg_term_coverage": round(sum(r["term_coverage"] for r in valid) / len(valid), 3) if valid else 0,
            "manifest_hit_rate": round(sum(1 for r in valid if r["selected"]) / len(valid), 3) if valid else 0,
            "total_entity_pages": max((r["entity_pages"] for r in valid), default=0),
            "touched_file_coverage": round(sum(r["touched_files_covered_by_entities"] for r in valid)
                                            / max(sum(r["files_touched"] for r in valid), 1), 3) if valid else 0,
            "llm_coverage_delta": round(sum(r["after_ingest"]["coverage_delta"] for r in llm_runs) / len(llm_runs), 3) if llm_runs else None,
        }

        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"# PR Replay Evaluation — {args.repo}\n")
            for r in report["replays"]:
                if "error" in r:
                    print(f"✗ PR #{r['pr']}: {r['error']}")
                    continue
                print(f"✓ PR #{r['pr']}: {r['task']}")
                print(f"    term coverage: {r['term_coverage']} ({r['covered_terms']}/{r['pr_terms']} PR terms in manifest)")
                print(f"    selected: {', '.join(r['selected'][:4]) or '(none)'}")
                print(f"    entity pages: {r['entity_pages']}, touched-file coverage: {r['touched_files_covered_by_entities']}/{r['files_touched']}")
                if "after_ingest" in r:
                    ai = r["after_ingest"]
                    print(f"    after LLM ingest ({r['llm_claims_extracted']} claims): coverage {ai['term_coverage']} (Δ {ai['coverage_delta']:+}) selected: {', '.join(ai['selected'][:4]) or '(none)'}")
            m = report["metrics"]
            print(f"\nManifest hit rate: {m['manifest_hit_rate']:.0%} | avg term coverage: {m['avg_term_coverage']} | entity coverage of touched files: {m.get('touched_file_coverage')}")
            if m.get("llm_coverage_delta") is not None:
                print(f"LLM-ingest coverage delta: {m['llm_coverage_delta']:+}")
            print(f"(term coverage = share of the PR's own vocabulary present in selected artifacts — a recall proxy)")
    finally:
        if tmp_repo and tmp_repo.exists():
            shutil.rmtree(tmp_repo, ignore_errors=True)


if __name__ == "__main__":
    main()