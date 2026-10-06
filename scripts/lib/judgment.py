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
  - G-J gate (the compiler's G4 analog): a judge swap is a judgment
    change — the current judge (route + model identity) must have a
    PASS calibration receipt (scripts/eval/eval-judgment.py --record)
    in registry/log.md before any call site accepts it. Untested judge
    = no proposals. Override with WIKI_JUDGE_GATE=0 (explicit env opt-out,
    logged when used) — the OFF switch is loud, never silent.

Integration shape (fabric.yaml):
    integrations:
      judgment:
        enabled: true
        route: local           # "cloud" | "local"
        local_backend: laya    # "laya" (auto: MLX if installed) | "ollama" (tev1/nimble decision models) | "generic"
        cloud_model: jev-latest # cloud route only

Judgment is a FABRIC-GLOBAL setting (no per-repo override — the graphify
graph_dir seam doesn't apply here): one judge identity per fabric keeps the
G-J calibration gate meaningful (a judge swap is a judgment change, and the
calibration receipt names the judge — per-repo route pinning would multiply
identities and silently fork the calibrations).
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

from fabric_config import get_config, get_integration_cfg, get_tuning


def fabric_config_get(key, default):
    """Tiny accessor so the ollama judge route reads live config (llm.)
    without a second import cycle."""
    return get_config().get(key, default)

CLOUD_MODEL_DEFAULT = "jev-latest"
MINING_THRESHOLD_DEFAULT = 0.8  # live-calibrated: unrelated pairs score ~0.75
NEAR_BAND = 0.1                 # |p - threshold| <= band => escalate, don't auto-decide


class JudgmentUnavailable(Exception):
    """Raised when the judgment tier is requested but not configured/reachable."""


def judgment_config(config=None):
    """Merged judgment dict — global only, deliberately. Judgment was once
    per-repo overridable (repos.<slug>.integrations.judgment); that seam is
    gone: the judge identity is a one-per-fabric calibration contract, and a
    per-repo route pin would multiply identities under one G-J gate.
    Disabled by default."""
    config = config or get_config()
    cfg = get_integration_cfg(config, "judgment")
    if not isinstance(cfg, dict):
        cfg = {"enabled": bool(cfg)}
    cfg.setdefault("enabled", False)
    cfg.setdefault("route", "cloud")
    cfg.setdefault("local_backend", "laya")
    cfg.setdefault("cloud_model", CLOUD_MODEL_DEFAULT)  # fabric_config default also updated
    return cfg


def is_judgment_active(config=None, repo=None):
    """True only when explicitly enabled globally. `repo` is accepted (and
    ignored) — the per-repo judgment override seam was removed; callers thread
    project context for other reasons and the asker-shape stays stable."""
    cfg = get_integration_cfg(config or get_config(), "judgment")
    return bool((cfg or {}).get("enabled", False))


def judgment_route(config=None, repo=None):
    cfg = judgment_config(config)
    if not is_judgment_active(config):
        raise JudgmentUnavailable("integrations.judgment.enabled is false")
    return cfg.get("route", "cloud")


def judge_identity(config=None, repo=None):
    """(judge, model) — the CURRENT judge's identity tuple, the thing a swap
    changes. route=cloud → cloud_model; local → backend + resolved tag."""
    cfg = judgment_config(config)
    route = cfg.get("route", "cloud")
    if route == "cloud":
        m = cfg.get("cloud_model") or CLOUD_MODEL_DEFAULT
        return ("cloud", m)
    backend = cfg.get("local_backend") or "laya"
    if backend == "ollama" or cfg.get("local_model"):
        try:
            from systemone import judge_tag
            return ("systemone", judge_tag())
        except Exception:
            return ("systemone", cfg.get("local_model") or "unresolved")
    return (backend, cfg.get("local_model") or backend)


def judgment_eval_recorded(config=None, log_path=None):
    """G-J gate: True when registry/log.md holds a PASS judgment-eval receipt
    for the CURRENT judge identity (judge_kind + model). The compiler's G4
    analog (fabric_config.compiler_eval_recorded): a judge swap is a judgment
    change; an uncalibrated judge may not propose. Returns (ok, detail).
    WIKI_JUDGE_GATE=0 (explicit, logged at use) skips — the off switch is
    loud."""
    identity = judge_identity(config)
    if os.environ.get("WIKI_JUDGE_GATE", "") == "0":
        return True, "G-J gate SKIPPED (WIKI_JUDGE_GATE=0)"
    import re
    import layout
    log_path = Path(log_path or (layout.registry() / "log.md"))
    if not log_path.exists():
        return False, ("no registry/log.md — run: "
                       "python3 scripts/eval/eval-judgment.py --record")
    text = log_path.read_text(errors="replace")
    # receipt blocks: '## YYYY-MM-DD' + '* **judgment-eval | PASS**' body
    block_re = re.compile(
        r"## \d{4}-\d{2}-\d{2}[^\n]*\n\* \*\*judgment-eval \| (\w+)\*\*(.*?)(?=\n## |\Z)",
        re.DOTALL)
    for m in block_re.finditer(text):
        verdict, body = m.group(1), m.group(2)
        line_m = re.search(r"judge: (.*)", body)
        line = (line_m.group(1).strip() if line_m else "")
        kind = line.split()[0] if line.split() else ""
        if verdict != "PASS" or kind != identity[0]:
            continue
        # parse the receipt line: 'judge: <kind> [<model>] route: <route>'
        tokens = line.split()
        after_kind = tokens[1:] if len(tokens) > 1 else []
        route_idx = after_kind.index("route:") if "route:" in after_kind else len(after_kind)
        model_tokens = after_kind[:route_idx] if "route:" in after_kind else []
        receipt_model = model_tokens[0] if model_tokens else ""
        if receipt_model:
            # a model-pinned receipt matches ONLY its own model (a swap must
            # re-calibrate — the core case this gate exists for)
            if receipt_model == identity[1]:
                return True, f"judgment-eval PASS recorded for {kind}:{identity[1]}"
            continue
        # unpinned receipt (route-only): matches the KIND — legacy receipt
        if "route" in line and kind == identity[0]:
            return True, (f"judgment-eval PASS recorded for {kind} "
                          f"(receipt predates model pinning)")
    return False, (f"no judgment-eval PASS receipt for judge {identity[0]}:{identity[1]} — "
                   f"a judge swap is a judgment change; run: "
                   f"python3 scripts/eval/eval-judgment.py --record")


def CORPUS_LOG():
    import layout
    return layout.registry()


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

def score(question, state, rubric=None, repo=None):
    """Ordered rubric score with probabilities + confidence. `repo` accepted
    and ignored (the per-repo override seam is gone — judgment is global)."""
    return _ask({"kind": "score", "question": question, "state": state,
                 "rubric": rubric or {}})


def choice(question, state, options, repo=None):
    """One of the options with probabilities + confidence. `repo` accepted
    and ignored (same shape stability as score)."""
    return _ask({"kind": "choice", "question": question, "state": state,
                 "options": list(options)})


def _ask(q, repo=None):
    """Route per CALL: the fabric's global judgment route (one judge identity,
    one G-J calibration). `repo` accepted and ignored for shape stability."""
    route = judgment_route()
    if route == "cloud":
        return _ask_cloud(q)
    return _ask_local(q)


def noul(question, state, false_desc=None, true_desc=None, repo=None):
    """P(yes) for a yes/no judgment (0.0..1.0). Criteria descriptions
    (false_desc/true_desc) dramatically sharpen laya's separation —
    live-calibrated: criteria phrasing separates 0.97 vs 0.19; abstract
    phrasing only 0.3–0.6 vs 0.19. `repo` accepted and ignored — the per-repo
    judgment override seam was removed (judgment is a fabric-global setting)."""
    out = _ask({"kind": "noul", "question": question, "state": state,
                "false_desc": false_desc, "true_desc": true_desc})
    return float(out.get("value", 0.0))


def _ask_cloud(q):
    """TypeSafe Jev — the System One wire (POST /v1/systemone, same protocol
    the local ollama tier serves). One question per request (our tier's
    usage is pairwise, so batching adds no value). Answer payload:
    answers.<name>.<type> with calibrated values."""
    base, key = _typesafe_endpoint()
    if not key:
        raise JudgmentUnavailable("TYPESAFE_API_KEY not set (judgment cloud route)")
    name, question = _systemone_question(q)
    body = {
        "model": judgment_config().get("cloud_model", CLOUD_MODEL_DEFAULT),
        "state": q.get("state") or "",
        "questions": {name: question},
    }
    out = _ask_systemone(base, body,
                         headers={"Authorization": f"Bearer {key}"})
    return _normalize_jev(out, name, q)


def _normalize_jev(out, name, q, backend="jev"):
    """Map System One answers.<name>.<type> to our internal shape (Jev cloud
    AND the local ollama /v1/systemone tier share one wire protocol —
    same normalizer, backend tag differs)."""
    answers = out.get("answers") or {}
    a = answers.get(name) or {}
    kind = q["kind"]
    if kind == "noul":
        value = a.get("noul")
        return {"value": float(value) if value is not None else 0.0,
                "confidence": a.get("answer_confidence") or a.get("confidence"),
                "probabilities": a.get("probabilities"),
                "backend": backend, "model": out.get("model", backend)}
    if kind == "choice":
        # laya-style options dicts vs our option list: Jev returns the label
        return {"value": str(a.get("choice", "")),
                "confidence": a.get("answer_confidence") or a.get("confidence"),
                "probabilities": a.get("probabilities"),
                "backend": backend, "model": out.get("model", backend)}
    if kind == "score":
        return {"value": a.get("score"),
                "confidence": a.get("answer_confidence") or a.get("confidence"),
                "probabilities": a.get("probabilities"),
                "backend": backend, "model": out.get("model", backend)}
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
    """Local judging, platform-aware (#29; 2026-09-30: decision models add
    the ollama tier — Tev/Nimble-class server-local classifiers, egress-free):

      1. laya-as-judge (MLX, Apple Silicon) — fastest path (7-14ms)
      2. upstream laya (pip laya, torch/ONNX — macOS/Linux/Windows, CPU/GPU)
         — same typed heads, calibrated; first load downloads ~430MB
      3. ollama decision models (repo-external, server-local; e.g. tev1:latest,
         nimble:latest) — typed-ish heads via format:json probes; no egress
      4. generic route (any local GGUF/text model via local_llm, lowest
         fidelity) — explicit only, opt-in

    Config: local_backend: laya (auto) | laya-mlx | laya-torch | ollama | generic."""
    cfg = judgment_config()
    backend = cfg.get("local_backend", "laya")
    if backend == "generic":
        return _ask_generic(q)
    if backend == "ollama":
        return _ask_ollama(q)
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


_OLLAMA_JUDGE_REJECT_TAGS = ("cloud", "hosted", "remote")  # hosted farm = egress


def _judge_ollama_model():
    """The decision-model tag (single truth: systemone.judge_tag — the same
    resolution + hosted-farm/notice contract)."""
    from systemone import judge_tag, SystemOneUnavailable
    try:
        return judge_tag()
    except SystemOneUnavailable as e:
        raise JudgmentUnavailable(str(e))


def _systemone_question(q):
    """Our question shape → System One wire shape (shape truth here; the
    POST itself is single-truth via systemone.py)."""
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
    return name, question


def _ask_systemone(base_url, body, timeout=120, headers=None):
    """POST /v1/systemone via the single wire implementation (systemone.py)."""
    from systemone import systemone as _post, SystemOneUnavailable
    try:
        return _post(base_url, body.get("model"), body.get("state"),
                     body.get("questions"),
                     timeout_ms=timeout * 1000 if timeout else None,
                     headers=headers)
    except SystemOneUnavailable as e:
        raise JudgmentUnavailable(str(e))


def _ask_ollama(q):
    """Judgment via the LOCAL ollama server's System One endpoint
    (POST /v1/systemone — the same wire protocol as TypeSafe Jev cloud,
    minus auth). Model gates live in systemone.py (Tev/Nimble family;
    hosted-farm tags refused)."""
    model_id = _judge_ollama_model()
    name, question = _systemone_question(q)
    body = {
        "model": model_id,
        "state": q.get("state") or "",
        "questions": {name: question},
    }
    base_url = (fabric_config_get("llm", {}).get("base_url")
                or "http://localhost:11434/v1")
    try:
        out = _ask_systemone(base_url, body)
    except JudgmentUnavailable as e:
        raise JudgmentUnavailable(f"ollama judge failed ({model_id}): {e}")
    return _normalize_jev(out, name, q, backend="ollama")



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


def same_recurrence(item_a, item_b, threshold=None, config=None, context=None, repo=None):
    """Pairwise 'same recurring pattern?' judgment for cluster refinement.
    `repo` accepted and ignored: the per-repo judgment override seam is gone
    (one judge identity per fabric — mining pairs all route globally).
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
# Effects are a strict subset of lint's REL_TYPES (#155-E: one relation-typing
# truth — judgment may not introduce a relation verb the linter doesn't know).
# The option list itself stays fixed (supports/contradicts/supersedes/no-action)
# — the choice head's option set is part of the recorded eval contract.
_CORE_EFFECTS = {"supports", "contradicts", "supersedes"}
_REL_EXEMPT = {"no-action"}  # a judgment verdict, not a corpus relation
EFFECT_OPTIONS = {
    "supports": "the new claim confirms or strengthens this claim",
    "contradicts": "the new claim asserts something incompatible with this claim",
    "supersedes": "the new claim is a newer version replacing this claim's content",
    "no-action": "neither — they are about different aspects or facts",
}


def effect_options_subset_of_lint():
    """Contract check (#155-E): every judgment effect must be a known REL_TYPE
    (no-action is exempt: it's the tier's abstention verdict, not a relation
    verb). Returns (ok, detail) — exercised by tests; lint-independent fallback
    keeps the tier runnable when scripts/cmd isn't importable."""
    try:
        from lint import REL_TYPES
    except Exception:
        return True, "lint unavailable — contract checked at test time"
    unknown = (_CORE_EFFECTS - set(REL_TYPES))
    return (not unknown), unknown


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


def related_claim_pool(new_claim_path, max_n=12, _claims_root=None):
    """Candidate existing claims to compare against: same-source first, then
    same-project claims (deterministic ordering, capped). Project cut is the
    canonical slug seam, not a lazy-dash regex (those truncated at the first
    dash: 'comfyui' out of comfyui-mcp). _claims_root overrides CORPUS_ROOT
    (test seam)."""
    from fabric_config import CORPUS_ROOT as _default_root
    root = _claims_root or _default_root
    from layout import claims_for_project, claims_for_source
    text = Path(new_claim_path).read_text(encoding="utf-8", errors="replace")
    m = re.search(r'\[\[(src-[\w-]+)\]\]', text)
    out = []
    if m:
        src_slug = m.group(1)
        # claims citing the same source record: src-slug minus the 'src-' prefix
        # IS the raw-rel slug — the claim glob is claim-<raw-rel-slug>-NNN
        stem_prefix = src_slug[len("src-"):]
        s_glob = claims_for_source(root, stem_prefix)
        for p in sorted(s_glob.parent.glob(s_glob.name)):
            if p.resolve() != Path(new_claim_path).resolve():
                out.append(p)
    # topical neighbors: same project namespace. Structural parse: the raw
    # rel slug's FIRST segment is the project dir (dash-free in raw tree
    # names? no — could contain dashes; so fold candidates through the
    # canonical slug: try each dash-prefix, keep the longest with hits).
    stem = Path(new_claim_path).stem
    if stem.startswith("claim-"):
        body = stem[len("claim-"):]
        cands = body.rsplit("-", 1)[0] if body.rsplit("-", 1)[-1].isdigit() else body
        proj = None
        parts = cands.split("-")
        for cut in range(len(parts), 0, -1):
            cand = "-".join(parts[:cut])
            g = claims_for_project(root, cand)
            if any(g.parent.glob(g.name)):
                proj = cand
                break
        if proj:
            g = claims_for_project(root, proj)
            for p in sorted(g.parent.glob(g.name)):
                if p.resolve() != Path(new_claim_path).resolve() and p not in out:
                    out.append(p)
    return out[:max_n]
