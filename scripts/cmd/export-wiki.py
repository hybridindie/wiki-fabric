#!/usr/bin/env python3
# export-wiki.py — Generate the human-layer wiki from the evidence corpus.
#
# Produces narrative articles (OpenWiki style) into the vault:
#   wiki/topics/<topic>.md      — mechanism-first, cross-project
#   wiki/projects/<project>.md  — narrative per-repo summary
#   wiki/domains/               — domain hubs (table of contents)
#   wiki/index.md               — staleness dashboard + recent changes
#
# Articles are ASSEMBLED VIEWS over claims — never copied content.
# Claims are cited as numbered footnotes. Generation mode configurable
# per project (mechanical | llm | hybrid) in fabric.yaml wiki.generation.
#
# Staleness: 3-tier citation surfacing (current / ⚠ due / archived).
#
# Usage:
#   python3 scripts/cmd/export-wiki.py [--project <slug>] [--dry-run]
#        [--mode mechanical|llm|hybrid]

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import os
import json
from pathlib import Path
from datetime import date, datetime, timedelta

from fabric_config import FABRIC_ROOT, CORPUS_ROOT, get_config, get_all_repo_names, get_repo_config, get_vault_path, actor
from wf_common import now_iso_utc

TODAY = date.today()

# Provenance stamp for every generated wiki page (OKF §5 / LangChain-OpenWiki style).
# The agent actor is the compiler model that wrote the prose; mechanical pages are
# stamped as a process. `by` carries the full actor; `at` is an ISO-8601 instant.
def _producer_actor(config, mode):
    """Actor stamp for a generated wiki page. LLM/hybrid prose is authored by the
    compiler model; mechanical pages are deterministic (a process, no model)."""
    if mode in ("llm", "hybrid"):
        return actor(config, "agent",
                     model=(config.get("llm", {}).get("compiler_model")
                            or config.get("llm", {}).get("model") or "unknown"))
    return actor(config, "process", model="export-wiki")


# --- Human-side enrichment: consistent anatomy, provenance, diagram repair ---
# Every generated wiki page gets the same skeleton (LangChain-OpenWiki style):
#   YAML frontmatter + provenance stamps
#   SUMMARY: <one line>            (lead, matches first prose line)
#   ... prose ...
#   ## Key Takeaways               (the durable facts the page asserts)
#   ## Sources                     (claim -> source -> locator backtrace)
# And any mermaid fence that fails a lightweight syntactic check is degraded to a
# `text` fence with a repair comment (repaired on the next run) — so a broken
# diagram never ships.

MERMAID_REPAIR_COMMENT = "OPENWIKI-REPAIR"


def _provenance_block(producer, generated_at):
    return f"generated: {{ by: \"{producer}\", at: \"{generated_at}\" }}"


def _claim_provenance(claim_path):
    """Return {source, locator} for a claim's first source_ref, or {}."""
    s = claim_path.read_text(encoding="utf-8", errors="replace")
    src = re.search(r'source: "\[\[(src-[^\]]+)\]\]"', s)
    loc = re.search(r'locator: "?([^\n"]+)', s)
    return {
        "source": src.group(1) if src else None,
        "locator": loc.group(1) if loc else None,
    }


def _extract_mermaid_fences(text):
    """Find ```fence blocks. Returns list of {'start': line_no(0-based) of the
    opening fence, 'lang': str, 'body': str}. Markdown fences close with a bare
    ``` line regardless of the opening language."""
    fences = []
    block_lang = None
    block_lines = []
    start_line = None
    for i, ln in enumerate(text.splitlines()):
        is_open = re.match(r"^```([A-Za-z0-9_#+-]*)\s*$", ln.strip())
        if block_lang is None:
            if is_open:
                block_lang = is_open.group(1) or ""
                start_line = i
                block_lines = []
            continue
        # inside a fence: a bare ``` (any trailing content on the line ignored
        # per CommonMark) closes it
        if re.match(r"^```", ln.strip()):
            fences.append({"start": start_line, "lang": block_lang,
                           "body": "\n".join(block_lines)})
            block_lang = None
        else:
            block_lines.append(ln)
    return fences


def _mermaid_valid(body):
    """Lightweight, dependency-free syntactic sanity check on a mermaid body.
    A fully rigorous check needs the mermaid parser (installed in CI); this
    catches gross breakages (unbalanced code/arrow/flow terminators) so a broken
    fence degrades to text instead of shipping a broken block."""
    # balanced braces/parens
    for op, cl in (("{", "}"), ("(", ")"), ("[", "]")):
        if body.count(op) != body.count(cl):
            return False
    # a flowchart/state/sequence body should contain at least one directional edge
    if re.search(r"\b(graph|flowchart|sequenceDiagram|stateDiagram|erDiagram|pie)\b", body) \
            and not re.search(r"->>|--[>|]|--->|[=>]-|>>|\.\.|-\.", body):
        return False
    return True


def _validate_and_repair_diagrams(article):
    """Repair broken mermaid fences in an article body. Returns the repaired text
    and a count of repairs."""
    fences = _extract_mermaid_fences(article)
    if not fences:
        return article, 0
    repaired = 0
    lines = article.splitlines()
    for f in reversed(fences):  # edit from the bottom so line indices stay valid
        if f["lang"] != "mermaid" or _mermaid_valid(f["body"]):
            continue
        # Degrade the fence language to text; the closing fence needs no change
        # (``` closes a ```text fence identically).
        lines[f["start"]] = "```text"
        # add repair comment just inside the open fence, on the body's first line
        # insert comment line after the opening fence
        lines.insert(f["start"] + 1,
                     f"<!-- {MERMAID_REPAIR_COMMENT}: invalid mermaid degraded to text; "
                     f"a --update will regenerate -->")
        repaired += 1
    return "\n".join(lines), repaired


