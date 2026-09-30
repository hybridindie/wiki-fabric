#!/usr/bin/env python3
"""wiki_lib/tombstones.py — rejected-proposal buffer (#140 / SkillOpt-epic S3).

Rejected proposals become first-class negative evidence:
  - `_inbox` rejects write a tombstone page (reason + cluster signature)
    instead of deleting the candidate.
  - Rejected promotion dossiers get a tombstone too (they already persist with
    status: rejected, but nothing told the miner).
  - `mine-promotions.py` reads active tombstones and suppresses matching
    clusters (skipped, with the tombstone named in the report).

A tombstone's `suppressed:` list records every matching cluster observed later
— an audit trail of suppression, reviewable and overturnable by a human.
"""

import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from wf_common import parse_frontmatter

TOMBSTONE_DIR_NAME = "patterns/_rejected"


def tombstone_dir(vault_root):
    return Path(vault_root) / TOMBSTONE_DIR_NAME


def _sig_tokens(text):
    """Normalized token bag for cluster matching (deterministic, 0 tokens)."""
    words = re.findall(r"[a-z]{4,}", (text or "").lower())
    stop = {"that", "this", "with", "from", "have", "when", "then", "were",
            "been", "into", "over", "under", "their", "them", "these", "those",
            "about", "after", "before", "while", "which", "would", "there"}
    return {w for w in words if w not in stop}


def write_tombstone(vault_root, source, source_id, reason, sig_tokens, actor_str):
    """Persist a rejection tombstone. Returns the tombstone path. The id is
    the source id minus its own type prefix (pattern-/promotion-)."""
    d = tombstone_dir(vault_root)
    d.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    tokens = " ".join(sorted(sig_tokens))
    short = re.sub(r"^(pattern-|promotion-|anti-pattern-)", "", source_id)
    text = (f"---\ntype: rejection-tombstone\nid: tombstone-{short}\n"
            f"source: {source}\n"
            f"rejected_at: \"{now}\"\n"
            f"rejected_by: \"{actor_str}\"\n"
            f"reason: \"{reason.strip()[:200]}\"\n"
            f"signature: \"{tokens}\"\n"
            f"status: active\n---\n\n"
            f"# Tombstone: {short}\n\n"
            f"Rejected ({source}). Reason: {reason.strip()}\n\n"
            f"Signature: {tokens}\n")
    p = d / f"tombstone-{short}.md"
    p.write_text(text, encoding="utf-8")
    return p


def load_active(vault_root):
    """Active tombstones: [(id, signature_tokens, reason, path)]."""
    d = tombstone_dir(vault_root)
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("tombstone-*.md")):
        fm, _ = None, None
        try:
            from wf_common import parse_frontmatter as _pf
            fm, body = _pf(p)
        except Exception:
            continue  #continue  # unparseable tombstone → ignored (active-only filter below)
        if not fm or str(fm.get("status", "")).lower() != "active":
            continue
        sig = set(re.findall(r"[a-z]{4,}", str(fm.get("signature", ""))))
        if sig:
            out.append((p.stem.replace("tombstone-", ""),
                        sig, str(fm.get("reason", "")), p))
    return out


def match_cluster(event_texts, tombstones, threshold=0.25):
    """Does this cluster match an active tombstone? Returns (tombstone_id, jaccard)
    for the best match above threshold, else (None, 0)."""
    cluster_tokens = set()
    for t in event_texts:
        cluster_tokens |= _sig_tokens(t)
    if not cluster_tokens:
        return None, 0.0
    best, best_j = None, 0.0
    for tid, sig, reason, path in tombstones:
        inter = len(cluster_tokens & sig)
        union = len(cluster_tokens | sig)
        j = inter / union if union else 0.0
        if j > best_j:
            best, best_j = tid, j
    if best_j >= threshold:
        return best, best_j
    return None, best_j


def annotate_suppressed(tombstone_path, cluster_key, event_slugs):
    """Record a suppression hit on the tombstone (the buffer stays reviewable)."""
    text = tombstone_path.read_text(encoding="utf-8", errors="replace")
    entry = (f"\n## Suppressed {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
             f"- cluster: {cluster_key}\n"
             f"- events: {', '.join(event_slugs)}\n")
    if "## Suppressions" not in text:
        text = text.rstrip("\n") + "\n\n## Suppressions\n" + entry
    else:
        text = text.rstrip("\n") + "\n" + entry
    tombstone_path.write_text(text, encoding="utf-8")