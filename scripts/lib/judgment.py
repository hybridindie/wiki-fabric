"""judgment.py — optional judgment tier: low-variance decision-model judging.

Sits between the fabric's deterministic string ops (0 tokens, always) and
its generative LLM calls (expensive, variable): a "System One" decision
model evaluates typed questions against the assembled state and returns
typed answers + calibrated probabilities. Three backends, tried in order:

  cloud: TypeSafe Jev API          (route: cloud; TYPESAFE_API_KEY env)
  laya:  Laya-MLX on-device judge  (optional package laya-as-judge[mlx];
                                   real inference via CustomJudge typed heads)
  local: generic local-model JSON  (fallback: any local_llm model that can
                                   emit a JSON verdict — lowest fidelity)

Hard contract (AGENTS.md / machine-contract.md):
  - NEVER used in wf context / wf query / lint — the 0-token core is
    pure string ops and stays that way. This module is called only from
    evaluation and promotion-review surfaces (test-guarded).
  - Low-variance judgment, not determinism: every call records the
    backend, model, and probabilities so consumers can distinguish
    judged surfaces from deterministic ones.
  - Judgment is never authority: a judge score supports a check; the
    provenance/scope/human-gate rules still decide.
  - The emulator NEVER auto-serves judgment: laya's keyword-heuristic
    fallback has no discriminative power (returns fixed probabilities),
    so it is explicitly rejected here.

Integration shape (fabric.yaml):
    integrations:
      judgment:
        enabled: true
        route: local           # "cloud" | "local"
        local_backend: laya    # "laya" (auto: MLX when installed) | "generic"
        cloud_model: jev-1     # cloud route only
"""

import os
import sys
import json as _json
import pathlib as _p

_HERE = _p.Path(__file__).resolve().parent
# Same explicit bootstrap shape as the other lib modules (guarded by
# tests/test_wf_common.py::TestExplicitImportBootstrap).
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

from fabric_config import get_config, get_integrations, is_integration_active

CLOUD_MODEL_DEFAULT = "jev-1"
MINING_THRESHOLD_DEFAULT = 0.8  # live-calibrated: unrelated pairs score ~0.75
NEAR_BAND = 0.1                 # |p - threshold| <= band => escalate, don't auto-decide


class JudgmentUnavailable(Exception):
    """Raised when the judgment tier is requested but not configured/reachable."""


def judgment_config(config=None):
    """Merged integrations.judgment dict; disabled by default."""
    config = config or get_config()
    integ = get_integrations(config)
    cfg = integ.get("judgment") or {}
    if not isinstance(cfg, dict):
        cfg = {"enabled": bool(cfg)}
    cfg.setdefault("enabled", False)
    cfg.setdefault("route", "cloud")
    cfg.setdefault("local_backend", "laya")
    cfg.setdefault("cloud_model", CLOUD_MODEL_DEFAULT)
    return cfg


def is_judgment_active(config=None):
    """True only when explicitly enabled in fabric.yaml (same rule as
    graphify/embeddings)."""
    return is_integration_active(config or get_config(), "judgment")


def judgment_route(config=None):
    cfg = judgment_config(config)
    if not is_judgment_active(config):
        raise JudgmentUnavailable("integrations.judgment.enabled is false")
    return cfg.get("route", "cloud")


def _typesafe_endpoint():
    """TypeSafe Jev endpoint + key. Endpoint overridable for self-hosted/
    compatible judges; key from env TYPESAFE_API_KEY (never committed)."""
    return (
        os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1"),
        os.environ.get("TYPESAFE_API_KEY", ""),
    )


# ---- Laya backend (real on-device inference; optional import) ----

_LAYA_ENGINE = {}  # module-level judge cache: {judge_key: judge}


def laya_available():
    """True when the laya-as-judge package imports (MLX runtime present)."""
    try:
        import laya_as_judge  # noqa: F401
        return True
    except ImportError:
        return False