def _enrich_page(path, config, mode, related_links=None):
    """Post-process a generated wiki page: stamp provenance, enforce a SUMMARY
    lead, append Key Takeaways + Sources backtrace, a Related cross-links
    section, and validate/repair diagrams.

    Runs uniformly after whichever generator (LLM or mechanical) produced the raw
    body, so every page converges on the same OpenWiki-style anatomy."""
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return 0
    fm_block, body = m.group(1), m.group(2)
    stamp = _provenance_block(_producer_actor(config, mode), now_iso_utc())
    # idempotent stamp: always refresh the `generated:` line
    if re.search(r"generated: \{", fm_block):
        fm_block = re.sub(r"generated: \{[^\n]*\}", stamp, fm_block, count=1)
    else:
        fm_block = fm_block.rstrip() + "\n" + stamp

    # Aliases: human-readable name variants so [[slug]] resolution + Obsidian
    # graph tolerate alternate titles. Derived from the page title.
    title = re.search(r"^title:\s*\"?([^\"]+)", fm_block, re.MULTILINE)
    if title:
        variants = {title.group(1).strip()}
        # lowercase + kebab for graph matching
        variants.add(re.sub(r"[^a-z0-9-]+", "-", title.group(1).lower()).strip("-"))
        aliases_block = "aliases:\n" + "".join(f'  - "{a}"\n' for a in sorted(variants) if a)
        if re.search(r"^aliases:", fm_block, re.MULTILINE):
            fm_block = re.sub(r"aliases:.*(?=\n[^- ])", aliases_block, fm_block, count=1, flags=re.DOTALL)
        else:
            fm_block = fm_block.rstrip() + "\n" + aliases_block.rstrip()

    # SUMMARY lead from the first prose line (skip headings/bullets; dedup an
    # existing SUMMARY). This is the one-line "what is this" for index/search.
    body = re.sub(r"^SUMMARY: .*\n", "", body.lstrip("\n"))
    first_line = ""
    for ln in body.splitlines():
        ln = ln.strip()
        if ln and not ln.startswith(("#", "-", "|", "```", ">")) and ":" not in ln[:1]:
            first_line = ln
            break
    summary_line = f"SUMMARY: {first_line}\n\n" if first_line else ""

    # Key Takeaways + Sources derived deterministically from the page's own cited
    # claims — truthful, never hallucinated (LangChain OpenWiki "grounded" ethos).
    # Claims are referenced either as [[claim-...]] wikilinks or as footnote
    # citation lines `[N] claim-... — statement`.
    cite_ids = dict.fromkeys(
        re.findall(r"\[\[(claim-[^\]]+)\]\]", body)
        + re.findall(r"^\[\d+\]\s+(claim-[a-z0-9-]+)", body, re.MULTILINE))
    takeaways, sources = [], {}
    for cs in cite_ids:
        cp = CORPUS_ROOT / "evidence" / "claims" / f"{cs}.md"
        if not cp.exists():
            continue
        s = cp.read_text(encoding="utf-8", errors="replace")
        st = re.search(r"statement: \"?([^\n]+)", s)
        if st:
            takeaways.append(f"- {st.group(1).strip()[:160]} [[{cs}]]")
        prov = _claim_provenance(cp)
        if prov.get("source") and prov["source"] not in sources:
            sources[prov["source"]] = prov.get("locator") or ""

    sections = [summary_line, body]
    if related_links and not re.search(r"^## Related", body, re.MULTILINE):
        sections.append("\n## Related\n")
        for r in related_links:
            kind = {"source": "shares sources with", "claim": "related to"}.get(r["kind"], r["kind"])
            w = f" ({r['weight']} shared)" if r.get("weight", 0) > 1 else ""
            sections.append(f"- [[{r['target']}]] — {kind}{w}")
        sections.append("")
    if takeaways:
        sections.append("\n## Key Takeaways\n")
        sections.append("\n".join(takeaways) + "\n")
    if sources:
        src_lines = ["- [[%s]]%s" % (s, f" `{l}`" if l else "")
                     for s, l in sources.items()]
        sections.append("\n## Sources\n")
        sections.append("\n".join(src_lines) + "\n")

    article = "\n".join(sections)
    article, _ = _validate_and_repair_diagrams(article)
    out = f"---\n{fm_block}\n---\n\n{article}\n"
    path.write_text(out, encoding="utf-8")
    return 1


def _wiki_root():
    """The wiki output dir — inside the configured vault when set, else
    in-repo (CORPUS_ROOT/wiki/). The vault is a real output dir (no symlinks)."""
    v = get_vault_path()
    return (v / "wiki") if v else (CORPUS_ROOT / "wiki")


