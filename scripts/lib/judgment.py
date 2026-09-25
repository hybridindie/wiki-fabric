"""judgment.py — optional judgment tier: low-variance decision-model judging.

Sits between the fabric's deterministic string ops (0 tokens, always) and
its generative LLM calls (expensive, variable): a "System One" decision
model evaluates typed questions against the assembled state and returns
typed answers + calibrated probabilities. Two routes, mirroring the
extract/synthesize/dossier routing tiers:

  cloud: TypeSafe Jev API            (llm.judgment or judgment.default)
  local: Laya-MLX on-device judge    (llm.local_model style dispatch)

Hard contract (AGENTS.md / machine-contract.md):
  - NEVER used in wf context / wf query / lint — the 0-token core is
    pure string ops and stays that way. This module is called only from
    evaluation and (future) promotion-review surfaces.
  - Low-variance judgment, not determinism: every call records the
    backend, model, and probabilities so consumers can distinguish
    judged surfaces from deterministic ones.
  - Judgment is never authority: a judge score supports a check; the
    provenance/scope/human-gate rules still decide.

Integration shape (fabric.yaml):
    integrations:
      judgment:
        enabled: true
        route: cloud          # "cloud" | "local"
        cloud_model: jev-1    # TypeSafe Jev model id (cloud route)
        # local route uses llm.local_model (Laya-MLX GGUF/MLX judge)
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
    cfg.setdefault("cloud_model", CLOUD_MODEL_DEFAULT)
    return cfg


def is_judgment_active(config=None):
    """True only when explicitly enabled in fabric.yaml (same rule as
    graphify/embeddings)."""
    return is_integration_active(config or get_config(), "judgment")


def _typesafe_endpoint():
    """TypeSafe Jev endpoint + key. Endpoint overridable for self-hosted/
    compatible judges; key from env TYPESAFE_API_KEY (never committed)."""
    return (
        os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai/v1"),
        os.environ.get("TYPESAFE_API_KEY", ""),
    )


# ---- question constructors (typed; shared by both routes) ----

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


def judgment_route(config=None):
    cfg = judgment_config(config)
    if not is_judgment_active(config):
        raise JudgmentUnavailable("integrations.judgment.enabled is false")
    return cfg.get("route", "cloud")


def noul(question, state):
    """P(yes) for a yes/no judgment (0.0..1.0). Convenience wrapper."""
    out = _ask({"kind": "noul", "question": question, "state": state})
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
    """On-device judge (Laya-MLX open Jev-alike) via the local-model stack."""
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
    """Binary verdict for eval gates. Returns (passed, detail). Escalation is
    the caller's policy: values near the threshold (band) should route to the
    existing human-gate machinery, never auto-decide."""
    p = noul(question, state)
    return (p >= threshold, p)


def same_recurrence(item_a, item_b, threshold=0.6):
    """Pairwise 'same recurring pattern?' judgment for cluster refinement.
    Returns (same: bool, probability: float). Used by mine-promotions to
    rescue near-miss keyword pairs (judgment-enabled mode only)."""
    state = (f"Item A: {item_a}\n\nItem B: {item_b}")
    p = noul("Do these two records describe the same recurring problem and intervention?",
             state)
    return (p >= threshold, p)