def _laya_engine(questions):
    """Build (and memoize) a CustomJudge for the given typed questions.
    backend='auto' selects MLX on Apple Silicon; the keyword-heuristic
    emulator is explicitly REJECTED (no discriminative power)."""
    key = _json.dumps(sorted(questions), sort_keys=True)
    if key in _LAYA_ENGINE:
        return _LAYA_ENGINE[key]
    try:
        from laya_as_judge import CustomJudge
    except ImportError as e:
        raise JudgmentUnavailable(
            f"laya-as-judge not installed (pip install 'laya-as-judge[mlx]'): {e}")
    builder = CustomJudge.builder("WikiFabricJudge")
    for q in questions:
        if q["kind"] == "noul":
            builder = builder.add_noul(q["name"], q["question"],
                                       false_desc=q.get("false_desc"),
                                       true_desc=q.get("true_desc"))
        elif q["kind"] == "score":
            builder = builder.add_score(q["name"], q["question"], q.get("criteria", []))
        elif q["kind"] == "choice":
            builder = builder.add_choice(q["name"], q["question"], q.get("options", []))
        else:
            raise JudgmentUnavailable(f"unsupported question kind: {q['kind']}")
    judge = builder.build(backend="auto")
    # refuse the emulator: it is a keyword heuristic, not a model
    probe = judge.evaluate("__probe__")
    backend_name = probe.to_dict().get("backend", "")
    if "emulator" in backend_name.lower():
        raise JudgmentUnavailable(
            "laya backend resolved to the EmulatorBackend (no MLX runtime) — "
            "install 'laya-as-judge[mlx]' on Apple Silicon for real inference")
    _LAYA_ENGINE[key] = (judge, backend_name)
    return _LAYA_ENGINE[key]


def _ask_laya(q):
    """Typed on-device judgment via laya CustomJudge (MLXBackend)."""
    import time
    name = q.get("name") or "q"
    qs = [{"name": name, "kind": q["kind"], "question": q["question"]}]
    if q["kind"] == "score":
        qs = [x for x in [qs[0]] if x]
    judge, backend_name = _laya_engine(qs)
    t0 = time.monotonic()
    report = judge.evaluate(q.get("state") or "")
    d = report.to_dict()
    judgement = (d.get("judgements") or {}).get(name)
    if not judgement:
        raise JudgmentUnavailable(f"laya report missing judgement {name!r}: {d}")
    out = {
        "value": judgement.get("prob_true") if q["kind"] == "noul"
        else judgement.get("expected_score", judgement.get("holds")),
        "confidence": judgement.get("confidence"),
        "probabilities": judgement.get("action_probability"),
        "backend": f"laya/{backend_name}",
        "model": d.get("model"),
        "latency_ms": round((time.monotonic() - t0) * 1000, 2),
    }
    if q["kind"] == "choice":
        # typed choice: find the argmax option from the report
        choice_val = judgement.get("decision", judgement.get("choice"))
        out["value"] = choice_val
    return out


# ---- question constructors (typed; shared by all routes) ----

def score(question, state, rubric=None):
    """Ordered rubric score with probabilities + confidence."""
    return _ask({"kind": "score", "question": question, "state": state,
                 "rubric": rubric or {}})


def choice(question, state, options):
    """One of the options with probabilities + confidence."""
    return _ask({"kind": "choice", "question": question, "state": state,
                 "options": list(options)})


def _ask(q):
    route = judgment_route()
    if route == "cloud":
        return _ask_cloud(q)
    return _ask_local(q)


def noul(question, state, false_desc=None, true_desc=None):
    """P(yes) for a yes/no judgment (0.0..1.0). Criteria descriptions
    (false_desc/true_desc) dramatically sharpen laya's separation —
    live-calibrated: criteria phrasing separates 0.97 vs 0.19; abstract
    phrasing only 0.3–0.6 vs 0.19."""
    out = _ask({"kind": "noul", "question": question, "state": state,
                "false_desc": false_desc, "true_desc": true_desc})
    return float(out.get("value", 0.0))