def _compute_wiki_edges(topics, projects, min_shared=2):
    """Compute the wiki's cross-page network from grounded latent edges.

    `topics` and `projects` are the dicts produced by select_topics() /
    gathered project configs; both expose `.slug` and `claims`. Returns
    (page_edges, node_index):
      page_edges: {slug: [{"target", "kind", "weight"}, ...]} — the wikilinks a
        page should carry (topic->topic via shared source, topic<->project via
        shared claim). `kind` is "source" or "claim"; weight is shared count.
      node_index: {slug: {"type": "topic"|"project", "title"}}
    These edges are REAL relations derivable from evidence, never invented.
    """
    # Normalize projects: may be passed as slugs (from main) or dicts.
    def _proj_claims(p):
        if isinstance(p, str):
            return [c.stem for c in (CORPUS_ROOT / "evidence" / "claims").glob(f"claim-{p}-*.md")]
        return [c.get("id") if isinstance(c, dict) else c for c in p.get("claims", [])]

    def _proj_slug(p):
        return p if isinstance(p, str) else p["slug"]

    # claim -> topic slugs
    claim_topics = {}
    for t in topics:
        for c in t["claims"]:
            cid = c.get("id") if isinstance(c, dict) else c
            claim_topics.setdefault(cid, set()).add(t["slug"])
    # claim -> project slugs
    claim_projects = {}
    for p in projects:
        pslug = _proj_slug(p)
        for cid in _proj_claims(p):
            if cid:
                claim_projects.setdefault(cid, set()).add(pslug)
    # claim -> source
    claim_source = {}
    for cp in (CORPUS_ROOT / "evidence" / "claims").glob("claim-*.md"):
        m = re.search(r'resource: "\[\[(src-[^\]]+)\]\]"',
                      cp.read_text(encoding="utf-8", errors="replace"))
        if m:
            claim_source[cp.stem] = m.group(1)

    # topic -> set of sources it cites (for topic-topic via shared source)
    topic_sources = {}
    for cid, src in claim_source.items():
        for t in claim_topics.get(cid, ()):
            topic_sources.setdefault(t, set()).add(src)

    page_edges = {t["slug"]: [] for t in topics}
    page_edges.update({_proj_slug(p): [] for p in projects})
    node_index = {t["slug"]: {"type": "topic", "title": t["title"]} for t in topics}
    node_index.update({_proj_slug(p): {"type": "project", "title": _proj_slug(p)} for p in projects})

    # topic <-> topic via shared source (>= min_shared)
    topic_slugs = [t["slug"] for t in topics]
    for i in range(len(topic_slugs)):
        for j in range(i + 1, len(topic_slugs)):
            a, b = topic_slugs[i], topic_slugs[j]
            shared = len(topic_sources.get(a, set()) & topic_sources.get(b, set()))
            if shared >= min_shared:
                page_edges[a].append({"target": b, "kind": "source", "weight": shared})
                page_edges[b].append({"target": a, "kind": "source", "weight": shared})

    # topic <-> project via shared claim
    for cid in set(claim_topics) & set(claim_projects):
        for t in claim_topics[cid]:
            for p in claim_projects[cid]:
                page_edges[t].append({"target": p, "kind": "claim", "weight": 1})
                page_edges[p].append({"target": t, "kind": "claim", "weight": 1})

    # dedupe + sort by weight desc
    for slug, edges in page_edges.items():
        by_key = {}
        for e in edges:
            key = e["target"]
            prev = by_key.get(key)
            if prev is None:
                by_key[key] = dict(e)
            else:
                by_key[key]["weight"] += e["weight"]
        page_edges[slug] = sorted(by_key.values(), key=lambda e: -e["weight"])
    return page_edges, node_index

# === staleness classification ===
def _staleness(review_after, stale_after):
    """Returns (tier, label, days) where tier is 1=current, 2=due, 3=stale."""
    def _parse(s):
        try:
            from datetime import datetime as dt
            return dt.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
        except Exception:
            return None
    ra = _parse(review_after) if review_after else None
    sa = _parse(stale_after) if stale_after else None
    due = ra or sa
    if not due:
        return 1, None, 0
    overdue = (TODAY - due).days
    if overdue > 90 or (sa and sa <= TODAY):
        return 3, f"stale since {due}", overdue
    if overdue > 0:
        return 2, f"review overdue {overdue}d", overdue
    return 1, None, 0

def _cite_claim(claim_path, idx):
    """Format a footnote citation for a claim. Returns (inline_ref, footnote)."""
    s = claim_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^title: (.+)$|^statement: \"?([^\n]{10,})", s, re.MULTILINE)
    title = (m.group(1) or m.group(2) or "")[:80].strip() if m else claim_path.stem
    ra = re.search(r"review_after: (\S+)", s)
    sa = re.search(r"stale_after: (\S+)", s)
    tier, _, overdue = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
    if tier == 2:
        return f"⚠️[{idx}]", f"[{idx}] {claim_path.stem.replace('claim-','').replace('-',' ')} — {title} ⚠️ review overdue {overdue}d"
    return f"[{idx}]", f"[{idx}] {claim_path.stem} — {title}"

# === topic selection: concepts with >= N claims become topic articles ===
def select_topics(min_claims=6):
    """Group claims by concept → topics with enough evidence become articles."""
    topics = []
    for c in sorted((CORPUS_ROOT / "concepts").glob("concept-*.md")):
        s = c.read_text(encoding="utf-8", errors="replace")
        title = re.search(r"^title: (.+)$", s, re.MULTILINE)
        dom = re.search(r"^domain: \[(.*?)\]", s, re.MULTILINE)
        claims = re.findall(r'\[\[(claim-[^\]]+)\]\]', s)
        if len(claims) >= min_claims:
            topics.append({
                "file": c, "title": title.group(1).strip() if title else c.stem,
                "domain": dom.group(1) if dom else "agent-systems",
                "claims": claims, "body": s.split("---", 2)[2] if s.startswith("---") else s,
            })
    for t in topics:
        t["slug"] = re.sub(r"[^a-z0-9-]+", "-", t["title"].lower()).strip("-")
    return topics


def _project_slug_from_claim(claim_stem):
    m = re.match(r"claim-([a-z0-9-]+?)-", claim_stem)
    return m.group(1) if m else "unknown"


