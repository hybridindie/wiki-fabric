"""Single truth for corpus layout segment names (Tier-2 layout module).

Every second-level content dir is declared ONCE here as a segment tuple;
producers/consumers compose their paths via the accessors instead of
re-spelling "evidence/claims"-style literals at each use site (~250 composed
joins / ~120 bare literals were the cost of renaming before this module).

Layout conventions (docs/site/corpus-layout.md is the canonical doc):
  evidence/    captures + derivatives: raw/ (immutable), sources/,
               source-summaries/, claims/, insights/, traces/, _inbox/
  patterns/    canonical patterns + _inbox/ (staged) + _rejected/ (tombstones)
  anti-patterns/, skills/, concepts/, domains/, projects/ — canonical atoms
  registry/    machine-written indexes + receipts + effects (deterministic
               verdict artifacts live here, never beside pages)
  global/      entities/ + graphs/ (derived, gitignored)
  syntheses/, questions/ — gated synthesis + harvested questions

Accessors take an explicit `root` (a Path). Passing None falls back to
fabric_config.CORPUS_ROOT resolved AT CALL TIME — command modules keep
their monkeypatchable module-level roots (tests patch e.g. ingest.VAULT_ROOT
and pass it in), so no import-time freezing.
"""
from pathlib import Path

# name -> path segments relative to the corpus root. Names mirror usage
# (prefix constants below are the naming-convention contract).
SEGMENTS = {
    "evidence": ("evidence",),
    "evidence_raw": ("evidence", "raw"),
    "evidence_raw_git": ("evidence", "raw"),  # leaf <slug>/git/ appended by capture-git
    "evidence_sources": ("evidence", "sources"),
    "evidence_source_summaries": ("evidence", "source-summaries"),
    "evidence_claims": ("evidence", "claims"),
    "evidence_insights": ("evidence", "insights"),
    "evidence_traces": ("evidence", "traces"),
    "evidence_traces_change_sets": ("evidence", "traces", "change-sets"),
    "evidence_traces_wiki_runs": ("evidence", "traces", "wiki-runs"),
    "evidence_inbox": ("evidence", "_inbox"),
    "evidence_experiments": ("evidence", "experiments"),
    "patterns": ("patterns",),
    "patterns_inbox": ("patterns", "_inbox"),
    "patterns_rejected": ("patterns", "_rejected"),
    "anti_patterns": ("anti-patterns",),
    "skills": ("skills",),
    "concepts": ("concepts",),
    "domains": ("domains",),
    "projects": ("projects",),
    "registry": ("registry",),
    "registry_effects": ("registry", "effects"),
    "registry_receipts": ("registry", "receipts"),
    "registry_promotions": ("registry", "promotions"),
    "global": ("global",),
    "global_entities": ("global", "entities"),
    "global_graphs": ("global", "graphs"),
    "syntheses": ("syntheses",),
    "questions": ("questions",),
}

# Page-id prefixes (the naming contract rebuild-index/lint/promote assume).
PREFIXES = {
    "source": "src-",
    "source_summary": "sum-",
    "claim": "claim-",
    "insight": "insight-",
    "experience_event": "ee-",
    "pattern": "pattern-",
    "anti_pattern": "anti-pattern-",
    "concept": "concept-",
    "promotion_dossier": "promotion-",
    "tombstone": "tombstone-",
    "entity": "entity-",
    "question": "question-",
    "change_set": "change-set-",
    "receipt": "receipt-",
}


def _resolve_root(root):
    if root is not None:
        return Path(root)
    try:
        from fabric_config import CORPUS_ROOT
        return Path(CORPUS_ROOT)
    except Exception:
        raise RuntimeError("layout: no root passed and fabric_config unavailable")


def seg(name):
    """Path segments for a declared dir id (KeyError on unknown — the point)."""
    if name not in SEGMENTS:
        raise KeyError(f"layout: undeclared dir {name!r} — add it to SEGMENTS, "
                       f"never re-spell corpus paths at call sites")
    return Path(*SEGMENTS[name])


def make(root, name):
    """<root>/<declared dir> (mkdir parents handled by callers)."""
    return _resolve_root(root) / seg(name)


def evidence(root=None):          return make(root, "evidence")
def evidence_raw(root=None):      return make(root, "evidence_raw")
def sources(root=None):           return make(root, "evidence_sources")
def source_summaries(root=None):  return make(root, "evidence_source_summaries")
def claims(root=None):            return make(root, "evidence_claims")
def insights(root=None):          return make(root, "evidence_insights")
def change_sets(root=None):       return make(root, "evidence_traces_change_sets")
def wiki_runs(root=None):         return make(root, "evidence_traces_wiki_runs")
def evidence_inbox(root=None):    return make(root, "evidence_inbox")
def evidence_experiments(root=None): return make(root, "evidence_experiments")
def patterns(root=None):          return make(root, "patterns")
def patterns_inbox(root=None):    return make(root, "patterns_inbox")
def patterns_rejected(root=None): return make(root, "patterns_rejected")
def anti_patterns(root=None):     return make(root, "anti_patterns")
def skills(root=None):            return make(root, "skills")
def concepts(root=None):          return make(root, "concepts")
def domains(root=None):           return make(root, "domains")
def projects(root=None):          return make(root, "projects")
def registry(root=None):          return make(root, "registry")
def effects(root=None):           return make(root, "registry_effects")
def receipts(root=None):          return make(root, "registry_receipts")
def promotions(root=None):        return make(root, "registry_promotions")
def global_entities(root=None):   return make(root, "global_entities")
def global_graphs(root=None):     return make(root, "global_graphs")
def syntheses(root=None):         return make(root, "syntheses")
def questions(root=None):         return make(root, "questions")


def raw_slug_dir(root, slug, *leaf):
    """evidence/raw/<slug>[/<leaf...>] — the capture tree (git/, chats/,
    obsidian/ leaves). Single truth for the shape ingest's slug-join depends
    on (src-<slug> == raw rel path)."""
    return evidence_raw(root) / slug / Path(*leaf) if leaf else evidence_raw(root) / slug


def claims_for_source(root, source_slug):
    """claim-<source_slug>-*.md glob pattern — the ingest/lint/promote join
    contract (source_slug is the raw rel path, <=80 chars)."""
    return claims(root) / f"{PREFIXES['claim']}{source_slug}-*.md"