def _ask_cloud(q):
    """TypeSafe Jev (or any OpenAI-compatible decision endpoint)."""
    base, key = _typesafe_endpoint()
    if not key:
        raise JudgmentUnavailable("TYPESAFE_API_KEY not set (judgment cloud route)")
    try:
        import urllib.request
        cfg = judgment_config()
        body = _json.dumps({
            "model": cfg.get("cloud_model", CLOUD_MODEL_DEFAULT),
            "question": q["question"],
            "state": q.get("state"),
            "kind": q["kind"],
        }).encode()
        req = urllib.request.Request(
            f"{base}/judge",
            data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = _json.loads(resp.read().decode())
    except JudgmentUnavailable:
        raise
    except Exception as e:
        raise JudgmentUnavailable(f"cloud judge unreachable: {e}")
    return _normalize(out)


def _ask_local(q):
    """On-device judging. Primary: laya-as-judge (typed heads, MLX). Fallback:
    generic local-model JSON emission (lowest fidelity, opt-in explicitly)."""
    cfg = judgment_config()
    backend = cfg.get("local_backend", "laya")
    if backend == "laya":
        try:
            return _ask_laya(q)
        except JudgmentUnavailable as e:
            if "EmulatorBackend" in str(e) or "not installed" in str(e):
                if backend == "laya" and cfg.get("local_fallback") != "generic":
                    raise
            raise
    # generic route: any local text model emitting JSON verdicts
    from fabric_config import get_local_model
    model_id = cfg.get("local_model") or get_local_model()
    prompt = (f"Question: {q['question']}\n\nState:\n{q.get('state') or ''}\n\n"
              f"Answer with a JSON object: "
              + ('{"value": <probability 0..1>}' if q["kind"] == "noul"
                 else '{"value": <option|score>, "confidence": <float>}'))
    try:
        from local_llm import generate
        raw = generate(prompt, model_id=model_id, max_tokens=256)
    except Exception as e:
        raise JudgmentUnavailable(f"local judge unavailable: {e}")
    return _parse_local(raw)


def _parse_local(raw):
    """Extract the JSON object from local text output (tolerant)."""
    txt = raw.strip()
    try:
        out = _json.loads(txt)
    except Exception:
        start, end = txt.find("{"), txt.rfind("}")
        if start < 0 or end <= start:
            raise JudgmentUnavailable(f"local judge returned non-JSON: {txt[:120]}")
        try:
            out = _json.loads(txt[start:end + 1])
        except Exception as e:
            raise JudgmentUnavailable(f"local judge JSON unparseable: {e}")
    return _normalize(out)


def _normalize(out):
    """Coerce any backend's answer into {value, confidence, probabilities}."""
    if not isinstance(out, dict):
        out = {"value": out}
    value = out.get("value", out.get("probability", out.get("answer")))
    return {
        "value": value,
        "confidence": out.get("confidence"),
        "probabilities": out.get("probabilities"),
        "backend": out.get("backend"),
    }


# ---- eval-integration helper: stable verdict from low-variance judgment ----

def verdict(question, state, threshold=0.5):
    """Binary verdict for eval gates. Returns (passed, probability). Escalation
    is the caller's policy: values within NEAR_BAND of the threshold surface
    as near-threshold and should route to the human gate, never auto-decide."""
    p = noul(question, state)
    return (p >= threshold, p)


def is_near_threshold(p, threshold):
    """True when the probability sits inside the escalation band."""
    return abs(p - threshold) <= NEAR_BAND


def same_recurrence(item_a, item_b, threshold=None):
    """Pairwise 'same recurring pattern?' judgment for cluster refinement.
    Returns (same: bool, probability: float). Threshold defaults to
    MINING_THRESHOLD_DEFAULT (0.8) — live-calibrated on Laya: true paraphrase
    pairs score ~0.93, unrelated pairs ~0.75, so 0.6 would wrongly merge
    unrelated content. Used by mine-promotions (judgment-enabled mode only)."""
    if threshold is None:
        threshold = MINING_THRESHOLD_DEFAULT
    state = (f"Item A: {item_a}\n\nItem B: {item_b}")
    p = noul("Do these two records describe the same recurring problem and intervention?",
             state)
    return (p >= threshold, p)