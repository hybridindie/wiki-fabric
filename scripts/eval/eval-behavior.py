#!/usr/bin/env python3
# eval-behavior.py — P4: measure whether the fabric changes agent behavior.
#
# Two modes:
#   default (zero-LLM): assert manifest-level properties per fixture —
#     does the compiled context deliver the required artifacts (patterns,
#     binding decisions) and exclude the required ones (superseded, stale)?
#     Deterministic, 0 tokens, CI-safe.
#   --llm: additionally probe a real model with the assembled prompt and score
#     its compliance (must_contain / must_not_contain). Requires openai pkg.
#
# Metrics (per evaluations/rubric.md):
#   Knowledge Utility = fixtures whose required knowledge was delivered / total
#
# Usage:
#   python3 scripts/eval/eval-behavior.py               # zero-LLM mode (CI-safe)
#   python3 scripts/eval/eval-behavior.py --llm         # also probe a real model
#   python3 scripts/eval/eval-behavior.py --record      # append metrics to registry/log.md
#   python3 scripts/eval/eval-behavior.py --json        # machine report

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import os
import re
import json
import argparse
import shutil
import tempfile
import subprocess
from pathlib import Path
from datetime import date

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

# Eval fixtures + harness code live with the HARNESS (evaluations/, scripts/,
# schemas/); the registry timeline is corpus content. Split homes.
from fabric_config import CORPUS_ROOT as _CORPUS
_HARNESS = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = _HARNESS / "evaluations" / "behavior"


def load_fixture(path):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", path.read_text(encoding="utf-8"), re.DOTALL)
    if not m:
        return {}, ""
    if HAVE_YAML:
        try:
            return (yaml.safe_load(m.group(1)) or {}), m.group(2)
        except Exception:
            return {}, ""
    return {}, m.group(2)


