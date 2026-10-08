#!/usr/bin/env python3
# eval-ab-fabric.py — the A/B: does the fabric change measurable engineering
# behavior? (#185-cycle: the eval the whole loop is built for.)
#
# Protocol (reproducible):
#   - TASK CORPUS: evaluations/ab/tasks.yaml — real comfyui-mcp work, each
#     task's gate = a NEW test file must pass + the full suite must not regress.
#   - ARMS:
#       A ("without"): the task prompt, nothing else.
#       B ("with"):    the task prompt + the FULL text of the pinned context
#                      manifest (evaluations/ab/contexts/<task>.md — generated
#                      once from the fabric corpus, committed as the fixture,
#                      identical bytes for every re-run).
#   - MODEL/HARNESS: identical across arms — one model id
#     (WIKI_EVAL_MODEL, default glm-5.3-flash:cloud via the local
#     OpenAI-compatible endpoint), same system prompt, same tool (run_cmd),
#     same loop shape and step budget.
#   - SANDBOX: a fresh `git worktree`-style clone at the pinned sha per
#     (arm, task) — no shared state, no drift by construction.
#
# MEASURED (the things engineers care about):
#   - thinking tokens / output tokens / total tokens (API usage; the
#     reasoning/output split is a char-proportional estimator, documented)
#   - tool calls (round trips) + errored commands (exit != 0)
#   - task gates: new-test pass + suite pass + wall time
#   - context overhead is ALSO counted for arm B: the manifest's own tokens
#     appear in arm B's first prompt (that's the honest cost of delivery).
#
# Telemetry: one MLFlow run per (arm, task) in experiment wf-ab-engineering-
# tasks + a JSONL mirror per run (self-contained, MLFlow-independent).
#
# Usage:
#   python3 scripts/eval/eval-ab-fabric.py --arms A,B              # the full run
#   python3 scripts/eval/eval-ab-fabric.py --arms B --tasks T2     # one cell
#   python3 scripts/eval/eval-ab-fabric.py --arms A,B --report      # after runs
#
# Reproducibility: every prompt + response is written to the run dir (the
# artifacts ARE the transcript); re-runs with the same model produce
# comparable distributions (sampling temperature is pinned but the model is
# stochastic — run --repeats N for multi-sample medians).

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import os
import re
import json
import time
import shutil
import argparse
import tempfile
import subprocess
from datetime import date
from pathlib import Path

_REPO = _HERE.parent.parent
EVAL_DIR = _REPO / "evaluations" / "ab"
RUNS_ROOT = _REPO / "evaluations" / "ab" / "runs"

SYSTEM_PROMPT = (
    "You are an engineering agent implementing a task in comfyui_mcp "
    "(a Python MCP server project). You CANNOT run commands or read files: "
    "you produce ONE response containing the COMPLETE new contents of every "
    "file the task requires (create or full-replace), in this exact format "
    "per file:\n\n"
    "path/relative/to/repo.py\n"
    "```python\n"
    "<complete file contents>\n"
    "```\n\n"
    "Order files so dependencies come first. Include every new test file the "
    "task names. CONTRACT — PRESERVE each file's full existing public surface "
    "EXACTLY: every current public name (classes, functions, type aliases, "
    "Annotated types, TypeVars, generics declaration forms) must remain "
    "defined with its SAME type/form — other modules in this repo import and "
    "compile those names (pydantic builds schemas from them at import; "
    "TypedDict+Generic declarations must keep their exact form). DO NOT "
    "compact, rename, or reshape existing definitions. Finish "
    "with one line summarizing what you changed. No git commands, no "
    "commentary outside the file blocks."
)

MAX_STEPS = 60
TEMPERATURE = 0.0  # pinned for reproducibility


def _llm():
    from openai import OpenAI
    base = os.environ.get("WIKI_LLM_BASE_URL", "http://localhost:11434/v1")
    key = os.environ.get("WIKI_LLM_API_KEY", "ollama")
    model = os.environ.get("WIKI_EVAL_MODEL", "glm-5.3-flash:cloud")
    return OpenAI(base_url=base, api_key=key, timeout=600.0), model


