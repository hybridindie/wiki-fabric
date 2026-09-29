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
        cloud_model: jev-latest # cloud route only
"""

import os
import re
import sys
from pathlib import Path
import json as _json
import pathlib as _p

_HERE = _p.Path(__file__).resolve().parent
# Same explicit bootstrap shape as the other lib modules (guarded by
# tests/test_wf_common.py::TestExplicitImportBootstrap).
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

from fabric_config import get_config, get_integrations, is_integration_active, get_tuning

CLOUD_MODEL_DEFAULT = "jev-latest"
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
    cfg.setdefault("cloud_model", CLOUD_MODEL_DEFAULT)  # fabric_config default also updated
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
    """TypeSafe Jev endpoint + key. Resolution order (key):
    1. TYPESAFE_API_KEY env var / secrets.env (machine-local, gitignored;
       loaded into env at config load — real env wins)
    2. integrations.judgment.api_key in fabric.yaml (legacy literal, still
       read; preferred home is secrets.env)
    Endpoint overridable for self-hosted/compatible judges."""
    env_key = os.environ.get("TYPESAFE_API_KEY", "")
    if env_key:
        base = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai")
        return base, env_key
    cfg = judgment_config()
    cfg_key = str(cfg.get("api_key", "")).strip()
    if cfg_key:
        base = cfg.get("base_url") or os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai")
        return base, cfg_key
    return os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai"), ""


def cloud_key_ready(config=None):
    """True when the cloud route has a key (env or config). Pre-flight check —
    surfaces the missing-key condition BEFORE a run burns work it can't finish."""
    _, key = _typesafe_endpoint()
    return bool(key)


# ---- Laya backend (real on-device inference; optional import) ----

_LAYA_ENGINE = {}  # module-level judge cache: {judge_key: judge}


