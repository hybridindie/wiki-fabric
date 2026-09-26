#!/usr/bin/env python3
# propose-domains.py — Discover and propose new domains from evidence
#
# Usage:
#   python3 scripts/cmd/propose-domains.py              # Scan and dump to stdout
#   python3 scripts/cmd/propose-domains.py --apply      # Write proposal dossiers (pending-review)
#   python3 scripts/cmd/propose-domains.py --dry-run    # Show without writing
#
# The ontology is per-fabric and human-gated: this script only PROPOSES, writing
# a pending-review dossier per candidate domain under registry/domain-proposals/.
# The ontology itself is merged only after human review via
# `python3 scripts/cmd/promote-domains.py --apply <dossier>`. Never auto-apply.
#
# The ontology is per-fabric and human-gated: this script only PROPOSES. It
# writes a pending-review dossier per candidate domain under
# registry/domain-proposals/; the ontology itself is merged only after human
# review via `python3 scripts/cmd/promote-domains.py --apply <dossier>`.
#
# Discovers domains by clustering claims/repo-snapshots by tech-stack signals
# (imports, file extensions, tag patterns, source-repo associations). When a
# cluster doesn't fit the existing ontology, proposes a new domain.
#
# The ontology is a LIVING artifact — this script keeps it current.

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import yaml
import json
import argparse
from pathlib import Path
from datetime import date
from collections import Counter, defaultdict

from fabric_config import get_config, CORPUS_ROOT, resolve_repo_path, get_all_repo_names, get_domain_signals
from wf_common import parse_frontmatter

CORPUS = CORPUS_ROOT
# The domain ontology is a per-fabric, synced artifact (content path), not harness.
ONTOLOGY_PATH = CORPUS / "domains" / "ontology.md"
ONTOLOGY_DIR = CORPUS / "domains"
CLAIMS_DIR = CORPUS / "evidence" / "claims"
SOURCES_DIR = CORPUS / "evidence" / "sources"
PROJECTS_DIR = CORPUS / "projects"
PROPOSALS_DIR = CORPUS / "registry" / "domain-proposals"

# Domain signal lookup — built from fabric.yaml domains.signals
# A dependency/tag matching a signal → that domain gets a score


def build_signal_lookup(config):
    """Build {signal: domain} from fabric.yaml domain signals."""
    lookup = {}
    for domain, signals in get_domain_signals(config).items():
        for signal in signals:
            lookup[signal.lower().replace("-", "_")] = domain
    return lookup


def match_signal(dep_or_tag, signal_lookup):
    """Match a dependency/tag to a domain via signal lookup + fuzzy match."""
    dep = dep_or_tag.lower().replace("-", "_")
    # Exact match
    if dep in signal_lookup:
        return signal_lookup[dep]
    # Partial match (dep contains signal or signal contains dep)
    for signal, domain in signal_lookup.items():
        if len(signal) > 3 and (signal in dep or dep in signal):
            return domain
    return None

STOPWORDS = {"the", "a", "an", "is", "of", "to", "in", "and", "or", "for", "on",
             "with", "at", "by", "from", "that", "this", "it", "as", "be", "are",
             "was", "were", "repo", "snapshot", "capture", "test", "doc", "log"}