WIKI_ARTICLE_PROMPT = """You are writing a concept page for a knowledge-fabric wiki (LangChain-OpenWiki style). The page covers: {title}

You have the following evidence — claims with locators. Every claim carries a numbered reference [N] that you MUST cite inline wherever you use it. Draw ONLY from this evidence; never invent facts, examples, or architecture not entailed by a claim.

{evidence}

Write a 300-650 word article with this exact anatomy:

## Definition
One paragraph: what this topic is, and why it matters. Cite [N].

## How it works
2-4 ## subheadings grouping the evidence into logical sections (the mechanism, the constraints, the tradeoffs present in the claims). Every concrete statement cites its claim [N].

## Diagram
If the topic has a clear flow, architecture, lifecycle, or state relationship supported by the claims, include a mermaid diagram that is GROUNDED in the evidence — every node/edge must reflect a stated claim. Choose the type by the topic's nature:
- Use `sequenceDiagram` for protocol/handshake/request-response topics (server-driven command, connection lifecycle, client-server exchange).
- Use `stateDiagram-v2` for lifecycle/state-machine topics (pending→running→done, status transitions).
- Otherwise use `flowchart TD` for architecture/flow/decision structure.
If there is no such flow, write the mermaid fence anyway with a minimal `flowchart TD` connecting the distinct ideas present in the evidence. Use only `flowchart TD`, `sequenceDiagram`, or `stateDiagram-v2` syntax.

## Related
End by listing 3-5 `- [[slug]]` links to related concepts. Use ONLY slugs that appear in the evidence's source/project prefixes; never invent slugs.

Rules:
- Cite claims inline as numbered footnotes [N] matching the evidence list.
- Every factual statement must trace to a provided claim — never invent evidence.
- Plain engineering language, no marketing tone.
- If a claim is low-confidence or contested, mark it (e.g. "(low confidence)").

Return ONLY the markdown article body (no YAML frontmatter).
"""

def _llm_topic_article(topic, claims, dry_run=False):
    """Generate a narrative wiki article using the compiler model."""
    from extract_backends import parse_json_array, llm_config
    import openai, os
    cfg = llm_config(compiler=True)
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                           timeout=float(os.environ.get("WIKI_LLM_TIMEOUT", "600")))

    evidence_parts = []
    for i, cp in enumerate(claims, 1):
        s = cp.read_text(encoding="utf-8", errors="replace")
        statement = re.search(r"statement: \"?([^\n]+)", s)
        locator = re.search(r'locator: "?([^\n]+?)"?\s*$', s, re.MULTILINE)
        project = re.search(r"claim-([a-z0-9-]+?)-", cp.stem)
        evidence_parts.append(
            f"[{i}] {statement.group(1) if statement else cp.stem} "
            f"(from {project.group(1) if project else '?'}"
            f"{', ' + locator.group(1) if locator else ''})")
    evidence_text = "\n".join(evidence_parts)

    prompt = WIKI_ARTICLE_PROMPT.format(title=topic["title"], evidence=evidence_text)
    resp = client.chat.completions.create(
        model=cfg["model"], temperature=0.1, max_tokens=4096,
        messages=[{"role": "system", "content": "You write wiki articles. Return ONLY valid markdown."},
                  {"role": "user", "content": prompt}])
    return resp.choices[0].message.content or ""


PROJECT_ARTICLE_PROMPT = """You are writing a project retrospective article for a knowledge fabric.
The project is: {project}

You have the following evidence:

{evidence}

Promoted patterns (load-bearing rules this project or its evidence contributed to):
{patterns}

Insight takeaways from the project's chat sessions:
{insights}

Related wiki articles (topics this project contributed to):
{topic_refs}

Write a 500-900 word project retrospective that:
1. Opens with what the project is, its role, and why it matters
2. ## What was built — the mechanisms, the architecture, the tools
3. ## Constraints discovered — the hard limits, API gaps, platform behaviors
4. ## Patterns that emerged — how problems were solved, what worked
5. ## Decisions made — the choices and their rationale
6. ## Current state — claims count, graph status, what's still open
7. Reference related topic articles by wikilink: [[<topic-slug>]] for mechanics
8. Reference promoted patterns by wikilink: [[<pattern-slug>]] for load-bearing rules
9. Every factual statement must trace to the evidence — never invent
10. Excludes transient details (CI states, PR counts, review queue states)
11. Uses plain engineering language

Return ONLY the markdown article body (no YAML frontmatter).
"""

def _llm_project_article(project, claims, topic_links, insight_takeaways, patterns, dry_run=False):
    """Generate a project retrospective using the compiler model."""
    from extract_backends import llm_config
    import openai, os
    cfg = llm_config(compiler=True)
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                           timeout=float(os.environ.get("WIKI_LLM_TIMEOUT", "600")))

    # evidence: durable claims (not transient)
    evidence_parts = []
    for i, cp in enumerate(claims, 1):
        s = cp.read_text(encoding="utf-8", errors="replace")
        statement = re.search(r"statement: \"?([^\n]+)", s)
        evidence_parts.append(f"[{i}] {statement.group(1) if statement else cp.stem}")
    evidence_text = "\n".join(evidence_parts[:30])  # cap at 30 for context

    topic_refs = "\n".join(f"- [[{slug}]] {title}" for slug, title in topic_links)
    insights_text = "\n".join(f"- {it[:120]}" for it in insight_takeaways) if insight_takeaways else "_(none)_"
    prompt = PROJECT_ARTICLE_PROMPT.format(
        project=project, evidence=evidence_text, topic_refs=topic_refs,
        patterns="\n".join(f"- [[{ps}] {pt}" for ps, pt in patterns) if patterns else "_(none yet)_",
        insights=insights_text)
    resp = client.chat.completions.create(
        model=cfg["model"], temperature=0.1, max_tokens=4096,
        messages=[{"role": "system", "content": "You write project retrospectives. Return ONLY valid markdown."},
                  {"role": "user", "content": prompt}])
    return resp.choices[0].message.content or ""