def _usage_estimate(message_usage, message):
    """(completion_api, reasoning_est, output_api, total_spend_est).
    MEASURED (0.4.6-cycle): this endpoint's usage.completion_tokens counts
    ONLY the final content — the model's reasoning text is EXCLUDED from
    the token accounting (a reasoning-heavy turn ships ~337 chars of
    thinking against a 97-token usage). The split:
      output_tokens = usage.completion_tokens   (the API truth, billed)
      reasoning_est = chars(reasoning)/4        (the documented estimator)
      total_spend   = output + reasoning_est    (the real wall-clock spend)
    Artifacts record BOTH the API truth and the estimate, always labeled."""
    u = message_usage
    completion_api = int((getattr(u, "completion_tokens", None)
                          if not isinstance(u, dict) else u.get("completion_tokens")) or 0)
    reasoning_txt = str(getattr(message, "reasoning", None) or "")
    reasoning_est = round(len(reasoning_txt) / 4)
    return completion_api, reasoning_est, completion_api, completion_api + reasoning_est


import signal as _sig

class _call_alarm:
    """Hard wall-clock watchdog on one LLM call (the ollama proxy has hung
    indefinitely with the client timeout unset-able; 660 > the 600 nominal
    timeout — this is the belt)."""
    def __init__(self, seconds):
        self.seconds = seconds
    def __enter__(self):
        try:
            _sig.signal(_sig.SIGALRM, lambda *a: (_ for _ in ()).throw(
                TimeoutError("llm call watchdog")))
            _sig.alarm(self.seconds)
        except (ValueError, OSError):
            pass  # non-main thread → no alarm available (rare in the runner)
        return self
    def __exit__(self, *a):
        try:
            _sig.alarm(0)
        except Exception:
            pass


def _run_agent(task_prompt, workdir, run_dir, step_budget=MAX_STEPS,
               fabric_context=None, log=print):
    """The SINGLE-CALL protocol (the multi-step loop collapsed here):
    the model receives the task (+ optionally the pinned fabric manifest),
    reads nothing, and emits ONE fenced edit block — the full file contents
    for each file it changes (heredoc-style apply by the RUNNER, not the
    model). Deterministic framing both arms; one usage record each.

    Why single-call: the 2026-10-07 multi-step dataset collapsed to noise —
    DNS-fail storms (ollama.com 502s), prose-executed-as-bash, venv syncing.
    The engineers' question (does the fabric change what the model gets
    RIGHT, and what does the context cost) is answerable at this altitude:
    usage + correctness per call, repeated for medians."""
    client, model = _llm()
    user_prompt = task_prompt
    if fabric_context:
        user_prompt = (f"{task_prompt}\n\n"
                       f"# Project knowledge (fabric context manifest)\n"
                       f"{fabric_context}\n\n"
                       f"(Evidence-backed knowledge about this project — "
                       f"claims carry source locators. Use where it helps; "
                       f"verify against the code as usual.)")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    m = {"completion_tokens": 0, "reasoning_tokens": 0, "output_tokens": 0,
         "total_spend": 0, "prompt_tokens": 0, "calls": 1, "tool_calls": 0,
         "errored_cmds": 0, "steps": 1}
    t0 = time.time()
    try:
        # reasoning_effort pins the thinking budget: the 2026-10-07
        # overnight runs burned 33-35k REASONING tokens per call and the
        # actual edit hit the 32,768 cap before a single file landed
        # (finished_reason=length, zero content). low = none-to-minimal
        # thinking, the edit ships. Recorded per run; medium/low flips are
        # protocol changes (bump --repeats and re-run both arms).
        _effort = os.environ.get("WF_EVAL_REASONING_EFFORT", "low")
        with _call_alarm(660):
            resp = client.chat.completions.create(
                model=model, temperature=TEMPERATURE,
                messages=messages, max_tokens=32768,
                extra_body={"reasoning_effort": _effort})
    except Exception as e:
        log(f"  llm error: {e}")
        (run_dir / "errors.log").open("a").write(f"call: {e}\n")
        m["wall_seconds"] = round(time.time() - t0, 1)
        return m
    msg = resp.choices[0].message
    usage = resp.usage
    total, r_tok, o_tok, total_spend = _usage_estimate(usage, msg)
    content = (msg.content or "").strip()
    _u_prompt = int((getattr(usage, "prompt_tokens", None)
                     if not isinstance(usage, dict) else usage.get("prompt_tokens")) or 0)
    m.update(completion_tokens=total, reasoning_tokens=r_tok,
             output_tokens=o_tok, total_spend=total_spend + _u_prompt,
             prompt_tokens=_u_prompt)
    (run_dir / "transcript.jsonl").open("a").write(json.dumps(
        {"step": 0, "assistant": content[:8000],
         "reasoning": (getattr(msg, "reasoning", "") or "")[:8000],
         "usage": {"completion_api": total, "reasoning_est": r_tok,
                   "output_api": o_tok, "total_spend_est": total_spend + _u_prompt,
                   "prompt": _u_prompt}}, ensure_ascii=False) + "\n")
    # the edit block: ```python fenced FILE blocks with a preceding path line
    import re as _re
    blocks = _re.findall(r"(?:^|\n)(?:#+\s*)?(?:file:\s*)?([\w./-]+\.[a-z]+)\s*\n```\w*\n(.*?)```",
                         content, _re.DOTALL)
    if not blocks:
        # unclosed fence(s): the response hit the token cap mid-file — take
        # each path-line + body-to-next-file (or EOF) rather than nothing
        # (the 2026-10-07 T2 run: a 16k-cap truncation read 'blocks: 0' and
        # threw the whole edit away)
        parts = _re.split(r"(?:^|\n)([\w./-]+\.[a-z]+)\s*\n```\w*\n", content)
        for i in range(1, len(parts) - 1, 2):
            blocks.append((parts[i], parts[i + 1]))
        (run_dir / "apply.log").open("a").write(
            f"truncation fallback engaged: {len(blocks)} partial block(s)\n")
    edits_applied = 0
    for path, body in blocks:
        # sandbox-relative + safe
        rel = str(path).lstrip("./")
        if rel.startswith("/") or ".." in rel:
            continue
        dest = Path(workdir) / rel
        if not str(dest).startswith(str(Path(workdir))):
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")
        edits_applied += 1
    m["edits_applied"] = edits_applied
    (run_dir / "apply.log").write_text(
        f"blocks detected: {len(blocks)}, applied: {edits_applied}\n")
    m["wall_seconds"] = round(time.time() - t0, 1)
    return m