def seed_fabric(tmp, seeds):
    """Copy the harness (scripts/schemas) into a fresh temp fabric, then write seed artifacts."""
    shutil.copytree(_HARNESS / "scripts", tmp / "scripts", dirs_exist_ok=True)
    shutil.copytree(_HARNESS / "schemas", tmp / "schemas", dirs_exist_ok=True)
    for pycache in (tmp / "scripts").glob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)
    (tmp / "registry").mkdir(exist_ok=True)
    (tmp / "registry" / "log.md").write_text("# Log\n\nAppend-only timeline.\n")
    for seed in seeds:
        dest = tmp / "corpus" / seed["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        stem = Path(seed["path"]).stem
        fm_lines = [f"type: {seed['type']}", f"id: {stem}", f"title: {stem}"]
        for k in ("status", "maturity", "review_after", "project"):
            if k in seed and seed[k] is not None:
                fm_lines.append(f"{k}: {seed[k]}")
        dest.write_text("---\n" + "\n".join(fm_lines) + "\n---\n\n" + seed["body"] + "\n")


def compile_manifest(fabric, task, project=None):
    out = subprocess.run(
        [sys.executable, str(fabric / "scripts" / "cmd/context.py"),
         "--task", task, "--format", "json"],
        capture_output=True, text=True, cwd=str(fabric),
        env={**os.environ, "WIKI_FABRIC_DIR": str(fabric)},
    )
    if out.returncode != 0:
        raise RuntimeError(f"context compile failed: {out.stderr}")
    return json.loads(out.stdout)


def assemble_prompt(fabric, manifest):
    """Agent prompt assembled from the manifest (same shape as demo.sh)."""
    parts = [f"# Task\n{manifest['task']}\n", "# Knowledge you must follow (from wiki-fabric)\n"]
    for s in manifest["selected"]:
        text = (fabric / "corpus" / s["path"]).read_text()
        body = text.split("---", 2)[-1].strip() if text.count("---") >= 2 else text
        body = "\n".join(l for l in body.split("\n")
                         if l.strip() and not l.strip().startswith(
                             ("observed_problem:", "intervention:", "outcomes:",
                              "confidence:", "created:", "review_after:", "evidence:")))
        kind = {"decision": "BINDING DECISION", "anti-pattern": "DO NOT",
                "pattern": "PATTERN", "concept": "BACKGROUND",
                "experience-event": "EVIDENCE"}.get(s["type"], s["type"].upper())
        warn = f" ⚠ {s['warning']}" if s.get("warning") else ""
        parts.append(f"## [{kind}] {s.get('title') or s['id']}{warn}\nReason: {s['reason']}\n\n{body}\n")
    parts.append("# Precedence\nProject decisions override domain patterns; domain patterns override global policies.\n")
    return "\n".join(parts)


def zero_llm_checks(fixture, manifest, fabric):
    """Manifest-level compliance checks (no LLM needed)."""
    checks = []
    me = fixture.get("manifest_expectations", {})
    z = fixture.get("zero_llm_check", {})
    stems = {s["stem"] for s in manifest["selected"]}
    excluded = {e["stem"] for e in manifest["excluded"]}

    for want in me.get("must_include_stems", []):
        checks.append({"kind": "delivered", "detail": want, "passed": want in stems})
    for want in me.get("must_exclude_stems", []):
        checks.append({"kind": "excluded", "detail": want, "passed": want in excluded})
    if "must_exclude_stem" in z:
        checks.append({"kind": "excluded", "detail": z["must_exclude_stem"],
                       "passed": z["must_exclude_stem"] in excluded})
    if z.get("binding_decision_in_prompt"):
        checks.append({"kind": "binding_decision", "detail": "a project decision is in the manifest",
                       "passed": any(s["type"] == "decision" for s in manifest["selected"])})
    if "pattern_in_prompt" in z:
        checks.append({"kind": "pattern_delivered", "detail": "a pattern/anti-pattern is in the manifest",
                       "passed": any(s["type"] in ("pattern", "anti-pattern") for s in manifest["selected"])})
    if z.get("banned_terms_in_prompt"):
        prompt = assemble_prompt(fabric, manifest)
        for term in z["banned_terms_in_prompt"]:
            checks.append({"kind": "in_prompt", "detail": term,
                           "passed": term.lower() in prompt.lower()})
    return checks


def llm_probe(fixture, prompt, model=None):
    try:
        from fabric_config import get_llm_config, get_config
        import openai
        cfg = get_llm_config(get_config())
        client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"])
        resp = client.chat.completions.create(
            model=model or cfg["model"],
            messages=[{"role": "user", "content": prompt + f"\n\n# Question\n{fixture['probe']['question']}\n"}],
            max_tokens=400,
        )
        answer = resp.choices[0].message.content or ""
    except Exception as e:
        return {"answer": "", "ok": False, "failures": [f"llm error: {e}"]}
    ok = True
    failures = []
    for term in fixture["probe"].get("must_contain", []):
        if term.lower() not in answer.lower():
            ok = False
            failures.append(f"missing: {term}")
    for term in fixture["probe"].get("must_not_contain", []):
        if term.lower() in answer.lower():
            ok = False
            failures.append(f"banned: {term}")
    return {"answer": answer, "ok": ok, "failures": failures}


def main():
    parser = argparse.ArgumentParser(description="Behavior evaluations: does the fabric change agent behavior?")
    parser.add_argument("--llm", action="store_true", help="Also probe a real model (requires openai pkg + endpoint)")
    parser.add_argument("--model", default=None, help="LLM model override")
    parser.add_argument("--record", action="store_true", help="Append metrics to registry/log.md")
    parser.add_argument("--json", action="store_true", help="JSON report")
    args = parser.parse_args()

    if not HAVE_YAML:
        print("pyyaml required", file=sys.stderr)
        sys.exit(2)

    fixtures = sorted(EVAL_DIR.glob("be*.yaml"))
    if not fixtures:
        print(f"No behavior fixtures found in {EVAL_DIR}", file=sys.stderr)
        sys.exit(2)

    results = []
    for fx_path in fixtures:
        fixture, _ = load_fixture(fx_path)
        if not fixture:
            results.append({"id": fx_path.stem, "ok": False, "checks": [{"kind": "fixture", "detail": "unparseable", "passed": False}]})
            continue
        tmp = Path(tempfile.mkdtemp(prefix="wf-eval."))
        try:
            seed_fabric(tmp, fixture.get("seeds", []))
            manifest = compile_manifest(tmp, fixture["task"])
            checks = zero_llm_checks(fixture, manifest, tmp)
            entry = {
                "id": fixture.get("eval_id", fx_path.stem),
                "title": fixture.get("title", ""),
                "ok": all(c["passed"] for c in checks),
                "checks": checks,
                "selected": [s["stem"] for s in manifest["selected"]],
                "excluded": [f"{e['stem']} ({e['reason']})" for e in manifest["excluded"]],
                "mode": "zero-llm",
            }
            if args.llm:
                prompt = assemble_prompt(tmp, manifest)
                probe = llm_probe(fixture, prompt, args.model)
                entry["probe_ok"] = probe["ok"]
                entry["probe_failures"] = probe["failures"]
                entry["answer_excerpt"] = probe["answer"][:300]
                entry["ok"] = entry["ok"] and probe["ok"]
                entry["mode"] = "llm"
            results.append(entry)
        except Exception as e:
            results.append({"id": fx_path.stem, "ok": False, "checks": [{"kind": "error", "detail": str(e), "passed": False}]})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    utility = passed / total if total else 0.0

    if args.json:
        print(json.dumps({"metrics": {"knowledge_utility": round(utility, 3),
                                      "passed": passed, "total": total},
                          "results": results}, indent=2))
    else:
        print("# Behavior Evaluation\n")
        for r in results:
            mark = "✓" if r["ok"] else "✗"
            print(f"{mark} {r['id']} — {r.get('title', '')}")
            for c in r.get("checks", []):
                cm = "✓" if c["passed"] else "✗"
                print(f"  {cm} {c['kind']}: {c['detail']}")
            for f in r.get("probe_failures", []):
                print(f"    ✗ {f}")
        print()
        print(f"Knowledge Utility: {utility:.0%} ({passed}/{total})")
        if not args.llm:
            print("(zero-LLM mode: manifest-level compliance. Run --llm to probe a real model.)")

    if args.record:
        log = _CORPUS / "registry" / "log.md"
        with open(log, "a") as f:
            f.write(f"\n## {date.today().isoformat()}\n* **eval-behavior | utility {utility:.0%} ({passed}/{total})**\n")
            for r in results:
                f.write(f"- {r['id']}: {'PASS' if r['ok'] else 'FAIL'}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()