def _generate_topic_article(topic, mode="mechanical", dry_run=False):
    """Generate one topic article from a concept + its claims."""
    title = topic["title"]
    slug = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-")
    claims = []
    for cs in topic["claims"]:
        cp = CORPUS_ROOT / "evidence" / "claims" / f"{cs}.md"
        if cp.exists():
            claims.append(cp)
    if not claims:
        return None, 0
    # staleness tiers
    current, flagged, stale = [], [], []
    for cp in claims:
        s = cp.read_text(encoding="utf-8", errors="replace")
        ra = re.search(r"review_after: (\S+)", s)
        sa = re.search(r"stale_after: (\S+)", s)
        tier, _, _ = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
        statement = re.search(r'statement: "?([^\n]+)', s)
        st = statement.group(1) if statement else ""
        if tier == 3:
            stale.append((cp, st))
        elif tier == 2:
            flagged.append((cp, st))
        else:
            current.append((cp, st))

    # LLM mode: generate narrative prose with the compiler model
    if mode in ("llm", "hybrid") and (mode == "llm" or len(current) >= 5):
        try:
            body = _llm_topic_article(topic, claims, dry_run=dry_run)
            if body:
                lines = [
                    "---",
                    f"type: wiki-article",
                    f"title: \"{title}\"",
                    f"domain: [{topic['domain']}]",
                    f"review_after: {(TODAY + timedelta(days=120)).isoformat()}",
                    f"---",
                    f"",
                    body,
                    f"",
                    f"---",
                    f"",
                    f"_Citations link to claims in evidence/claims/. Generated on {TODAY.isoformat()}._",
                ]
                article = "\n".join(lines) + "\n"
                out_dir = _wiki_root() / "topics"
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{slug}.md"
                if not dry_run:
                    out_path.write_text(article, encoding="utf-8")
                return out_path, len(claims)
        except Exception as e:
            print(f"  LLM generation failed for {title}: {e} — falling back to mechanical", file=sys.stderr)

    lines = [
        "---",
        f"type: wiki-article",
        f"title: \"{title}\"",
        f"domain: [{topic['domain']}]",
        f"review_after: {(TODAY + timedelta(days=120)).isoformat()}",
        f"---",
        f"",
        f"# {title}",
        f"",
        f"## Definition",
        f"",
    ]
    # Deterministic, grounded definition: the topic's key claim statements,
    # joined into a plain-language summary (0 tokens, never hallucinated).
    key = (current[:8] if current else flagged[:8])
    if key:
        defn = " ".join(s.rstrip('"')[:130] + "." for _, s in key)
        lines.append(f"{title} covers: {defn}")
    else:
        lines.append(f"{title} is a topic recorded in the evidence fabric.")
    lines.append("")
    footnotes = []
    idx = 1
    if current:
        seen_statements = set()
        lines.append(f"{len(current)} current claim(s) support this topic.")
        lines.append("")
        for cp, st in current:
            st_short = st[:80]
            if st_short in seen_statements:
                continue
            seen_statements.add(st_short)
            ref, note = _cite_claim(cp, idx)
            lines.append(f"- {st[:140]} {ref}")
            footnotes.append(note)
            idx += 1
    if flagged:
        lines.append("")
        lines.append(f"## ⚠️ Due for review ({len(flagged)})")
        for cp, st in flagged[:10]:
            ref, note = _cite_claim(cp, idx)
            lines.append(f"- {st[:140]} ⚠️{ref}")
            footnotes.append(note)
            idx += 1
    if stale:
        lines.append("")
        lines.append(f"## Archived (stale)")
        lines.append("<details><summary>These claims informed the topic but may no longer be accurate.</summary>")
        lines.append("")
        for cp, st in stale[:10]:
            ref, note = _cite_claim(cp, idx)
            lines.append(f"- {st[:140]} [{idx}]")
            footnotes.append(note)
            idx += 1
        lines.append("</details>")

    lines.append("")
    lines.append("---")
    lines.append("")
    for fn in footnotes:
        lines.append(fn)
    lines.append("")
    lines.append(f"_Generated from the evidence fabric on {TODAY.isoformat()}. "
                 f"Citations link to claims in evidence/claims/._")

    article = "\n".join(lines) + "\n"
    out_dir = _wiki_root() / "topics"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.md"
    if not dry_run:
        out_path.write_text(article, encoding="utf-8")
    return out_path, len(claims)