def _verify(sandbox, task, run_dir):
    """The gates: new test file passes + full suite green. Both must hold."""
    cmds = [task["verify_new"]]
    if task.get("verify_suite"):
        cmds.append(task.get("suite_cmd") or _suite_cmd(sandbox))
    results = {}
    import os as _os3
    _env3 = {**_os3.environ, "PYTHONPATH": f"{sandbox}/src"}
    for c in cmds:
        r = subprocess.run(["bash", "-c", c], cwd=sandbox,
                           capture_output=True, text=True, timeout=900,
                           env=_env3)
        results[c] = {"rc": r.returncode,
                      "tail": (r.stdout or "").strip().splitlines()[-1:] and
                              (r.stdout or "").strip().splitlines()[-1]}
    (run_dir / "verify.json").write_text(json.dumps(results, indent=1))
    return all(x["rc"] == 0 for x in results.values()), results


def _suite_cmd(sandbox):
    return ".venv/bin/pytest tests/ -q -m 'not integration'"


def _sandbox(task_cfg, run_name):
    """A throwaway clone at the pinned sha (clean, shared-obj-free)."""
    base = task_cfg["base"]
    sb = Path(tempfile.mkdtemp(prefix=f"wf-ab-{run_name}-"))
    work = sb / "repo"
    repo = Path(base["repo"])
    subprocess.run(["git", "worktree", "add", "--detach", str(work),
                    base["pinned_sha"]], cwd=repo, capture_output=True, check=True)
    # the venv is provisioned as a symlink to the original repo's .venv:
    # identical interpreter/lock both arms, and the 127-verify class (a fresh
    # worktree has no .venv) plus the ~5min uv-sync tax both vanish — the
    # measured variable becomes the WORK, not environment bootstrapping
    venv = repo / ".venv"
    if venv.exists():
        # The venv must import THIS sandbox's src. Three mechanisms failed in
        # sequence (the 2026-10-07 run): a symlinked venv imported the REAL
        # src; a `uv pip -e` reinstall left the editable META-PATH finder
        # winning over everything under pytest (plain python imported the
        # sandbox, pytest the real repo — the maddening case); the surviving
        # deterministic fix: KILL every finder hook in the clone and let
        # PYTHONPATH=sandbox/src drive imports (sys.path, pytest-honored).
        import subprocess as _sp
        done = _sp.run(["bash", "-c",
                        f"cp -Rc '{venv}' '{work}/.venv' && "
                        f"rm -f '{work}/.venv'/lib/python*/site-packages/*.pth "
                        f"'{work}/.venv'/lib/python*/site-packages/__editable__* && "
                        f"rm -rf '{work}/.venv'/lib/python*/site-packages/comfyui_mcp_secure-*.dist-info"],
                       capture_output=True, text=True, timeout=600)
        if done.returncode != 0:
            print(f"  sandbox venv hygiene FAILED ({done.stderr[-160:]})",
                  file=sys.stderr)
    return sb, work


