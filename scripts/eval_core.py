#!/usr/bin/env python3
# eval_core.py — Shared scoring primitives for the eval harnesses.
#
# The graphify audit found five eval harnesses (eval.py, eval-stability.py,
# eval-behavior.py, eval-pr-replay.py, eval-real-repo.py) each carrying their
# own fuzzy-matching vocabulary. This module holds the primitives that were
# duplicated or subtly drifting:
#   STOPWORDS        — shared stopword set (query.py concept scoring + eval.py)
#   concept_match    — golden-key coverage check (was eval.py-only, query-consistent)
#   jaccard          — set similarity (was eval-stability)
#   fuzzy_coverage   — mean-best-Jaccard coverage (was eval-stability)
#   tokens           — stemming-ish token set (was eval-pr-replay)
#
# Pure functions, stdlib-only: harnesses stay independently runnable.

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wf_common import norm

STOPWORDS = {
    "the", "a", "an", "is", "of", "to", "in", "and", "or", "for", "on",
    "with", "at", "by", "from", "that", "this", "it", "as", "be", "are",
    "makes", "produces", "yields", "gives", "fails", "crashes",
}


def concept_match(golden_key, statement):
    """Loose semantic match: check for key concept overlap.
    Previously in eval.py; kept behavior-identical (golden corpus depends on it)."""
    gk_n = norm(golden_key)
    stmt_n = norm(statement)

    # 1. Exact substring
    if gk_n in stmt_n:
        return True

    # 2. All-words substring
    gk_words = set(gk_n.split())
    if gk_words and gk_words.issubset(set(stmt_n.split())):
        return True

    # 3. Concept overlap: distinctive words (skip stopwords) must cover >= 0.6
    gk_content = gk_words - STOPWORDS
    stmt_words = set(stmt_n.split())
    if gk_content:
        overlap = len(gk_content & stmt_words) / len(gk_content)
        if overlap >= 0.6:
            return True

    return False


def jaccard(a, b):
    """Token-set Jaccard similarity. Two empty sets are identical (1.0)."""
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def fuzzy_coverage(source_set, target_set, threshold=0.7):
    """Mean best token-Jaccard of each source statement against target_set —
    robust to minor wording drift that exact-set Jaccard over-penalizes."""
    src = {s: set(s.split()) for s in source_set}
    tgt = {s: set(s.split()) for s in target_set}
    if not src:
        return 1.0
    vals = []
    for toks in src.values():
        best = 0.0
        for tt in tgt.values():
            u = len(toks | tt)
            if u:
                best = max(best, len(toks & tt) / u)
        vals.append(best)
    return sum(vals) / len(vals) if vals else 0.0


def tokens(text):
    """Stemming-ish token set for term-coverage scoring (was eval-pr-replay)."""
    out = set()
    for w in re.findall(r"[a-z0-9][a-z0-9_-]{3,}", (text or "").lower()):
        out.add(w)
        for suf, add in (("tion", ""), ("ting", ""), ("ing", "e"), ("ed", "e"), ("s", "")):
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                out.add(w[: -len(suf)])
                if add:
                    out.add(w[: -len(suf)] + add)
                break
    return out