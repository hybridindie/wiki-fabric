#!/usr/bin/env python3
# ingest.py — Ingest a raw source into the evidence fabric
#
# Usage: python3 scripts/cmd/ingest.py <source-path> [--project PROJECT] [--dry-run] [--extract-claims]
#
# LLM configuration (env vars):
#   WIKI_LLM_BASE_URL   — OpenAI-compatible base URL (default: http://localhost:11434/v1 for Ollama)
#   WIKI_LLM_API_KEY    — API key (default: "ollama"; Ollama ignores it)
#   WIKI_LLM_MODEL      — model name (default: qwen2.5-coder:7b)

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import os
import time
import re
import hashlib
import json
import subprocess
from pathlib import Path
from datetime import date

from fabric_config import get_config, VAULT_ROOT, actor, get_stage_route, is_local_route, ensure_local_model, get_local_model
# Extraction layer lives in extract_backends (prompt, LLM backends, JSON
# parsing/repair, locator verification). Re-exported here for backward
# compatibility (tests + synthesize/eval import from ingest).
from extract_backends import (
    CLAIM_PROMPT, CLAIM_KEY_MAP, number_lines, build_prompt, llm_config,
    _normalize_for_match, repair_quote, verify_and_fix_locators,
    _json_repair_load, parse_json_array,
    extract_claims_mlx, extract_claims_openai_compatible,
    extract_claims_anthropic, extract_claims_opencode, extract_claims,
)
import extract_backends as _eb
_EXTRACTION_MODEL = _eb._EXTRACTION_MODEL

# Alias: ingest_source() has a bool parameter named extract_claims that shadows
# the function inside its scope — reference the function via this alias.
extract_claims_fn = extract_claims

_MLX_ENSURE_DONE = False

import threading as _threading
from wf_common import slugify, yaml_scalar, sha256_file as sha256, now_iso_utc as _dt_iso
import layout as _layout
# thin aliases: call sites pass VAULT_ROOT explicitly (module attr stays
# monkeypatchable for tests), helpers resolve roots at call time. `claims_dir`
# (not `claims`) — ingest_source() has a local claims list by that name.
evidence_raw = _layout.evidence_raw
sources = _layout.sources
source_summaries = _layout.source_summaries
claims_dir = _layout.claims
claims_for_source = _layout.claims_for_source
change_sets = _layout.change_sets
registry = _layout.registry
_LOG_LOCK = _threading.Lock()

# main() sets this from argv (global). Module-level default so ingest_source()
# stays callable as a library entry point (tests, evals) without a NameError.
args_dry_run = False



def find_project_namespace(vault_root):
    overlay_path = vault_root / ".wiki-overlay.md"
    if not overlay_path.exists():
        return "default-project"
    text = overlay_path.read_text()
    m = re.search(r"namespace:\s*(\S+)", text)
    return m.group(1) if m else "default-project"


def clean_quote(quote):
    """Strip L<n>: line-number prefixes that the LLM may have copied from the numbered source."""
    if not quote:
        return ""
    # Remove leading L<n>: from the start and any mid-quote L<n>: artifacts
    cleaned = re.sub(r'L\d+:', '', quote)
    # Collapse whitespace artifacts from removed prefixes
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned




def provenance_relations(source_slug, source_path):
    """#79: evidence-plane provenance edges on claims.

    The source the claim came from is already known at ingest time — record
    the typed link instead of emitting relations: []. Chat captures get
    originated_in (the claim originated in that conversation); PR/issue
    captures get decided_in (the PR is where the decision/fix landed);
    doc captures stay edge-less (their provenance is the source_refs block).
    Provenance only — never a second truth layer; targets are evidence pages.
    """
    rel = {"type": "originated_in", "target": f"[[src-{source_slug}]]"}
    p = str(source_path).replace("\\", "/")
    if "/git/pr-" in p or "/git/issue-" in p:
        rel = {"type": "decided_in", "target": f"[[src-{source_slug}]]"}
    elif "/chats/" in p:
        rel = {"type": "originated_in", "target": f"[[src-{source_slug}]]"}
    else:
        return []
    return [rel]