def scan_repo_tech_stack(repo_path, signal_lookup):
    """Scan a repo's dependency files for tech-stack signals."""
    signals = Counter()

    # Python: pyproject.toml, requirements*.txt
    for f in repo_path.rglob("pyproject.toml"):
        try:
            text = f.read_text()
            for m in re.finditer(r'"([\w-]+)[><=~]', text):
                dep = m.group(1).lower()
                domain = match_signal(dep, signal_lookup)
                if domain:
                    signals[domain] += 1
        except Exception:
            pass

    # JS: package.json
    for f in repo_path.rglob("package.json"):
        if "node_modules" in str(f):
            continue
        try:
            data = json.loads(f.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for dep in deps:
                domain = match_signal(dep, signal_lookup)
                if domain:
                    signals[domain] += 1
        except Exception:
            pass

    # Docker / k8s
    for pattern in ["docker-compose*.yml", "Dockerfile*", "k8s/**/*.yaml"]:
        for f in repo_path.glob(pattern):
            signals["devops"] += 1

    # GDScript (godot signal)
    for ext in [".gd"]:
        count = sum(1 for f in repo_path.rglob(f"*{ext}") if ".godot" not in str(f))
        if count > 0:
            signals["godot-systems"] += min(count, 5)

    return signals


def scan_claim_tags(signal_lookup):
    """Scan claim tags for domain signals."""
    signals = Counter()
    for f in CLAIMS_DIR.glob("claim-*.md"):
        fm, _ = parse_frontmatter(f)
        for tag in (fm.get("tags", []) or []):
            domain = match_signal(tag, signal_lookup)
            if domain:
                signals[domain] += 1
    return signals


def scan_source_tags(signal_lookup):
    """Scan source records for domain signals."""
    signals = Counter()
    for f in SOURCES_DIR.glob("src-*.md"):
        fm, _ = parse_frontmatter(f)
        for tag in (fm.get("tags", []) or []):
            domain = match_signal(tag, signal_lookup)
            if domain:
                signals[domain] += 1
    return signals


def load_ontology_domains():
    """Parse existing domains from ontology.md. Tolerant of a not-yet-seeded
    ontology: a missing file means no domains are declared yet."""
    if not ONTOLOGY_PATH.exists():
        return set()
    text = ONTOLOGY_PATH.read_text()
    domains = set()
    for m in re.finditer(r'-\s+\*\*(\w[\w-]*)\*\*', text):
        domains.add(m.group(1))
    return domains


def compute_domain_scores(config):
    """Aggregate all signals and score domain candidates."""
    signal_lookup = build_signal_lookup(config)
    total = Counter()

    # Scan each connected repo's tech stack
    for repo_name in get_all_repo_names(config):
        repo_path = resolve_repo_path(config, repo_name)
        if repo_path and repo_path.exists():
            signals = scan_repo_tech_stack(repo_path, signal_lookup)
            for domain, score in signals.items():
                total[domain] += score

    # Add claim and source tag signals
    total.update(scan_claim_tags(signal_lookup))
    total.update(scan_source_tags(signal_lookup))

    return total


def write_proposal_dossier(domain, score):
    """Write one domain-approval dossier into registry/domain-proposals/
    (pending-review). NEVER mutates ontology.md — a human must approve."""
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    slug = domain
    today = date.today().isoformat()
    path = PROPOSALS_DIR / f"domain-{slug}.md"
    # Idempotent: don't overwrite an existing pending proposal.
    if path.exists():
        return path, False
    dossier = f"""---
type: change-set
title: "Propose domain: {domain}"
description: "Domain proposed from evidence signals (score {score}). Human review before merge."
status: proposed
scope: domains
domain: {domain}
id: domain-proposal-{slug}
created: {today}
---
# Propose domain: {domain}

- **Domain**: `{domain}`
- **Signal score**: {score}
- **Evidence**: auto-proposed from claim/source tech-stack signals.
- **Decision requested**: approve to add `{domain}` to `domains/ontology.md`, or reject.

Review: `python3 scripts/cmd/promote-domains.py --apply <domain-proposal-{slug}>`
"""
    path.write_text(dossier, encoding="utf-8")
    return path, True


def structural_domains(repo_path):
    """Vocabulary-free domain detection from structural evidence only.

    No seeded signal lexicon: file-type profiles and top-level directory
    names map to GENERIC structural families. Used when the ontology has
    no domains yet (cold-start fabric) so the vocabulary builds from the
    first project's own shape rather than hardcoded defaults."""
    exts = Counter(f.suffix for f in repo_path.rglob("*")
                   if f.is_file() and "node_modules" not in str(f)
                   and ".venv" not in str(f) and not f.name.startswith("."))
    dirs = {d.name for d in repo_path.iterdir()
            if d.is_dir() and not d.name.startswith(".")}
    signals = Counter()
    if exts.get(".gd", 0) >= 3:
        signals["godot"] += min(exts[".gd"], 5)
    if (exts.get(".sql", 0) >= 3 or "migrations" in dirs
            or any(d in dirs for d in ("k8s", "docker"))):
        signals["devops"] += 3
    if exts.get(".tsx", 0) + exts.get(".jsx", 0) >= 3 or "frontend" in dirs:
        signals["web-ui"] += 3
    if any(d in dirs for d in ("tests", "spec", "e2e")):
        signals["testing"] += 2
    if "migrations" in dirs:
        signals["data-layer"] += 2
    return signals


def main():
    parser = argparse.ArgumentParser(description="Discover and propose new domains")
    parser.add_argument("--apply", action="store_true",
                        help="Write proposal dossiers (human review still required to merge)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show proposals without writing anything")
    parser.add_argument("--min-score", type=int, default=3,
                        help="Minimum signal score to propose a domain")
    args = parser.parse_args()

    config = get_config()

    # Load existing domains
    existing = load_ontology_domains()
    print(f"Existing ontology domains: {sorted(existing)}")
    print()

    if not existing:
        # Cold-start: no ontology vocabulary yet. Build the first proposals
        # from STRUCTURAL evidence (file-type profiles, directory shapes) —
        # no seeded lexicon. The vocabulary derives from the projects
        # themselves rather than hardcoded bootstrap defaults.
        print("Cold-start: no ontology domains yet — using structural scan.")
        scores = Counter()
        for repo_name in get_all_repo_names(config):
            repo_path = resolve_repo_path(config, repo_name)
            if not repo_path or not repo_path.exists():
                continue
            repo_signals = structural_domains(repo_path)
            for d, s in repo_signals.items():
                scores[d] += s
            if repo_signals:
                print(f"  {repo_name}: {dict(repo_signals)}")
    else:
        # Compute scores
        scores = compute_domain_scores(config)

    # Separate known vs new
    new_domains = {d: s for d, s in scores.items()
                   if d not in existing and s >= args.min_score}
    known_domains = {d: s for d, s in scores.items() if d in existing}

    print("Known domains (signal strength):")
    for d, s in sorted(known_domains.items(), key=lambda x: -x[1]):
        print(f"  {d}: {s}")

    print()
    print(f"New domain candidates (score >= {args.min_score}):")
    proposals = []
    for d, s in sorted(new_domains.items(), key=lambda x: -x[1]):
        print(f"  {d}: {s}")
        proposals.append({"domain": d, "score": s, "status": "proposed"})

    if not proposals:
        print("  (none — ontology is current)")

    if args.dry_run or not proposals:
        print("\n[DRY RUN] No changes written (run without --dry-run to write proposal dossiers)")
        return

    # Write pending-review proposal dossiers — the ontology itself is untouched
    # until a human runs promote-domains.py --apply <dossier>.
    written = 0
    for p in proposals:
        path, is_new = write_proposal_dossier(p["domain"], p["score"])
        if is_new:
            written += 1
            print(f"  ✎ proposal dossier: {path.relative_to(CORPUS)}")
    print(f"\nWrote {written} proposal dossier(s) to registry/domain-proposals/")
    print("The ontology is unchanged. To merge after human review:")
    print(f"  python3 scripts/cmd/promote-domains.py --apply <dossier>")


if __name__ == "__main__":
    main()