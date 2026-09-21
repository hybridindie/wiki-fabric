#!/usr/bin/env python3
# local_llm.py — Shared on-device LLM backend for wiki-fabric scripts.
#
# Two backends, selected by model-id shape:
#   "mlx"   — mlx-lm (Apple Silicon only). mlx-community/* ids or local dirs.
#   "gguf"  — llama-cpp-python (any OS). *.gguf ids or local dirs/files.
#
# Single entry point:
#   generate(prompt, model_id, max_tokens) -> str
# Raises RuntimeError when the backend/model is unavailable; callers catch and
# degrade to their cloud path. Generation is serialized (one model in memory,
# both backends are single-tenant).

import os
import re
import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import find_local_model_path, GGUF_QUANT_PREFERENCE

_LOCK = threading.Lock()
_LOADED = [None]  # (model_id, backend, handle)


def backend_for(model_id):
    """Return "mlx" | "gguf" | "prism" for a model id/path, or None."""
    low = str(model_id).lower()
    if low.endswith(".gguf") or "gguf" in low:
        return "gguf"
    if "prism" in low or "ternary" in low or "bonsai" in low:
        return "prism"
    if "mlx" in low:
        return "mlx"
    p = Path(model_id).expanduser()
    if p.is_dir():
        if list(p.glob("*.gguf")):
            return "gguf"
        return "mlx"
    return None


def _resolve_gguf_dir(model_id):
    """Find the directory containing .gguf files for a model id."""
    p = Path(model_id).expanduser()
    if p.is_dir(): return p
    snap = find_local_model_path(model_id)
    if snap is not None and snap.is_dir(): return snap
    return None


def _resolve_gguf_path(model_id):
    """Find a concrete .gguf file: local file, dir, or HF cache snapshot.
    Quantization preference is case-insensitive (Q4_K_M preferred)."""
    p = Path(model_id).expanduser()
    if p.is_file():
        return p if p.suffix.lower() == ".gguf" else None
    roots = []
    if p.is_dir():
        roots.append(p)
    snap = find_local_model_path(model_id)
    if snap is not None and snap.is_dir():
        roots.append(snap)
    for root in roots:
        ggufs = sorted(x for x in root.glob("*.gguf"))
        if not ggufs:
            continue
        for rx in GGUF_QUANT_PREFERENCE:
            hits = [x for x in ggufs if re.search(rx, x.name.lower())]
            if hits:
                return hits[0]
        return ggufs[0]
    return None


def _load_prism(model_id):
    """Load a prism/ternary VLM model via mlx_vlm."""
    try:
        from mlx_vlm import load
        from mlx_vlm.prompt_utils import apply_chat_template
    except ImportError:
        raise RuntimeError("mlx-vlm not installed (pip install mlx-vlm)")
    model, processor = load(model_id)
    return model, processor


def _load(model_id):
    """Load the model. Returns (backend, handle). Raises RuntimeError."""
    backend = backend_for(model_id)
    if backend is None:
        raise RuntimeError(f"cannot determine local backend for '{model_id}'")
    if backend == "prism":
        if sys.platform != "darwin":
            raise RuntimeError(f"prism backend requires macOS (Apple Silicon); got {sys.platform}")
        return "prism", _load_prism(model_id)
    if backend == "mlx":
        if sys.platform != "darwin":
            raise RuntimeError(f"mlx backend requires macOS (Apple Silicon); got {sys.platform}")
        try:
            from mlx_lm import load
        except ImportError:
            raise RuntimeError("mlx-lm not installed (pip install mlx-lm)")
        return "mlx", load(model_id)
    root = _resolve_gguf_dir(model_id)
    if root is None:
        raise RuntimeError(f"no .gguf files found for '{model_id}'")
    import re as _re
    from fabric_config import GGUF_QUANT_PREFERENCE
    # try each root-level .gguf in quantization-preference order
    candidates = sorted(root.glob("*.gguf")) if root.is_dir() else [root]
    ordered = []
    for rx in GGUF_QUANT_PREFERENCE:
        hits = [f for f in candidates if _re.search(rx, f.name.lower())]
        for h in hits:
            if h not in ordered: ordered.append(h)
    for f in candidates:
        if f not in ordered: ordered.append(f)
    if not ordered:
        raise RuntimeError(f"no .gguf file found for '{model_id}'")

    try:
        from llama_cpp import Llama
    except ImportError:
        raise RuntimeError("llama-cpp-python not installed (pip install llama-cpp-python)")

    n_ctx = int(os.environ.get("WIKI_LOCAL_N_CTX", "16384"))
    last_error = None
    for path in ordered:
        try:
            llm = Llama(model_path=str(path), n_ctx=n_ctx, n_gpu_layers=-1, verbose=False)
            print(f"  gguf: loaded {path.name}", file=sys.stderr)
            return "gguf", llm
        except (ValueError, RuntimeError) as e:
            last_error = e
            print(f"  gguf: {path.name} failed ({e}) — trying next", file=sys.stderr)
    raise RuntimeError(
        f"No GGUF variant of '{model_id}' could be loaded. Last error: {last_error}. "
        f"Prism ternary models may require a llama.cpp build with prism quantization support, "
        f"or use the MLX variant on macOS.")


def _apply_template(prompt, tokenizer):
    """mlx: wrap the raw prompt in the model's chat template. The
    reasoning_effort kwarg is the supported knob for templates that accept it
    (qwen3_5 hardcodes xhigh without a system message); ignored otherwise."""
    try:
        return tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True,
            reasoning_effort=os.environ.get("WIKI_MLX_REASONING", "low"),
        )
    except Exception:
        return prompt


def _gguf_chat_or_complete(handle, prompt, max_tokens):
    """GGUF: chat-tuned models (gemma etc.) return empty text from raw
    completion without their turn markers. Use create_chat_completion (applies
    the model's built-in template); fall back to raw completion when a model
    has no template (base completions models)."""
    try:
        r = handle.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens, temperature=0.1)
        msg = r["choices"][0]["message"]
        return msg.get("content") or "" if isinstance(msg, dict) else (msg.content or "")
    except (KeyError, TypeError, ValueError):
        # no chat template: base completion model — raw path
        return handle.create_completion(
            prompt=prompt, max_tokens=max_tokens, temperature=0.1,
        )["choices"][0]["text"]


def generate(prompt, model_id, max_tokens=4096):
    """Run a single completion on the on-device backend. Serialized: one model
    in memory, single-tenant backends (mlx-lm and llama-cpp are not thread-safe
    on a shared instance)."""
    with _LOCK:
        if _LOADED[0] is None or _LOADED[0][0] != model_id:
            t0 = time.time()
            backend, handle = _load(model_id)
            _LOADED[0] = (model_id, backend, handle)
            print(f"local[{backend}]: loaded {model_id} in {time.time()-t0:.0f}s",
                  file=sys.stderr)
        _, backend, handle = _LOADED[0]
        if backend == "prism":
            from mlx_vlm.prompt_utils import apply_chat_template
            model, processor = handle
            formatted = apply_chat_template(processor, model.config, prompt)
            from mlx_vlm import generate as vlm_generate
            result = vlm_generate(model, processor, prompt=formatted,
                                  max_tokens=max_tokens, verbose=False)
            out = result.text if hasattr(result, "text") else str(result)
        elif backend == "mlx":
            from mlx_lm import generate as mlx_generate
            mlx_model, tok = handle
            out = mlx_generate(mlx_model, tok, prompt=_apply_template(prompt, tok),
                               max_tokens=max_tokens, verbose=False)
        else:
            out = _gguf_chat_or_complete(handle, prompt, max_tokens)
        return out