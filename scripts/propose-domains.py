#!/usr/bin/env python3
# propose-domains.py — Discover and propose new domains from evidence
#
# Usage:
#   python3 scripts/propose-domains.py              # Scan and propose
#   python3 scripts/propose-domains.py --apply      # Apply proposals to ontology
#   python3 scripts/propose-domains.py --dry-run    # Show without writing
#
# Discovers domains by clustering claims/repo-snapshots by tech-stack signals
# (imports, file extensions, tag patterns, source-repo associations). When a
# cluster doesn't fit the existing ontology, proposes a new domain.
#
# The ontology is a LIVING artifact — this script keeps it current.

import sys
import re
import yaml
import json
import argparse
from pathlib import Path
from datetime import date
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from fabric_config import get_config, FABRIC_ROOT, resolve_repo_path, get_all_repo_names, get_domain_signals

VAULT_ROOT = FABRIC_ROOT
ONTOLOGY_PATH = VAULT_ROOT / "schemas" / "ontology.md"
CLAIMS_DIR = VAULT_ROOT / "evidence" / "claims"
SOURCES_DIR = VAULT_ROOT / "evidence" / "sources"
PROJECTS_DIR = VAULT_ROOT / "projects"

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


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, ""
    try:
        return (yaml.safe_load(m.group(1)) or {}), m.group(2)
    except Exception:
        return {}, ""


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
    """Parse existing domains from ontology.md."""
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


def main():
    parser = argparse.ArgumentParser(description="Discover and propose new domains")
    parser.add_argument("--apply", action="store_true", help="Apply proposals to ontology")
    parser.add_argument("--dry-run", action="store_true", help="Show proposals without writing")
    parser.add_argument("--min-score", type=int, default=3, help="Minimum signal score to propose a domain")
    args = parser.parse_args()

    config = get_config()
    owner = config.get("owner", "you")

    # Load existing domains
    existing = load_ontology_domains()
    print(f"Existing ontology domains: {sorted(existing)}")
    print()

    # Compute scores
    scores = compute_domain_scores(config)

    # Separate known vs new
    new_domains = {d: s for d, s in scores.items() if d not in existing and s >= args.min_score}
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

    if args.dry_run:
        print("\n[DRY RUN] No changes written")
        return

    if not proposals:
        return

    # Apply proposals to ontology
    today = date.today().isoformat()
    text = ONTOLOGY_PATH.read_text()

    # Find the "## Domains" section and append new domains
    lines = text.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if line.startswith("## Shared tag set"):
            insert_idx = i
            break

    if insert_idx is None:
        print("Warning: could not find insertion point in ontology.md", file=sys.stderr)
        return

    new_lines = []
    for p in proposals:
        desc = p["domain"].replace("-", " ")
        new_lines.append(f"- **{p['domain']}** — {desc} (auto-proposed {today}, signal score: {p['score']}).")
        new_lines.append(f"   - Status: proposed — review and add examples before confirming.")

    lines[insert_idx:insert_idx] = new_lines + [""]

    ONTOLOGY_PATH.write_text("\n".join(lines))
    print(f"\nAdded {len(proposals)} proposed domains to {ONTOLOGY_PATH.name}")
    print("Review with: cat schemas/ontology.md")


if __name__ == "__main__":
    main()