def _cleanup_worktree(sb, work):
    shutil.rmtree(sb, ignore_errors=True)
    subprocess.run(["git", "worktree", "prune"], cwd=Path(work).parent,
                   capture_output=True)


def run_arm(arm, task_ids=None, repeats=1):
    import yaml
    cfg = yaml.safe_load((EVAL_DIR / "tasks.yaml").read_text())
    tasks = cfg["tasks"]
    if task_ids:
        tasks = [t for t in tasks if t["id"] in task_ids]
    stamp = date.today().isoformat()
    results = []
    for t in tasks:
        ctx_file = EVAL_DIR / "contexts" / f"{t['id']}.md"
        fabric_text = ctx_file.read_text(encoding="utf-8") if arm == "B" else None
        for rep in range(repeats):
            rep_s = f"r{rep}" if repeats > 1 else ""
            run_name = f"{arm}-{t['id']}{rep_s and '-' + rep_s}"
            run_dir = RUNS_ROOT / f"{stamp}" / run_name
            if (run_dir / "metrics.json").exists():
                print(f"[{run_name}] already recorded — skip (delete the dir to re-run)")
                f = run_dir / "metrics.json"
                import json as _j2
                results.append(_j2.loads(f.read_text()))
                continue
            run_dir.mkdir(parents=True, exist_ok=True)
            print(f"[{run_name}] sandbox…")
            sb, work = _sandbox(cfg, run_name)
            try:
                print(f"[{run_name}] agent loop ({MAX_STEPS} steps max)…")
                m = _run_agent(t["prompt"], str(work), run_dir,
                               fabric_context=fabric_text)
                print(f"[{run_name}] verify…")
                ok, gates = _verify(work, t, run_dir)
                # record the produced diff for review
                subprocess.run(
                    ["bash", "-c",
                     f"git add -N . 2>/dev/null; git diff > {run_dir}/produced.diff; "
                     f"git status --porcelain > {run_dir}/status.txt"],
                    cwd=work)
            finally:
                shutil.rmtree(sb, ignore_errors=True)
                subprocess.run(["git", "worktree", "prune"], cwd=Path(t.get("path", cfg["base"]["repo"])),
                               capture_output=True)
            rec = {"arm": arm, "task": t["id"], "repeat": rep,
               "model": os.environ.get("WIKI_EVAL_MODEL", "glm-5.3-flash:cloud"),
               "reasoning_effort": os.environ.get("WF_EVAL_REASONING_EFFORT", "low"),
               "gates_pass": ok, "gates": gates, **m}
            (run_dir / "metrics.json").write_text(json.dumps(rec, indent=1))
            _log_mlflow(rec, run_name)
            results.append(rec)
            print(f"[{run_name}] {'PASS' if ok else 'FAIL'} — tokens {m['completion_tokens']} "
                  f"(think~{m['reasoning_tokens']}, out~{m['output_tokens']}), "
                  f"cmds {m['tool_calls']} (err {m['errored_cmds']}), {m['wall_seconds']}s")
    return results