def _generate_project_article(project, config, dry_run=False, mode=None):
    """Generate a project narrative summary from claims + decisions."""
    rc = get_repo_config(config, project)
    if not rc:
        return None, 0
    claims = sorted((CORPUS_ROOT / "evidence" / "claims").glob(f"claim-{project}-*.md"))
    claims += sorted((CORPUS_ROOT / "evidence" / "claims").glob(f"claim-{project.replace('-', '_')}*.md"))
    # dedup
    seen = set()
    claims = [c for c in claims if not (c.stem in seen or seen.add(c.stem))]
    if not claims:
        return None, 0
    # staleness
    current, flagged, stale = [], [], []
    for cp in claims:
        s = cp.read_text(encoding="utf-8", errors="replace")
        ra = re.search(r"review_after: (\S+)", s)
        sa = re.search(r"stale_after: (\S+)", s)
        tier, _, _ = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
        statement = re.search(r'statement: "?([^\n]+)', s)
        st = statement.group(1) if statement else ""
        if tier == 3:
            stale.append((cp, st))
        elif tier == 2:
            flagged.append((cp, st))
        else:
            current.append((cp, st))

    # decisions
    decisions_dir = CORPUS_ROOT / "projects" / project / "decisions"
    decisions = sorted((decisions_dir := CORPUS_ROOT / "projects" / project / "decisions").glob("*.md")) if decisions_dir.is_dir() else []

    slug = re.sub(r"[^a-z0-9-]+", "-", project).strip("-")

    # LLM mode: generate a project retrospective
    mode = mode or config.get("wiki", {}).get("generation", {}).get("default") or "hybrid"
    if mode in ("llm", "hybrid") and (mode == "llm" or len(current) >= 10):
        try:
            # find topic articles that cite this project's claims
            topic_links = []
            topics_dir = _wiki_root() / "topics"
            if topics_dir.is_dir():
                for tf in sorted(topics_dir.glob("*.md")):
                    tf_text = tf.read_text(encoding="utf-8", errors="replace")
                    if f"claim-{project}" in tf_text or f"claim-{project.replace('-','_')}" in tf_text:
                        title_m = re.search(r"^title: (.+)$", tf_text, re.MULTILINE)
                        topic_links.append((tf.stem, title_m.group(1) if title_m else tf.stem))

            # gather insight takeaways for this project
            insight_takeaways = []
            for ins_file in sorted((CORPUS_ROOT / "evidence" / "insights").glob("*.md")):
                ins_text = ins_file.read_text(encoding="utf-8", errors="replace")
                if project in ins_text:
                    for line in ins_text.splitlines():
                        if line.startswith("- **[") and "— " in line:
                            insight_takeaways.append(line.strip("- ").strip("*").strip())
            # gather promoted patterns
            promoted = []
            for pf in sorted(Path("patterns").glob("pattern-*.md")):
                pt = re.search(r"^title: (.+)$", pf.read_text(), re.MULTILINE)
                promoted.append((pf.stem, pt.group(1).strip() if pt else pf.stem))
            body = _llm_project_article(project, [cp for cp, st in current[:30]], topic_links,
                                        insight_takeaways[:15], promoted, dry_run=dry_run)
            if body:
                lines = [
                    "---",
                    f"type: index",
                    f"title: \"{project}: What We Learned\"",
                    f"review_after: {(TODAY + timedelta(days=180)).isoformat()}",
                    f"---",
                    f"",
                    body,
                    f"",
                    f"---",
                    f"",
                    f"_Generated from the evidence fabric on {TODAY.isoformat()}. "
                    f"{len(current)} current claim(s) from {len(claims)} analyzed sources._",
                ]
                article = "\n".join(lines) + "\n"
                out_dir = _wiki_root() / "projects"
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{project}.md"
                if not dry_run:
                    out_path.write_text(article, encoding="utf-8")
                return out_path, len(current)
        except Exception as e:
            print(f"  LLM generation failed for {project}: {e} — falling back to mechanical", file=sys.stderr)

    lines = [
        "---",
        f"type: index",
        f"title: \"{project}: What We Learned\"",
        f"review_after: {(TODAY + timedelta(days=180)).isoformat()}",
        f"---",
        f"",
        f"# {project}: What We Learned",
        f"",
        f"## Current state",
        f"",
        f"{len(current)} verified claim(s) from {len(claims)} analyzed sources.",
    ]
    if flagged:
        lines.append(f"⚠️ {len(flagged)} claim(s) due for review.")
    if stale:
        lines.append(f"❌ {len(stale)} claim(s) stale (archived below).")
    lines += ["", "## Key findings", ""]
    footnotes = []
    for cp, st in current[:15]:
        ref, note = _cite_claim(cp, len(footnotes) + 1)
        lines.append(f"- {st[:140]} {ref}")
        footnotes.append(note)
    if decisions:
        lines += ["", "## Binding decisions", ""]
        for d in decisions:
            fm_title = re.search(r"^title: (.+)$", d.read_text(), re.MULTILINE)
            lines.append(f"- {fm_title.group(1) if fm_title else d.stem}")
    if stale:
        lines += ["", "## Archived (stale)", ""]
        for cp, st in stale[:10]:
            lines.append(f"- {st[:120]}")
    if footnotes:
        lines.append("")
        lines.append("---")
        lines.append("")
        for fn in footnotes:
            lines.append(fn)
    lines.append("")
    article = "\n".join(lines) + "\n"
    out_dir = _wiki_root() / "projects"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{project}.md"
    if not dry_run:
        out_path.write_text(article, encoding="utf-8")
    return out_path, len(current)