def stale_mark_derived_claims(source_path, file_hash, dry_run=None):
    """sha256-drift → mechanical staleness trigger.

    When an existing source record for this raw path carries a DIFFERENT
    sha256, the source re-captured (PR updated, issue got comments, doc
    changed) and every claim derived from the old revision is derived from
    evidence that no longer exists. Stamps stale_after=today and flips
    status → contested on those claims — consumer gates (wf context, wf
    export, lint STALE-AFTER / REVIEW-AFTER) then exclude/hint until the new
    revision is ingested and the claims re-verified. Deterministic, 0 tokens;
    dry_run defaults to the module args_dry_run."""
    if dry_run is None:
        dry_run = args_dry_run
    sources_dir = sources(VAULT_ROOT)
    if not sources_dir.exists():
        return 0
    try:
        target_norm = source_path.resolve().as_posix()
    except OSError:
        target_norm = Path(str(source_path)).as_posix()
    today = date.today().isoformat()
    stamped = 0
    for rec in sorted(sources_dir.glob("src-*.md")):
        text = rec.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^sha256:\s*([a-f0-9]{64})\s*$", text, re.MULTILINE)
        if not m or m.group(1) == file_hash:
            continue  # same revision → is_already_ingested anti-loop handles it
        sm = re.search(r'^source_path:\s*"?([^"\n]+)"?\s*$', text, re.MULTILINE)
        if not sm:
            continue
        raw_path = VAULT_ROOT / sm.group(1).strip()
        try:
            same = raw_path.resolve() == Path(target_norm).resolve()
        except OSError:
            same = raw_path.as_posix() == target_norm
        if not same:
            continue
        # this record is the previous revision of the same raw path →
        # stale its claims. The new revision's record is written fresh below.
        for cp in claims_dir(VAULT_ROOT).glob(claims_for_source(VAULT_ROOT, rec.stem[4:]).name):
            cs = cp.read_text(encoding="utf-8", errors="replace")
            if "stale_after:" in cs:
                continue
            flipped = re.sub(r"^status: (?:supported|proposed)$",
                             f"stale_after: {today}\nstatus: contested",
                             cs, count=1, flags=re.MULTILINE)
            if flipped == cs:
                continue
            cp.write_text(flipped, encoding="utf-8")
            stamped += 1
        break  # one record matches this raw path
    if stamped:
        print(f"Stale-stamped {stamped} claim(s) from the previous revision of "
              f"{source_path.name} (sha256 drift → contested + stale_after; 0 tokens)")
    return stamped


def sanitize_wikilinks(text):
    """LLM text may contain shell/code fragments like [[ "$x" == "y" ]] which
    lint parses as wikilinks (broken → error, gates the commit). Body prose
    in claim pages is NOT a link; escape the double bracket."""
    return text.replace("[[", "\\[\\[")


def claim_frontmatter(claim, source_slug, idx, provenance=None):
    quote = clean_quote(claim.get('quote', ''))
    statement = claim.get('statement', '')
    rels = list(provenance or [])
    if rels:
        rel_lines = "\n".join(
            f"  - type: {r['type']}\n    target: \"{r['target']}\"" for r in rels)
        relations_block = f"relations:\n{rel_lines}"
    else:
        relations_block = "relations: []"
    return f"""---
type: claim
id: claim-{source_slug}-{idx:03d}
statement: {yaml_scalar(statement)}
description: {yaml_scalar(statement[:140])}
resource: "[[src-{source_slug}]]"
generated: {{ by: "{actor(get_config(), 'agent', model=_EXTRACTION_MODEL[0])}", at: "{_dt_iso()}" }}
verified:
  - by: "{actor(get_config(), 'process', model='locator-verification')}"
    at: "{_dt_iso()}"
status: {claim.get('st', claim.get('status', 'proposed'))}
confidence: {claim.get('conf', claim.get('confidence', 'medium'))}
evidence_strength: {claim.get('ev', claim.get('evidence_strength', 'primary'))}
source_refs:
  - source: "[[src-{source_slug}]]"
    locator: {yaml_scalar(claim.get('loc', claim.get('locator', 'N/A')))}
    quote: {yaml_scalar(quote)}
    supports: true
last_verified: {date.today().isoformat()}
{relations_block}
---

# claim-{source_slug}-{idx:03d}

{sanitize_wikilinks(statement)}
"""


def is_already_ingested(source_path, file_hash):
    """Check if a source record with this sha256 already exists (anti-loop)."""
    sources_dir = sources(VAULT_ROOT)
    if not sources_dir.exists():
        return False
    for rec in sources_dir.glob("src-*.md"):
        if re.search(rf"sha256:\s*{re.escape(file_hash)}", rec.read_text(encoding="utf-8", errors="replace")):
            return rec
    return None


