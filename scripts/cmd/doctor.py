#!/usr/bin/env python3
# doctor.py — Environment diagnosis: surface drift BEFORE a gate blocks on it.
#
# Usage:
#   wf doctor                     # human report
#   wf doctor --json              # machine report (CI/harness)
#
# Checks (each independent; a failure in one never hides another):
#   1. endpoint reachability + model inventory
#   2. llm.model / llm.compiler_model resolve against the endpoint
#   3. compiler eval recorded for the current compiler model (G4 gate readiness)
#   4. judgment tier: enabled? route backend available? emulator-only?
#   5. vault structure freshness (delegates to vault-refresh --check)
#   6. registry log: exists + parseable (the corpus timeline the G4 gate reads)
#   7. HITL gate: pending decisions surfaced
#
# Philosophy: doctor never mutates. It names the drift and the one command
# that fixes it — the same discipline as wf status, deeper.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import json
import os
import urllib.request
from pathlib import Path

from fabric_config import FABRIC_ROOT, CORPUS_ROOT, get_config, get_llm_config


def check_result(name, passed, detail, fix=None):
    return {"check": name, "passed": passed, "detail": detail, "fix": fix}


def endpoint_models(base_url, api_key, timeout=10):
    """List model ids from the OpenAI-compatible endpoint; None on failure."""
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            d = json.loads(resp.read().decode())
        return [m["id"] for m in d.get("data", [])]
    except Exception:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Diagnose fabric environment drift (no mutations)")
    parser.add_argument("--json", action="store_true", help="Machine report")
    args = parser.parse_args()

    results = []

    # ---- 1. endpoint + model inventory ----
    llm = get_llm_config(get_config())
    base_url = llm.get("base_url", "")
    api_key = llm.get("api_key", "")
    models = endpoint_models(base_url, api_key)
    if models is None:
        results.append(check_result(
            "endpoint", False, f"unreachable: {base_url}",
            fix="start the endpoint (e.g. ollama serve) or fix llm.base_url in fabric.yaml"))
    else:
        results.append(check_result(
            "endpoint", True, f"{base_url} — {len(models)} models served"))

        # ---- 2. ops model resolves
        ops_model = llm.get("model", "")
        ops_ok = ops_model in models
        results.append(check_result(
            "llm.model", ops_ok,
            (f"resolved: {ops_model}" if ops_ok
             else f"phantom: {ops_model!r} not served by the endpoint"),
            fix=f"set llm.model to a served model, or pull it (e.g. ollama pull {ops_model})"))

        # ---- 3. compiler model resolves (the #43 finding: phantom defaults block gates)
        compiler = get_llm_config(get_config(), compiler=True).get("model", "")
        compiler_ok = compiler in models
        results.append(check_result(
            "compiler_model", compiler_ok,
            (f"resolved: {compiler}" if compiler_ok
             else f"phantom: {compiler!r} not served — the G4/promotion gates WILL block on eval for it"),
            fix="set llm.compiler_model to a served model in fabric.yaml"))
        if compiler_ok:
            # ---- 4. compiler eval recorded (gate readiness)
            try:
                from fabric_config import compiler_eval_recorded
                ok, why = compiler_eval_recorded(get_config())
                results.append(check_result(
                    "compiler_eval", ok,
                    why if ok else f"{compiler} has no recorded PASS eval — "
                    "mine/promote will refuse",
                    fix=f"python3 scripts/eval/eval-stability.py --models {compiler} --record"))
            except Exception as e:
                results.append(check_result("compiler_eval", False, f"check failed: {e}"))

    # ---- 4. judgment tier visibility
    try:
        from judgment import judgment_config, is_judgment_active, laya_available
        jcfg = judgment_config(get_config())
        active = is_judgment_active()
        if not active:
            results.append(check_result(
                "judgment_tier", True,
                "disabled (opt-in) — enable via integrations.judgment.enabled",
                fix="integrations.judgment: {enabled: true, route: local, local_backend: laya}"))
        else:
            route = jcfg.get("route")
            if route == "cloud":
                has_key = bool(os.environ.get("TYPESAFE_API_KEY"))
                results.append(check_result(
                    "judgment_tier", has_key,
                    f"enabled, route=cloud — TYPESAFE_API_KEY {'set' if has_key else 'NOT set'}",
                    fix="export TYPESAFE_API_KEY (cloud route)"))
            else:
                laya = laya_available()
                if laya:
                    results.append(check_result(
                        "judgment_tier", True,
                        "enabled, route=local — laya-as-judge importable (MLX)"))
                else:
                    results.append(check_result(
                        "judgment_tier", False,
                        "enabled, route=local — but laya-as-judge is NOT importable "
                        "(falls back to keyword behavior; generic route needs local_backend: generic)",
                        fix="pip install 'laya-as-judge[mlx]' (Apple Silicon, py3.11+) "
                            "or set integrations.judgment.local_backend: generic"))
    except Exception as e:
        results.append(check_result("judgment_tier", False, f"check failed: {e}"))

    # ---- 5. vault structure freshness
    try:
        import subprocess
        vault_path = FABRIC_ROOT
        vr = Path(__file__).parent / "vault-refresh.py"
        r = subprocess.run([sys.executable, str(vr), str(vault_path), "--check", "--quiet"],
                           capture_output=True, text=True, timeout=30)
        results.append(check_result(
            "vault_structure", r.returncode == 0,
            "fresh" if r.returncode == 0 else "structure drift detected",
            fix="wf vault"))
    except Exception as e:
        results.append(check_result("vault_structure", False, f"check failed: {e}"))

    # ---- 6. corpus log (the G4 gate reads it)
    log = CORPUS_ROOT / "registry" / "log.md"
    if log.exists():
        text = log.read_text()
        entries = text.count("* **")
        results.append(check_result(
            "registry_log", True, f"{log} — {entries} timeline entries"))
    else:
        results.append(check_result(
            "registry_log", False, "no corpus registry/log.md — the G4 gate reads this file",
            fix="run an eval with --record"))

    # ---- 7. HITL gate pending
    try:
        import subprocess
        gate = Path(__file__).parent / "gate.py"
        r = subprocess.run([sys.executable, str(gate), "--format", "json"],
                           capture_output=True, text=True, timeout=30)
        pending = json.loads(r.stdout or "{}")
        n = sum(len(v) for v in (pending.get("queues") or {}).values()) \
            if isinstance(pending.get("queues"), dict) else 0
        results.append(check_result(
            "gate", True,
            f"{n} pending decision(s)" if n else "nothing pending"))
    except Exception as e:
        results.append(check_result("gate", True, f"(gate check skipped: {e})"))

    # ---- report
    failures = [r for r in results if not r["passed"]]
    if args.json:
        print(json.dumps({"ok": not failures, "checks": results}, indent=2))
    else:
        print("Wiki Fabric — Doctor")
        print("═" * 40)
        for r in results:
            mark = "✓" if r["passed"] else "✗"
            print(f"{mark} {r['check']}: {r['detail']}")
            if not r["passed"] and r.get("fix"):
                print(f"    fix: {r['fix']}")
        print("═" * 40)
        if failures:
            print(f"{len(failures)} issue(s) — each names its fix")
        else:
            print("all checks passed")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())