def _near_band(config=None):
    return float(get_tuning(config, "judgment", "near_band", NEAR_BAND))


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
    # validate question specs BEFORE the laya import — config errors surface
    # even when the backend is missing (and tests can exercise this path)
    for q in questions:
        if q["kind"] == "choice" and not (q.get("options") or []):
            raise JudgmentUnavailable(f"choice question {q['name']!r} needs non-empty criteria")
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
            # laya's choice head takes criteria as {label: description} (or
            # bare list of labels); options entries are dicts {name, description}
            opts = q.get("options") or []
            criteria = {o["name"]: o.get("description") for o in opts} \
                if opts and isinstance(opts[0], dict) else list(opts)
            if not criteria:
                raise JudgmentUnavailable(f"choice question {q['name']!r} needs non-empty criteria")
            builder = builder.add_choice(q["name"], q["question"], criteria)
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
    if q["kind"] == "choice":
        qs[0]["options"] = q.get("options") or []
    if q["kind"] == "score":
        qs[0]["criteria"] = q.get("criteria") or []
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
    """TypeSafe Jev — the real System One wire protocol (POST /v1/systemone).
    One question per request (our tier's usage is pairwise, so batching adds
    no value). Answer payload: answers.<name>.<type> with calibrated values."""
    base, key = _typesafe_endpoint()
    if not key:
        raise JudgmentUnavailable("TYPESAFE_API_KEY not set (judgment cloud route)")
    import urllib.request
    name = q.get("name") or "q"
    question = {k: q[k] for k in ("type", "instructions", "criteria") if k in q}
    question["type"] = question.get("type") or q.get("kind", "")
    question["instructions"] = question.get("instructions") or q.get("question", "")
    if q["kind"] == "choice":
        # options entries are dicts {name, description} → Jev criteria map
        opts = q.get("options") or []
        question["criteria"] = question.get("criteria") or             {o["name"]: o.get("description") for o in opts}
    if q["kind"] == "noul" and q.get("false_desc"):
        question["criteria"] = {"false": q.get("false_desc"), "true": q.get("true_desc")}
    body = {
        "model": judgment_config().get("cloud_model", CLOUD_MODEL_DEFAULT),
        "state": q.get("state") or "",
        "questions": {name: question},
    }
    req = urllib.request.Request(
        f"{base}/v1/systemone",
        data=_json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = _json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode()[:200]
        except Exception:
            pass
        raise JudgmentUnavailable(f"cloud judge HTTP {e.code}: {detail}")
    except Exception as e:
        raise JudgmentUnavailable(f"cloud judge unreachable: {e}")
    return _normalize_jev(out, name, q)


def _normalize_jev(out, name, q):
    """Map Jev's answers.<name>.<type> to our internal shape."""
    cfg = judgment_config()
    cfg.setdefault("cloud_model", CLOUD_MODEL_DEFAULT)  # fabric_config default also updated
    answers = out.get("answers") or {}
    a = answers.get(name) or {}
    kind = q["kind"]
    if kind == "noul":
        value = a.get("noul")
        return {"value": float(value) if value is not None else 0.0,
                "confidence": a.get("answer_confidence") or a.get("confidence"),
                "backend": "jev", "model": out.get("model", "jev")}
    if kind == "choice":
        # laya-style options dicts vs our option list: Jev returns the label
        return {"value": str(a.get("choice", "")),
                "confidence": a.get("answer_confidence") or a.get("confidence"),
                "probabilities": a.get("probabilities"),
                "backend": "jev", "model": out.get("model", "jev")}
    if kind == "score":
        return {"value": a.get("score"),
                "confidence": a.get("answer_confidence") or a.get("confidence"),
                "backend": "jev", "model": out.get("model", "jev")}
    raise JudgmentUnavailable(f"unsupported question kind: {kind}")


def _is_apple_silicon():
    """True on macOS arm64 — the only platform laya's MLX backend supports."""
    if sys.platform != "darwin":
        return False
    try:
        import platform
        return platform.machine() == "arm64"
    except Exception:
        return False


def _ask_local(q):
    """On-device judging, platform-aware with a cross-platform default (#29):

      1. laya-as-judge (MLX, Apple Silicon) — fastest path (7-14ms)
      2. upstream laya (pip laya, torch/ONNX — macOS/Linux/Windows, CPU/GPU)
         — same typed heads, calibrated; first load downloads ~430MB
      3. generic route (any local GGUF/text model via local_llm, lowest
         fidelity) — explicit only, opt-in

    Config: local_backend: laya (auto) | laya-mlx | laya-torch | generic."""
    cfg = judgment_config()
    backend = cfg.get("local_backend", "laya")
    if backend == "generic":
        return _ask_generic(q)
    if backend == "laya-torch":
        return _ask_laya_direct(q)
    if backend in ("laya", "laya-mlx"):
        if _is_apple_silicon():
            try:
                return _ask_laya(q)
            except JudgmentUnavailable as e:
                if ("EmulatorBackend" in str(e) or "not installed" in str(e)) \
                        and cfg.get("local_fallback") == "generic":
                    return _ask_generic(q)
                # fall through to the cross-platform laya path
        return _ask_laya_direct(q)
    raise JudgmentUnavailable(f"unknown local_backend: {backend!r}")


def _ask_laya_direct(q):
    """Cross-platform on-device judgment via the upstream laya package
    (pip laya — torch/ONNX; macOS/Linux/Windows, CPU/CUDA/MPS). Same typed
    heads and calibrated probabilities as laya-as-judge's MLX path, without
    the Apple requirement. First load downloads the checkpoint (~430MB)."""
    try:
        from laya import Router
    except ImportError as e:
        raise JudgmentUnavailable(
            f"upstream laya not installed (pip install laya): {e}")
    name = q.get("name") or "q"
    question = {k: q[k] for k in ("type", "instructions", "criteria") if k in q}
    question["type"] = question.get("type") or q.get("kind", "")
    question["instructions"] = question.get("instructions") or q.get("question", "")
    if q["kind"] == "choice":
        opts = q.get("options") or []
        question["criteria"] = question.get("criteria") or \
            {o["name"]: o.get("description") for o in opts}
    if q["kind"] == "noul" and q.get("false_desc"):
        question["criteria"] = {"false": q.get("false_desc"), "true": q.get("true_desc")}
    router = _laya_direct_router()
    out = router.predict(q.get("state") or "", {name: question})
    a = (out.get("answers") or {}).get(name) or {}
    if q["kind"] == "noul":
        value = a.get("noul")
        return {"value": float(value) if value is not None else 0.0,
                "confidence": (a.get("answer_confidence") or a.get("confidence")),
                "backend": "laya-direct", "model": (out.get("routing") or {}).get("model", "laya")}
    if q["kind"] == "choice":
        return {"value": str(a.get("choice", "")),
                "confidence": (a.get("answer_confidence") or a.get("confidence")),
                "probabilities": a.get("probabilities"),
                "backend": "laya-direct", "model": (out.get("routing") or {}).get("model", "laya")}
    if q["kind"] == "score":
        return {"value": a.get("score"),
                "confidence": (a.get("answer_confidence") or a.get("confidence")),
                "backend": "laya-direct", "model": (out.get("routing") or {}).get("model", "laya")}
    raise JudgmentUnavailable(f"unsupported question kind: {q['kind']}")


_LAYA_DIRECT = {}


def _laya_direct_router():
    from laya import Router
    key = "router"
    if key not in _LAYA_DIRECT:
        _LAYA_DIRECT[key] = Router()
    return _LAYA_DIRECT[key]


def _ask_generic(q):
    """Generic route: any local text model emitting JSON verdicts (GGUF via
    llama.cpp on any platform; MLX on Apple Silicon — same model set as the
    local generation tier). Lowest fidelity: no typed heads, no calibration."""
    from fabric_config import get_local_model
    model_id = judgment_config().get("local_model") or get_local_model()
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
    return abs(p - threshold) <= _near_band()


def same_recurrence(item_a, item_b, threshold=None, config=None, context=None):
    """Pairwise 'same recurring pattern?' judgment for cluster refinement.
    Returns (same: bool, probability: float). Threshold defaults to
    MINING_THRESHOLD_DEFAULT (0.8) — live-calibrated on Laya: true paraphrase
    pairs score ~0.93, unrelated pairs ~0.75, so 0.6 would wrongly merge
    unrelated content. Used by mine-promotions (judgment-enabled mode only).
    context (#103b): optional thread-structure note — the model sees that
    the records' sessions share files or continue each other."""
    if threshold is None:
        threshold = get_tuning(config, "judgment", "mining_threshold",
                               MINING_THRESHOLD_DEFAULT)
    state = (f"Item A: {item_a}\n\nItem B: {item_b}")
    if context:
        state = f"{state}\n\n{context}"
    p = noul("Do these two records describe the same recurring problem and intervention?",
             state)
    return (p >= threshold, p)

# ---- Effect verification (ingest, #29 wiring A) ----------------------------

EFFECT_OPTIONS = {
    "supports": "the new claim confirms or strengthens this claim",
    "contradicts": "the new claim asserts something incompatible with this claim",
    "supersedes": "the new claim is a newer version replacing this claim's content",
    "no-action": "neither — they are about different aspects or facts",
}


def effect_verdict(new_statement, existing_statement):
    """Judged effect classification for one (new, existing) claim pair.
    Returns {effect, confidence, probabilities, backend, model}. Effects:
    supports | contradicts | supersedes | no-action (the agent's draft is
    verified, not replaced — the tier is the independent second opinion)."""
    options = [{"name": k, "description": v} for k, v in EFFECT_OPTIONS.items()]
    out = choice(
        "Which relationship does the NEW claim have to the EXISTING claim?",
        f"NEW claim:\n{new_statement}\n\nEXISTING claim:\n{existing_statement}",
        options,
    )
    val = str(out.get("value", "")).strip().lower()
    for k in EFFECT_OPTIONS:
        if k in val:
            return {"effect": k, "confidence": out.get("confidence"),
                    "probabilities": out.get("probabilities")}
    return {"effect": "no-action", "confidence": out.get("confidence"),
            "probabilities": out.get("probabilities")}


def related_claim_pool(new_claim_path, max_n=12):
    """Candidate existing claims to compare against: same-source first, then
    same-project claims (deterministic ordering, capped)."""
    from fabric_config import CORPUS_ROOT
    text = Path(new_claim_path).read_text(encoding="utf-8", errors="replace")
    m = re.search(r'\[\[(src-[\w-]+)\]\]', text)
    out = []
    if m:
        src_slug = m.group(1)
        # claims citing the same source record (slug match on stem)
        stem_prefix = src_slug.replace("-md", "")
        for p in sorted((CORPUS_ROOT / "evidence" / "claims").glob(f"claim-{stem_prefix}-*.md")):
            if p.resolve() != Path(new_claim_path).resolve():
                out.append(p)
    # topical neighbors: same project namespace
    m2 = re.search(r"claim-([\w-]+?)-[\w-]+-md-\d+", Path(new_claim_path).stem)
    if m2:
        proj = m2.group(1)
        for p in sorted((CORPUS_ROOT / "evidence" / "claims").glob(f"claim-{proj}-*.md")):
            if p.resolve() != Path(new_claim_path).resolve() and p not in out:
                out.append(p)
    return out[:max_n]