def find_pending_sources(project_slug):
    """Return raw files whose source record is status: pending (recorded but
    never claim-extracted). Complements find_changed_sources: --changed handles
    NEW/CHANGED files, --pending handles recorded-but-unextracted ones without
    tripping the anti-loop."""
    return _sources_with_status(project_slug, "pending")


def _sources_with_status(project_slug, status):
    """Source records for a project with the given status, resolved to their
    raw paths. Shared by --pending and --reclaim (#93)."""
    raw_dir = evidence_raw(root=VAULT_ROOT) / project_slug
    if not raw_dir.exists():
        return []
    pending_paths = set()
    sources_dir = sources(VAULT_ROOT)
    if sources_dir.exists():
        for rec in sources_dir.glob("src-*.md"):
            text = rec.read_text(encoding="utf-8", errors="replace")
            if f"status: {status}" not in text:
                continue
            m = re.search(r"source_path:\s*(.+)", text)
            if not m:
                continue
            sp = m.group(1).strip()
            # Scope to this project's raw subtree
            if f"evidence/raw/{project_slug}/" in sp or f"evidence/raw/{project_slug}/" in sp.replace("_", "-"):
                pending_paths.add(sp)
    pending = []
    for rel in sorted(pending_paths):
        f = VAULT_ROOT / rel
        if f.exists():
            pending.append(f)
    return pending


def find_orphaned_sources(project_slug):
    """#93 recovery: sources recorded as `ingested` but with zero claim files
    (claim-<slug>-*.md). Silent orphans from the pre-fix resume flip or an
    outage — recoverable by flipping back to pending (--reclaim)."""
    claims_glob = claims_dir(VAULT_ROOT)
    orphans = []
    for rec in _sources_with_status(project_slug, "ingested"):
        # rec is the raw file path; find its record to get the slug
        text_of = rec
        slug = None
        try:
            rel = rec.relative_to(evidence_raw(VAULT_ROOT))
            slug = slugify(rel.as_posix())[:80]
        except ValueError:
            slug = slugify(rec.name)[:80]
        rec_path = sources(VAULT_ROOT) / f"src-{slug}.md"
        if rec_path.exists() and not list(claims_glob.glob(f"claim-{slug}-*.md")):
            orphans.append((rec_path, rec))
    return orphans


def reclaim_orphans(project_slug, dry_run=False):
    """Flip zero-claim `ingested` records back to `status: pending` (#93).
    Mechanical, 0 tokens — after this, `--pending` picks them up normally."""
    orphans = find_orphaned_sources(project_slug)
    if not orphans:
        print(f"No orphaned sources for {project_slug} (ingested with zero claims)")
        return 0
    print(f"=== Reclaiming {len(orphans)} orphaned source(s) for {project_slug} ===")
    n = 0
    for rec_path, raw in orphans:
        if dry_run:
            print(f"  [dry-run] {rec_path.name} -> status: pending")
            n += 1
            continue
        text = rec_path.read_text(encoding="utf-8", errors="replace")
        rec_path.write_text(text.replace("status: ingested", "status: pending", 1),
                            encoding="utf-8")
        print(f"  reclaimed: {rec_path.name} (raw: {raw.name})")
        n += 1
    if not dry_run and n:
        print(f"\nNow run: wf ingest --pending {project_slug} --extract-claims")
    return n


def find_changed_sources(project_slug):
    """Return raw files that are NEW or CHANGED vs. their source records.

    Compares each file under evidence/raw/<slug>/ against every sha256 recorded
    in evidence/sources/. A file with no matching hash is new or changed.
    """
    raw_dir = evidence_raw(root=VAULT_ROOT) / project_slug
    if not raw_dir.exists():
        return []
    known_hashes = set()
    sources_dir = sources(VAULT_ROOT)
    if sources_dir.exists():
        for rec in sources_dir.glob("src-*.md"):
            m = re.search(r"sha256:\s*([a-f0-9]{64})", rec.read_text(encoding="utf-8", errors="replace"))
            if m:
                known_hashes.add(m.group(1))
    changed = []
    for f in sorted(raw_dir.rglob("*.md")):
        if sha256(f) not in known_hashes:
            changed.append(f)
    return changed