def _generate_index(topics, projects, dry_run=False):
    """Wiki front page: staleness dashboard + topic/project index."""
    report = _scan_staleness()
    lines = [
        "---",
        f"type: index",
        f"title: \"Wiki\"",
        f"generated: {TODAY.isoformat()}",
        f"---",
        f"",
        f"# Wiki",
        f"",
        f"## Review Status",
        f"",
        f"- ✅ Current: {report['current']}",
        f"- ⚠️ Due for review: {len(report['due'])}",
        f"- ⚠️ Overdue: {len(report['overdue'])}",
        f"- ❌ Archived: {len(report['stale'])}",
        f"",
        f"## Topics",
        f""]
    for t in topics:
        lines.append(f"- [[{t['slug']}]] — {t['title']} ({len(t['claims'])} claims)")
    lines += ["", "## Projects", ""]
    for p in projects:
        lines.append(f"- [[{p[0]}]] — {p[0]} ({p[1]} claims)")
    lines += ["", f"_Generated by `wf export wiki` on {TODAY.isoformat()}._"]
    out = _wiki_root() / "index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _generate_domain_hubs(topics, dry_run=False):
    """Generate one wiki/domains/<domain>.md hub per domain.

    A domain hub is a navigational page (LangChain-OpenWiki taxonomy/overview
    concept): lists the domain's topics with their one-line SUMMARY and a small
    mermaid cluster diagram, plus the domains it overlaps with. Written into the
    vault as wiki/domains/<slug>.md so Obsidian's graph shows a domain->topic
    structure. Returns the list of written paths.
    """
    from collections import OrderedDict
    # domain -> {topic_slug: {title, summary, claims, domains}}
    hubs = OrderedDict()
    for t in topics:
        tfile = _wiki_root() / "topics" / f"{t['slug']}.md"
        summary = ""
        if tfile.exists():
            m = re.search(r"^SUMMARY:\s*(.+)$", tfile.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
            summary = m.group(1).strip() if m else ""
        doms = re.findall(r"[a-z0-9-]+", t.get("domain") or "")
        if not doms:
            doms = ["misc"]
        for d in doms:
            hubs.setdefault(d, {})[t["slug"]] = {
                "title": t["title"], "summary": summary,
                "claims": len(t["claims"]), "domains": doms,
            }

    written = []
    out_dir = _wiki_root() / "domains"
    for domain, topics_map in hubs.items():
        ordered = sorted(topics_map.items())
        # cluster diagram: each topic as a node linked to the domain hub
        node_slugs = [s for s, _ in ordered]
        n_cluster = min(len(node_slugs), 20)
        mermaid_lines = ["flowchart TD"]
        mermaid_lines.append(f"    D[\"{domain}\"]")
        for s, _ in ordered[:n_cluster]:
            mermaid_lines.append(f"    D --> {s}[\"{(topics_map[s]['title'])[:40]}\"]")
        mermaid_body = "\n".join(mermaid_lines)

        body = [f"# {domain}", "",
                f"{len(ordered)} topic(s) in this domain.", ""]
        body.append("## Topics")
        body.append("")
        for slug, info in ordered:
            line = f"- [[{slug}]] — {info['title']}"
            if info["summary"]:
                line += f" — {info['summary'][:90]}"
            body.append(line)
        body.append("")
        body.append("## Cluster")
        body.append("")
        body.append("```mermaid")
        body.append(mermaid_body)
        body.append("```")
        body.append("")
        body.append("_Generated by `wf export wiki`._")
        article = "\n".join(body) + "\n"

        out_path = out_dir / f"{domain}.md"
        out_dir.mkdir(parents=True, exist_ok=True)
        article = ("---\ntype: index\ntitle: \"" + domain + "\" Hub\ngenerated: " +
                   TODAY.isoformat() + "\n---\n\n" + article)
        if not dry_run:
            out_path.write_text(article, encoding="utf-8")
        written.append(out_path)
    return written


def _scan_staleness():
    try:
        from review import scan
        return scan()
    except Exception:
        return {"current": 0, "due": [], "overdue": [], "stale": []}


def emit_citation_graph(topics, projects, dry_run=False):
    """Write registry/wiki-graph.json — the MACHINE-READABLE value of the wiki.

    The wiki's prose is human-facing; never feed it back to a model. Its
    machine value is the derived structure — the explicit node/edge network:
      nodes[]: every wiki page (topic/project) + source provenance
      edges[]: topic->claim, project->claim, claim->source, and the computed
               topic<->topic / topic<->project cross-page relations (grounded
               in shared sources/claims, never invented)
    So a GraphRAG/visualizer can represent the network without re-reading prose.

    Legacy keys (topics/projects/claim_sources) are retained for back-compat.
    """
    import json

    def _claim_tier(cp):
        s = cp.read_text(encoding="utf-8", errors="replace")
        ra = re.search(r"review_after: (\S+)", s)
        sa = re.search(r"stale_after: (\S+)", s)
        tier, _, _ = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
        return {1: "current", 2: "due", 3: "stale"}[tier]

    claim_sources = {}
    for cp in sorted((CORPUS_ROOT / "evidence" / "claims").glob("claim-*.md")):
        s = cp.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'resource: "\[\[(src-[^\]]+)\]\]"', s)
        claim_sources[cp.stem] = m.group(1) if m else None

    graph = {
        "generated": TODAY.isoformat(),
        "type": "wiki-graph",
        "nodes": [],
        "edges": [],
        "topics": [],
        "projects": [],
        "claim_sources": claim_sources,
    }

    node_ids = set()

    def _add_node(nid, label, ntype, **extra):
        if nid in node_ids:
            return
        node_ids.add(nid)
        n = {"id": nid, "label": label, "type": ntype, **extra}
        graph["nodes"].append(n)

    def _add_edge(source, target, rel, **extra):
        graph["edges"].append({"source": source, "target": target,
                               "relation": rel, **extra})

    # pages as nodes; links topic/project -> claim -> source as edges
    for t in topics:
        _add_node(f"topic:{t['slug']}", t["title"], "topic", domain=t.get("domain"), claims=len(t["claims"]))
        t_claims = []
        for cs in t["claims"]:
            cp = CORPUS_ROOT / "evidence" / "claims" / f"{cs}.md"
            if not cp.exists():
                continue
            tier = _claim_tier(cp)
            t_claims.append({"id": cs, "tier": tier})
            _add_node(f"claim:{cs}", cs, "claim", tier=tier)
            _add_edge(f"topic:{t['slug']}", f"claim:{cs}", "cites", tier=tier)
            src = claim_sources.get(cs)
            if src:
                _add_node(f"src:{src}", src, "source")
                _add_edge(f"claim:{cs}", f"src:{src}", "traces_to")
        graph["topics"].append({"slug": t["slug"], "title": t["title"],
                                "domain": t["domain"], "claims": t_claims})
    for proj in projects:
        p_claims = []
        for cp in sorted((CORPUS_ROOT / "evidence" / "claims").glob(f"claim-{proj}-*.md")):
            tier = _claim_tier(cp)
            p_claims.append({"id": cp.stem, "tier": tier})
            _add_node(f"claim:{cp.stem}", cp.stem, "claim", tier=tier)
            _add_edge(f"project:{proj}", f"claim:{cp.stem}", "cites", tier=tier)
        if p_claims:
            _add_node(f"project:{proj}", proj, "project", claims=len(p_claims))
            graph["projects"].append({"slug": proj, "claims": p_claims})

    # cross-page relations (topic<->topic, topic<->project)
    page_edges, _ = _compute_wiki_edges(topics, projects)
    proj_slugs = {p["slug"] for p in projects} if projects and not isinstance(projects[0], str) else set(projects)
    for slug, edges in page_edges.items():
        kind = "project" if slug in proj_slugs else "topic"
        src = f"{kind}:{slug}"
        for e in edges:
            tkind = "project" if e["target"] in proj_slugs else "topic"
            _add_edge(src, f"{tkind}:{e['target']}", e["kind"], weight=e["weight"])

    out_path = CORPUS_ROOT / "registry" / "wiki-graph.json"
    if not dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return out_path


