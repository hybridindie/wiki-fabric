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
    "You are an engineering agent working in a git checkout of comfyui_mcp "
    "(a Python MCP server project). You complete the assigned task by "
    "editing files and running commands. Work ONLY inside the current "
    "working directory. Bash is your single tool: use it to read files "
    "(cat/sed -n/rg), run the test suite (.venv/bin/pytest), and write "
    "files (heredoc-style). Prefer small verified steps. When the task's "
    "tests pass and the full suite is green, FINISH by replying DONE and "
    "nothing else. Never git commit or push."
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
    """The agent loop: identical shape both arms; arm B's FIRST user prompt
    pre-pends the pinned fabric manifest text. Returns the metrics dict."""
    client, model = _llm()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    user_prompt = task_prompt
    if fabric_context:
        user_prompt = (f"{task_prompt}\n\n"
                       f"# Project knowledge (fabric context manifest)\n"
                       f"{fabric_context}\n\n"
                       f"(This manifest is evidence-backed knowledge about "
                       f"this project; claims carry source locators. Use it "
                       f"where it helps; verify against the code as always.)")
    messages.append({"role": "user", "content": user_prompt})

    m = {"completion_tokens": 0, "reasoning_tokens": 0, "output_tokens": 0,
         "total_spend": 0, "prompt_tokens": 0, "calls": 0, "tool_calls": 0,
         "errored_cmds": 0, "steps": 0}
    t0 = time.time()
    for step in range(step_budget):
        m["steps"] = step + 1
        # the conversation itself is the transcript — saved verbatim
        (run_dir / "transcript.jsonl").open("a").write(
            json.dumps({"step": step, "messages_before_n": len(messages)}) + "\n")
        try:
            with _call_alarm(660):
                resp = client.chat.completions.create(
                    model=model, temperature=TEMPERATURE,
                    messages=messages, max_tokens=4096)
        except Exception as e:
            log(f"  llm error at step {step}: {e}")
            (run_dir / "errors.log").open("a").write(f"step {step}: {e}\n")
            time.sleep(3)
            continue
        msg = resp.choices[0].message
        usage = resp.usage
        total, r_tok, o_tok, total_spend = _usage_estimate(usage, msg)
        m["calls"] += 1
        content = (msg.content or "").strip()
        _u_prompt = int((getattr(usage, "prompt_tokens", None)
                         if not isinstance(usage, dict) else usage.get("prompt_tokens")) or 0)
        m["completion_tokens"] += total
        m["reasoning_tokens"] += r_tok
        m["output_tokens"] += o_tok
        m["total_spend"] += total_spend + _u_prompt
        m["prompt_tokens"] += _u_prompt
        m["reasoning_tokens"] += r_tok
        m["output_tokens"] += o_tok
        m["prompt_tokens"] += _u_prompt
        (run_dir / "transcript.jsonl").open("a").write(
            json.dumps({"step": step, "assistant": content[:4000],
                        "reasoning": (getattr(msg, "reasoning", "") or "")[:4000],
                        "usage": {"completion_api": total, "reasoning_est": r_tok,
                                  "output_api": o_tok, "total_spend_est": total_spend + _u_prompt,
                                  "prompt": _u_prompt}},
                       ensure_ascii=False) + "\n")
        if content.upper().startswith("DONE"):
            break
        # the command extraction: the model's LAST fenced block (```bash … ```)
        # is the action; prose outside fences is ignored. Fallback when no
        # fence: the whole text (the loop's simplicity stays; the fence-first
        # parse was found in the 2026-10-07 dataset — prose-heavy responses
        # were executing narration as bash, burning 20-50 errored cmds/run)
        m["tool_calls"] += 1
        fences = re.findall(r"```(?:bash|sh)?\s*\n(.*?)```", content, re.DOTALL)
        code = (fences[-1] if fences else content).strip("` \n")
        try:
            r = subprocess.run(["bash", "-c", code], cwd=workdir,
                               capture_output=True, text=True, timeout=420)
            out = (r.stdout or "")[-6000:]
            err = (r.stderr or "")[-3000:]
            if r.returncode != 0:
                m["errored_cmds"] += 1
            obs = f"exit={r.returncode}\n--- stdout ---\n{out}\n--- stderr ---\n{err}"
        except subprocess.TimeoutExpired:
            obs = "exit=124 (timed out 420s)"
            m["errored_cmds"] += 1
        (run_dir / "transcript.jsonl").open("a").write(
            json.dumps({"step": step, "cmd": code[:500],
                        "observation": obs[:6000]}) + "\n")
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": obs[:8000]})
    m["wall_seconds"] = round(time.time() - t0, 1)
    return m


def _verify(sandbox, task, run_dir):
    """The gates: new test file passes + full suite green. Both must hold."""
    cmds = [task["verify_new"]]
    if task.get("verify_suite"):
        cmds.append(task.get("suite_cmd") or _suite_cmd(sandbox))
    results = {}
    for c in cmds:
        r = subprocess.run(["bash", "-c", c], cwd=sandbox,
                           capture_output=True, text=True, timeout=900)
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
        # the venv must resolve THIS sandbox's src: the real .venv carries an
        # EDITABLE install .pth of comfyui_mcp → a symlinked venv imports the
        # REAL src (silently testing the wrong tree — found running the eval:
        # the agent's good diffs "failed" because imports never touched the
        # sandbox). A CLONED venv + a re-editable install into the clone is
        # sandbox-scoped: APFS reflink clone (cp -c, ~1s) + pip -e (~3s).
        import subprocess as _sp
        done = _sp.run(["bash", "-c",
                        f"cp -Rc '{venv}' '{work}/.venv' && "
                        f"uv pip install -q -e '{work}' --python '{work}/.venv/bin/python'"],
                       capture_output=True, text=True, timeout=600)
        if done.returncode != 0:
            print(f"  sandbox venv setup FAILED ({done.stderr[-200:]}) — "
                  f"verifies will run against the wrong src (loud, not silent)",
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
                     f"git diff > {run_dir}/produced.diff; git status --porcelain > {run_dir}/status.txt"],
                    cwd=work)
            finally:
                shutil.rmtree(sb, ignore_errors=True)
                subprocess.run(["git", "worktree", "prune"], cwd=Path(t.get("path", cfg["base"]["repo"])),
                               capture_output=True)
            rec = {"arm": arm, "task": t["id"], "repeat": rep, "model":
                   os.environ.get("WIKI_EVAL_MODEL", "glm-5.3-flash:cloud"),
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
                               "model": rec["model"], "repeat": rec.get("repeat", 0)})
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