def _log_mlflow(rec, run_name):
    try:
        import mlflow
        mlflow.set_tracking_uri(os.environ.get(
            "MLFLOW_TRACKING_URI", "https://mlflow.johndstudios.net"))
        mlflow.set_experiment("wf-ab-engineering-tasks")
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params({"arm": rec["arm"], "task": rec["task"],
                               "model": rec["model"], "repeat": rec.get("repeat", 0),
                               "reasoning_effort": rec.get("reasoning_effort", "low")})
            mlflow.log_metrics({
                "completion_tokens_api": rec["completion_tokens"],
                "reasoning_tokens_est": rec["reasoning_tokens"],
                "output_tokens_api": rec["output_tokens"],
                "prompt_tokens": rec["prompt_tokens"],
                "total_spend_est": rec["total_spend"],
                "total_tokens_api": rec["prompt_tokens"] + rec["completion_tokens"],
                "tool_calls": rec["tool_calls"],
                "errored_cmds": rec["errored_cmds"],
                "steps": rec["steps"],
                "wall_seconds": rec["wall_seconds"],
                "gates_pass": 1.0 if rec["gates_pass"] else 0.0,
            })
            run = mlflow.active_run()
            (RUNS_ROOT / "mlflow-index.jsonl").open("a").write(
                json.dumps({"run": run_name, "mlflow_run_id": run.info.run_id,
                            "arm": rec["arm"], "task": rec["task"],
                            "gates_pass": rec["gates_pass"]}) + "\n")
    except Exception as e:
        print(f"  (mlflow log failed: {e} — JSONL mirror intact)", file=sys.stderr)


def report():
    import json as _json
    rows = {}
    for f in sorted(RUNS_ROOT.rglob("metrics.json")):
        d = _json.loads(f.read_text())
        rows[f.parent.name] = d
    if not rows:
        print("no runs recorded yet (evaluations/ab/runs/ is empty)")
        return
    # the comparison table: per task x arm medians (repeat-aware)
    agg = {}
    for name, d in rows.items():
        key = (d["arm"], d["task"])
        agg.setdefault(key, []).append(d)
    def _med(xs, k):
        xs = sorted(x[k] for x in xs)
        return xs[len(xs) // 2]
    print(f"{'task':34} {'arm':4} {'pass':5} {'output':>7} {'think~':>7} "
          f"{'spend~':>8} {'cmds':>5} {'err':>4} {'sec':>7}")
    for (arm, task), xs in sorted(agg.items()):
        print(f"{task:34} {arm:4} {'yes' if any(x['gates_pass'] for x in xs) else 'no':5} "
              f"{_med(xs, 'output_tokens'):7} {_med(xs, 'reasoning_tokens'):7} "
              f"{_med(xs, 'total_spend'):8} {_med(xs, 'tool_calls'):5} "
              f"{_med(xs, 'errored_cmds'):4} {_med(xs, 'wall_seconds'):7}")
    # the deltas
    tasks = sorted({t for _, t in agg})
    if all((a, t) in agg for a in ("A", "B") for t in tasks):
        print()
        print(f"{'task':34} {'pass delta':>10} {'tok delta':>10} {'cmd delta':>10}")
        for t in tasks:
            a, b = agg[("A", t)], agg[("B", t)]
            pa = any(x["gates_pass"] for x in a)
            pb = any(x["gates_pass"] for x in b)
            td = _med(b, "total_spend") - _med(a, "total_spend")
            cd = _med(b, "tool_calls") - _med(a, "tool_calls")
            print(f"{t:34} {str(pa) + '->' + str(pb):>10} {td:+10} {cd:+10}")


def main():
    ap = argparse.ArgumentParser(description="A/B eval: fabric-informed vs bare")
    ap.add_argument("--arms", default="A,B", help="comma list: A (without), B (with)")
    ap.add_argument("--tasks", default=None, help="comma list of task ids (default: all)")
    ap.add_argument("--repeats", type=int, default=1, help="samples per cell (medians)")
    ap.add_argument("--report", action="store_true", help="print the comparison table only")
    args = ap.parse_args()
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    if args.report:
        report()
        return
    task_ids = [t for t in (args.tasks or "").split(",") if t] or None
    out = []
    for arm in [a.strip() for a in args.arms.split(",") if a.strip()]:
        out.extend(run_arm(arm, task_ids, args.repeats))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()