def _claim_tier(cp):
    s = cp.read_text(encoding="utf-8", errors="replace")
    ra = re.search(r"review_after: (\S+)", s)
    sa = re.search(r"stale_after: (\S+)", s)
    tier, _, _ = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
    return {1: "current", 2: "due", 3: "stale"}[tier]


def _reconcile_wiki_dir(subdir, dry_run=False):
    """Delete stale generated pages in a wiki subdir so a run always reflects
    current evidence (the vault is the RESULT, never an accumulating mirror).
    Returns count of files present (removed in non-dry-run)."""
    d = _wiki_root() / subdir
    if not d.exists():
        return 0
    removed = 0
    for p in d.glob("*.md"):
        removed += 1
        if dry_run:
            continue
        try:
            p.unlink()
        except OSError:
            pass
    return removed


def _concepts_exist():
    """True when the concept layer is already populated. export regenerates topics
    from existing concepts and does NOT re-synthesize on every run (concept
    synthesis is ~1 LLM call per cluster; bounded to first-run/repair)."""
    return (CORPUS_ROOT / "concepts").exists() and list(
        (CORPUS_ROOT / "concepts").glob("concept-*.md"))


def _synthesize_concepts(config, dry_run=False):
    """Restore the concept layer (which topics are built from) before selecting
    topics — but ONLY when concepts are missing/stale, so routine exports are
    cheap. Gated on the compiler eval; returns count of concepts synthesized."""
    if _concepts_exist():
        return 0
    try:
        import synthesize as _syn
        written = _syn.synthesize_uncovered(cfg=config, dry_run=dry_run)
        return len(written)
    except Exception as e:
        print(f"  SKIP concept synthesis (unavailable): {e}", file=sys.stderr)
        return 0


def _rebuild_catalog(dry_run=False):
    """Reconcile registry/catalog.json to what is actually on disk (part C).
    Returns True on success."""
    try:
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location(
            "rebuild_index",
            str(Path(__file__).parent / "rebuild-index.py"))
        _ri = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_ri)
        root = CORPUS_ROOT
        _ri.VAULT_ROOT = root
        _ri.INDEX_PATH = root / "registry" / "catalog.json"
        categories = _ri.scan_vault()
        registry = _ri.build_catalog(categories)
        if dry_run:
            return True
        _ri.write_catalog(registry)
        return True
    except Exception:
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate the human-layer wiki from the evidence corpus")
    parser.add_argument("--project", help="Generate for one project only")
    parser.add_argument("--mode", default=None, choices=["mechanical", "llm", "hybrid"],
                       help="Override generation mode (default: fabric.yaml wiki.generation)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = get_config()
    mode = args.mode or (config.get("wiki", {}).get("generation", {}).get("default") or "hybrid")

    print(f"=== Generating wiki ({mode}) ===")

    # (B) Reconcile: clear stale generated pages so the output reflects current
    # evidence, never an accumulating set of orphans.
    n_remove_t = _reconcile_wiki_dir("topics", dry_run=args.dry_run)
    n_remove_p = _reconcile_wiki_dir("projects", dry_run=args.dry_run)
    n_remove_d = _reconcile_wiki_dir("domains", dry_run=args.dry_run)

    # (A) Restore the concept layer (topics are built FROM concepts).
    #     Gated on the compiler eval; 0-token clustering, LLM synthesis.
    n_concepts = _synthesize_concepts(config, dry_run=args.dry_run)
    if n_remove_t or n_remove_p:
        print(f"  reconciled: removed {n_remove_t} stale topic(s), {n_remove_p} stale project(s)")

    topics = select_topics()
    projects = get_all_repo_names(config)
    print(f"  Topics: {len(topics)} ({n_concepts} concept(s) synthesized) | Projects: {len(projects)}")
    print()

    # Cross-page network: real relations derivable from evidence (shared
    # sources/claims). Feeds both the per-page "Related" links and the graph.
    page_edges, node_index = _compute_wiki_edges(topics, projects)

    n_topics = 0
    for t in topics:
        out, n = _generate_topic_article(t, mode, dry_run=args.dry_run)
        if out:
            n_topics += 1
            if not args.dry_run:
                _enrich_page(out, config, mode, related_links=page_edges.get(t["slug"], []))
            print(f"  topic: {out.name} ({n} claims)")

    n_projects = 0
    for proj in get_all_repo_names(config):
        if proj == "wiki-fabric":
            continue
        out, n = _generate_project_article(proj, config, dry_run=args.dry_run, mode=mode)
        if out:
            n_projects += 1
            if not args.dry_run:
                _enrich_page(out, config, mode, related_links=page_edges.get(proj, []))
            print(f"  project: {out.name} ({n} current claims)")

    index = _generate_index(topics, [(p, 0) for p in get_all_repo_names(config)], dry_run=args.dry_run)

    # Domain hub pages: navigational structure grouping topics by domain.
    n_domains = 0
    hubs = _generate_domain_hubs(topics, dry_run=args.dry_run)
    n_domains = len(hubs)
    if hubs:
        print(f"  domain hub(s): {n_domains}")

    # Machine value of the human wiki: the citation edges, as deterministic JSON.
    graph_path = emit_citation_graph(topics, get_all_repo_names(config), dry_run=args.dry_run)

    # (C) Reconcile the machine index to disk.
    if _rebuild_catalog(dry_run=args.dry_run):
        print("  rebuilt: registry/catalog.json")

    # Human exploration is done in Obsidian's native Graph view (which renders the
    # [[wikilinks]] between generated wiki pages); no separate HTML viewer.
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Generated {n_topics} topic article(s), "
          f"{n_projects} project article(s), 1 index")
    if not args.dry_run:
        print(f"Citation graph: {graph_path}")
    print(f"Wiki: {_wiki_root()}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())