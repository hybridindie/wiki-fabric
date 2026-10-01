#!/usr/bin/env python3
"""embed_index.py — hash-gated local embedding index for query re-rank (#12).

Optional ML tier, off by default (integrations.embeddings.enabled). The index
lives in registry/embed-index.json: {content_hash, model, vectors: {id: [...]}}.
Rebuilt only when the corpus content hash changes (same no-op discipline as
the wiki export manifest). Fully offline (fastembed ONNX); never a network
call at query time — if the model isn't cached, the tier reports unavailable
and the lexical+graph retriever stands alone.

Deterministic per (corpus state, model): same corpus + model ⇒ same vectors.
"""

import sys
import json
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

MODEL_DEFAULT = "sentence-transformers/all-MiniLM-L6-v2"


def _corpus_fingerprint(corpus_root):
    """Content hash over claim statement+id — the index's no-op gate."""
    from wf_common import claim_statement
    h = hashlib.sha256()
    n = 0
    from layout import claims
    for p in sorted(claims(corpus_root).glob("claim-*.md")):
        h.update(p.stem.encode())
        h.update(claim_statement(p).encode())
        n += 1
    return h.hexdigest()[:16], n


def _index_path(corpus_root):
    return Path(corpus_root) / "registry" / "embed-index.json"


def load_or_build(corpus_root, model_name=None, rebuild=False):
    """Returns (model, vectors: dict[id -> np.array], source: 'cache'|'built'|'unavailable').
    Never raises — a missing optional tier must not break retrieval."""
    try:
        import numpy as np
        from fastembed import TextEmbedding
    except ImportError as e:
        return None, {}, f"unavailable ({e.name}: pip install fastembed numpy)"
    corpus_root = Path(corpus_root)
    model_name = model_name or MODEL_DEFAULT
    fp, n = _corpus_fingerprint(corpus_root)
    ipath = _index_path(corpus_root)
    if not rebuild and ipath.exists():
        try:
            d = json.loads(ipath.read_text(encoding="utf-8"))
            if d.get("content_hash") == fp and d.get("model") == model_name:
                vecs = {k: np.array(v, dtype=float) for k, v in d["vectors"].items()}
                return None, vecs, "cache"   # model not needed for scoring
        except Exception:
            pass  # corrupt index → rebuild
    # build
    from wf_common import claim_statement
    texts, ids = [], []
    from layout import claims
    for p in sorted(claims(corpus_root).glob("claim-*.md")):
        st = claim_statement(p)
        if len(st) > 20:
            texts.append(st)
            ids.append(p.stem)
    if len(texts) < 2:
        return None, {}, "unavailable (too few claims)"
    try:
        model = TextEmbedding(model_name=model_name)
        vectors = {i: [float(x) for x in v] for i, v in zip(ids, model.embed(texts))}
    except Exception as e:
        return None, {}, f"unavailable (model load: {e})"
    if not rebuild:
        ipath.parent.mkdir(parents=True, exist_ok=True)
        ipath.write_text(json.dumps({"content_hash": fp, "model": model_name,
                                     "n": n, "vectors": vectors}, sort_keys=True) + "\n",
                         encoding="utf-8")
    return None, {k: np.array(v, dtype=float) for k, v in vectors.items()}, "built"


def cosine_top(scores_q, vectors, k=10):
    """Rank claim ids by cosine to the query vector. vectors values may be
    lists or arrays."""
    import numpy as np
    if scores_q is None or not vectors:
        return []
    q = np.asarray(scores_q)
    out = []
    for cid, v in vectors.items():
        v = np.asarray(v)
        denom = (np.linalg.norm(q) * np.linalg.norm(v)) or 1e-9
        out.append((float(np.dot(q, v) / denom), cid))
    out.sort(key=lambda x: -x[0])
    return out[:k]


def embed_query(text, model_name=None):
    """Query-side embedding (loads the model on demand; cached by fastembed)."""
    try:
        from fastembed import TextEmbedding
        return list(TextEmbedding(model_name=model_name or MODEL_DEFAULT).embed([text]))[0]
    except Exception:
        return None