def ingest_source(source_path, extract_claims=False, model=None, dry_run=False, namespace=None):
    """Ingest one source file. `extract_claims` is a bool flag (shadows the module
    function of the same name inside its scope, hence the alias below)."""
    # /tmp vs /private/tmp (macOS): resolve BOTH sides through the filesystem
    # so relative_to never throws on symlinked prefixes (sim finding #10).
    source_path = source_path.resolve()
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}", file=sys.stderr)
        return False

    file_hash = sha256(source_path)
    print(f"Source: {source_path}")
    print(f"SHA256: {file_hash}")

    # Anti-loop: skip sources already ingested with the same hash — except
    # sources recorded with status: pending (never claim-extracted). Those are
    # completed by --pending mode: claims extracted, record flipped to ingested.
    # (A DIFFERENT hash on the same raw path means the source re-captured —
    # stale_mark_derived_claims() has mechanically stale-stamped that
    # revision's claims above, before any skip decision.)
    stale_mark_drift = stale_mark_derived_claims(source_path, file_hash)
    existing = is_already_ingested(source_path, file_hash)
    resuming = False
    if existing:
        rec_text = existing.read_text(encoding="utf-8", errors="replace")
        if "status: pending" in rec_text:
            resuming = True
            print(f"Resuming pending source {existing.name}")
        else:
            print(f"Skipped — already ingested as {existing.name} (matching sha256)")
            print("  (anti-loop: unchanged sources are never re-ingested. If claims are "
                  "missing, run: wf ingest --pending <project> --extract-claims)")
            return False

    namespace = namespace or find_project_namespace(Path.cwd())
    print(f"Project namespace: {namespace}")

    try:
        rel_path = source_path.relative_to(evidence_raw(VAULT_ROOT))
        source_slug = slugify(rel_path.as_posix())
    except ValueError:
        source_slug = slugify(source_path.name)
    source_slug = source_slug[:80]

    source_record_path = sources(VAULT_ROOT) / f"src-{source_slug}.md"
    summary_path = source_summaries(VAULT_ROOT) / f"sum-{source_slug}.md"
    change_dir = change_sets(VAULT_ROOT) / f"{date.today().isoformat()}-{source_slug}"

    print(f"\nSource record: {source_record_path}")
    print(f"Source summary: {summary_path}")
    print(f"Change-set: {change_dir}/")

    if args_dry_run:
        print("  (dry run — no files written)")
        return True

    # 1. Source record (skipped when resuming a pending source — it exists)
    title = source_path.stem.replace('-', ' ').replace('_', ' ').title()
    sources(VAULT_ROOT).mkdir(parents=True, exist_ok=True)
    if resuming:
        print("  (resuming — source record exists)")
    else:
        _actor = actor(get_config(), "agent")
        source_record_path.write_text(f"""---
type: source
title: {title}
description: "Captured upstream source: {title.lower()}"
generated: {{ by: "{_actor}", at: "{_dt_iso()}" }}
tags: []
resource: "evidence/raw/{source_path.relative_to(VAULT_ROOT / 'evidence' / 'raw').as_posix() if 'evidence/raw' in str(source_path) else source_path.name}"
source_path: evidence/raw/{source_path.relative_to(VAULT_ROOT / 'evidence' / 'raw').as_posix() if 'evidence/raw' in str(source_path) else source_path.name}
sha256: {file_hash}
captured: {date.today().isoformat()}
summary: "[[sum-{source_slug}]]"
status: pending
---

# {title}

Captured from `{source_path}` on {date.today().isoformat()}.

Faithful summary: [[sum-{source_slug}]].
""")

    # 2. Extract claims (optional)
    claims = []
    if extract_claims:
        print("Extracting claims via LLM...")
        source_text = source_path.read_text(encoding="utf-8", errors="replace")
        claims = extract_claims_fn(source_text, str(source_path), model)
        if claims:
            print(f"Extracted {len(claims)} claims")
        else:
            print("No claims extracted", file=sys.stderr)

    # 3. Write claim files
    claims_dir(VAULT_ROOT).mkdir(parents=True, exist_ok=True)
    for i, claim in enumerate(claims):
        claim_path = claims_dir(VAULT_ROOT) / f"claim-{source_slug}-{i:03d}.md"
        claim_path.write_text(claim_frontmatter(claim, source_slug, i,
                                                provenance=provenance_relations(source_slug, source_path)))
        print(f"  Claim {i+1}: {claim_path}")

    # 4. Summary
    source_summaries(VAULT_ROOT).mkdir(parents=True, exist_ok=True)
    claim_lines = "\n".join(
        f"- {c.get('statement', c.get('s', ''))[:80]} (locator: {c.get('locator', c.get('loc', 'N/A'))})"
        for c in claims
    ) if claims else "- claim 1 (locator)"

    if not resuming:
        _actor = actor(get_config(), "agent")
        summary_path.write_text(f"""---
type: source-summary
title: {title} — Summary
description: "Faithful summary of {source_path.name} with line locators"
generated: {{ by: "{_actor}", at: "{_dt_iso()}" }}
tags: []
source: "[[src-{source_slug}]]"
status: pending
created: {date.today().isoformat()}
---

# Summary

Faithful summary of {source_path.name}.

## Key claims

{claim_lines or '- claim 1 (locator)'}
""")

    # 4b. Resume: flip the source record to ingested once claims exist (#93).
    # A 0-claim resume stays pending — flipping it would orphan the source
    # (ingested + zero claims is indistinguishable from a claim-less doc, and
    # the anti-loop gate would block every retry). LLM outages, malformed
    # JSON, and reasoning-budget burnout all surface as empty claims.
    if resuming:
        if claims:
            rec = source_record_path.read_text(encoding="utf-8", errors="replace")
            rec = rec.replace("status: pending", "status: ingested")
            source_record_path.write_text(rec)
        else:
            print("  0 claims extracted — source stays pending (retry: wf ingest --pending <project> --extract-claims)",
                  file=sys.stderr)

    # 5. Change-set
    Path(change_dir).mkdir(parents=True, exist_ok=True)
    change_set_id = f"change-set-{date.today().isoformat()}-{source_slug}"
    created_files = [f"evidence/sources/src-{source_slug}.md",
                     f"evidence/source-summaries/sum-{source_slug}.md"]
    created_files += [f"evidence/claims/claim-{source_slug}-{i:03d}.md" for i in range(len(claims))]

    change_dir.joinpath("manifest.md").write_text(f"""---
type: change-set
id: {change_set_id}
title: "Ingest {source_path.name}"
date: {date.today().isoformat()}
status: open
scope: staging
---

# Change-Set: {source_path.name}

## Sources processed

| Source | raw file | sha256 | record |
|---|---|---|---|
| {source_path.name} | `evidence/raw/{source_path.relative_to(VAULT_ROOT / 'evidence' / 'raw').as_posix() if 'evidence/raw' in str(source_path) else source_path.name}` | `{file_hash[:12]}...` | `src-{source_slug}` |

## Pages created (staging)

""" + "\n".join(f"- `{f}`" for f in created_files) + f"""

## New claims

""" + ("\n".join(f"- {c.get('statement', c.get('s', ''))[:80]}" for c in claims) if claims else "_(none extracted)_") + f"""

## Lint

- Run: `python3 scripts/cmd/lint.py .`

## Log

`registry/log.md` → `## {date} / **ingest | <slug>**`
""")

    change_dir.joinpath("diff.md").write_text(f"""---
type: change-set-diff
title: "Diff for {source_path.name}"
date: {date.today().isoformat()}
parent: "[[{change_set_id}]]"
---

# Diff: {source_path.name}

## + created (staging)
```
""" + "\n".join(f"+ {f}" for f in created_files) + "\n```\n")

    print("Created source record, summary, change-set manifest and diff")

    # 6. Log
    log_path = registry(VAULT_ROOT) / "log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(
            "---\ntype: log\ntitle: Log\ncreated: {d}\nupdated: {d}\n---\n\n# Log\n\nAppend-only timeline.\n".replace("{d}", date.today().isoformat())
        )
    with _LOG_LOCK, open(log_path, "a") as f:
        f.write(f"\n## {date.today().isoformat()}\n* **ingest | {source_slug}**\n")
        f.write(f"- Ingested {source_path.name} (sha256 {file_hash[:12]}...)\n")
        f.write(f"- Extracted {len(claims)} claims\n")
        f.write(f"- Change-set: {change_dir}\n")

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest a raw source into the evidence fabric")
    parser.add_argument("source", nargs="?", help="Path to source file under evidence/raw/")
    parser.add_argument("--changed", metavar="PROJECT", help="Ingest all NEW/CHANGED raw files for a project slug (vs. recorded sha256s)")
    parser.add_argument("--pending", metavar="PROJECT", help="Claim-extract all recorded-but-pending sources for a project slug (anti-loop safe)")
    parser.add_argument("--reclaim", metavar="PROJECT", help="Flip zero-claim ingested sources back to pending (#93 recovery; 0 tokens)")
    parser.add_argument("--project", help="Project namespace (from .wiki-overlay.md)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing")
    parser.add_argument("--extract-claims", action="store_true", help="Extract claims using LLM")
    parser.add_argument("--model", default=None, help="LLM model (default: $WIKI_LLM_MODEL or qwen2.5-coder:7b)")
    parser.add_argument("--workers", type=int, default=int(os.environ.get("WIKI_INGEST_WORKERS", "1")),
                        help="Concurrent extraction threads (default 1; cloud tiers tolerate 6-12)")
    args = parser.parse_args()

    global args_dry_run
    args_dry_run = args.dry_run

    if args.reclaim:
        n = reclaim_orphans(args.reclaim, dry_run=args.dry_run)
        sys.exit(0 if n or not find_orphaned_sources(args.reclaim) else 1)

    if args.pending:
        project = args.pending
        # stage routing: extract sees raw docs — per-repo privacy override
        if not args.model and not os.environ.get("WIKI_LLM_BACKEND"):
            _cfg = get_config()
            _model = get_stage_route(_cfg, project, "extract")
            if is_local_route(_cfg, project, "extract"):
                os.environ["WIKI_LLM_BACKEND"] = "mlx"
                ensure_local_model(_model, config=_cfg)  # before workers spawn
            args.model = _model
        pending = find_pending_sources(project)
        if not pending:
            print(f"No pending sources for {project} — nothing to extract")
            return
        print(f"=== Claim-extracting {len(pending)} pending sources for {project} "
              f"(workers: {args.workers}) ===\n")
        if args.workers <= 1 or args.dry_run:
            results = []
            for f in pending:
                print(f"--- {f.name} ---")
                results.append(ingest_source(f, args.extract_claims, args.model, args.dry_run, args.project or project))
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            results = []
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                futs = {ex.submit(ingest_source, f, args.extract_claims, args.model,
                                  args.dry_run, args.project or project): f
                        for f in pending}
                for fut in as_completed(futs):
                    print(f"--- done: {futs[fut].name} ---", flush=True)
                    results.append(fut.result())
        ingested = sum(1 for r in results if r)
        print(f"\nIngest summary: {ingested} ingested, {len(results) - ingested} skipped")
        return

    if args.changed:
        project = args.changed
        # stage routing: extract sees raw docs — per-repo privacy override
        if not args.model and not os.environ.get("WIKI_LLM_BACKEND"):
            _cfg = get_config()
            _model = get_stage_route(_cfg, project, "extract")
            if is_local_route(_cfg, project, "extract"):
                os.environ["WIKI_LLM_BACKEND"] = "mlx"
                ensure_local_model(_model, config=_cfg)  # before workers spawn
            args.model = _model
        changed = find_changed_sources(project)
        if not changed:
            print(f"No new or changed sources under evidence/raw/{project}/ — nothing to ingest")
            return
        print(f"=== Ingesting {len(changed)} new/changed sources for {project} "
              f"(workers: {args.workers}) ===\n")
        if args.workers <= 1 or args.dry_run:
            results = []
            for f in changed:
                print(f"--- {f.name} ---")
                results.append(ingest_source(f, args.extract_claims, args.model, args.dry_run, args.project or project))
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            results = []
            with ThreadPoolExecutor(max_workers=args.workers) as ex:
                futs = {ex.submit(ingest_source, f, args.extract_claims, args.model,
                                  args.dry_run, args.project or project): f
                        for f in changed}
                for fut in as_completed(futs):
                    print(f"--- done: {futs[fut].name} ---", flush=True)
                    results.append(fut.result())
        ingested = sum(1 for r in results if r)
        print(f"\nIngest summary: {ingested} ingested, {len(results) - ingested} skipped")
        return

    if not args.source:
        parser.error("provide a source path, or use --changed <project-slug>")

    source_path = Path(args.source)
    if not source_path.is_absolute():
        if "evidence/raw" in str(source_path):
            source_path = VAULT_ROOT / source_path
        else:
            source_path = evidence_raw(VAULT_ROOT) / source_path

    # Stage routing (single-source mode): a --project with a local extract
    # route runs the extraction on-device too, matching --pending/--changed.
    if args.project and not args.model and not os.environ.get("WIKI_LLM_BACKEND"):
        _cfg = get_config()
        _model = get_stage_route(_cfg, args.project, "extract")
        if is_local_route(_cfg, args.project, "extract"):
            os.environ["WIKI_LLM_BACKEND"] = "mlx"
            ensure_local_model(_model, config=_cfg)
        args.model = _model

    ok = ingest_source(source_path, args.extract_claims, args.model, args.dry_run, args.project)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()