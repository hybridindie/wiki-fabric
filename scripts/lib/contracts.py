#!/usr/bin/env python3
# contracts.py — the single behavioral rule-sets that more than one gate
# enforces (#151).
#
# SkillOpt S4 SLOW-REGION: a pattern's applicability/counterexamples are the
# durable negative knowledge. Two gates must agree on "did protected content
# change?" — check_slow_regions (lint, pre-commit) and the change-set apply
# gate. When the rule lived in a verb script (lint) and a grep copy
# (apply_changeset), a merge could pass one gate and fail the other.
# Everyone imports from here.

import json as _json
import re as _re

PROTECTED_FIELDS = ("applicability", "counterexamples")  # SkillOpt S4 slow lane


def protected_fingerprint(fm):
    """Deterministic fingerprint of a pattern's slow-lane content.
    None when the page carries no protected content."""
    payload = {}
    for f in PROTECTED_FIELDS:
        v = (fm or {}).get(f)
        if v not in (None, [], {}):
            payload[f] = v
    if not payload:
        return None
    import hashlib
    return hashlib.sha256(
        _json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()[:16]


def slow_update_justified(fm):
    """True when the page's own verified list carries a slow-update approval."""
    if isinstance((fm or {}).get("verified"), list):
        for v in fm["verified"]:
            if isinstance(v, dict) and "slow-update" in str(v.get("reason", "")):
                return True
    return False


def protected_content_changed_and_unjustified(old_fm, new_fm):
    """The SLOW-REGION rule both gates must agree on (#151):
    protected content changed vs the committed version AND no slow-update
    justification in the new frontmatter."""
    fp_old = protected_fingerprint(old_fm)
    fp_new = protected_fingerprint(new_fm)
    if fp_old is None or fp_old == fp_new:
        return False
    return not slow_update_justified(new_fm)