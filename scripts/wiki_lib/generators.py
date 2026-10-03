"""Wiki article generators + page enrichment + provenance helpers (#124.5a)."""
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import fabric_config
from fabric_config import get_config, get_all_repo_names, get_repo_config, actor
from wf_common import now_iso_utc, claim_statement, claim_prefix_for_project, parse_frontmatter
import layout as _layout


def _corpus():
    """Resolved at CALL time (never cached): tests monkeypatch
    fabric_config.CORPUS_ROOT per-test; a cached first-read broke them."""
    return fabric_config.CORPUS_ROOT
from wiki_lib.diagrams import MERMAID_REPAIR_COMMENT, _mermaid_valid, _validate_and_repair_diagrams

TODAY = date.today()


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


def _scan_staleness():
    try:
        from review import scan
        return scan()
    except Exception:
        return {"current": 0, "due": [], "overdue": [], "stale": []}



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
#   # Key Takeaways               (the durable facts the page asserts)
#   # Sources                     (claim -> source -> locator backtrace)
# And any mermaid fence that fails a lightweight syntactic check is degraded to a
# `text` fence with a repair comment (repaired on the next run) — so a broken
# diagram never ships.
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
        cp = _layout.claims(_corpus()) / f"{cs}.md"
        if not cp.exists():
            continue
        st = claim_statement(cp)
        if st:
            takeaways.append(f"- {st.strip()[:160]} [[{cs}]]")
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
    """The wiki output dir — the LAYOUT-AWARE default (parity:
    fabric_config._default_vault_root); an explicit vault.path names the
    wiki root directly (no /wiki append — the 2026-09-30 audit found the
    double-nested wiki/wiki in nested-corpus layouts)."""
    return fabric_config._default_vault_root()


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


def _claim_tier(cp):
    """Claim freshness tier ('current'/'due'/'stale') from review_after/
    stale_after. One copy (was duplicated in edges.py + export-wiki.py —
    #155 audit)."""
    s = cp.read_text(encoding="utf-8", errors="replace")
    ra = re.search(r"review_after: (\S+)", s)
    sa = re.search(r"stale_after: (\S+)", s)
    tier, _, _ = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
    return {1: "current", 2: "due", 3: "stale"}[tier]


# --- Evidence-version freshness (#143 / living-wiki S1) ----------------------
# A claim's tier is mechanical: current while the raw source it quotes still
# carries the sha256 recorded at ingest; drifted the moment that hash changes
# (the evidence moved, even if the calendar review date hasn't arrived).

_src_cache = {}


def _source_hash(src_ref):
    """sha256 recorded on the source record for [[src-...]] (None if absent)."""
    if src_ref in _src_cache:
        return _src_cache[src_ref]
    out = None
    try:
        src_dir = _layout.sources(_corpus())
        p = src_dir / f"{src_ref}.md"
        if p.exists():
            m = re.search(r"^sha256:\s*(\S+)", p.read_text(encoding="utf-8", errors="replace"), re.M)
            if m:
                out = m.group(1)
    except Exception:
        out = None
    _src_cache[src_ref] = out
    return out


def _raw_current_hash(src_ref):
    """sha256 of the raw file behind a source record right now (None = missing)."""
    try:
        src_dir = _layout.sources(_corpus())
        p = src_dir / f"{src_ref}.md"
        s = p.read_text(encoding="utf-8", errors="replace")
        sp_m = re.search(r"^source_path:\s*(\S+)", s, re.M)
        if not sp_m:
            return None
        sp = sp_m.group(1).strip('"')
        from wf_common import sha256_file as _hash
        rp = fabric_config.CORPUS_ROOT / sp
        if not rp.exists():
            return None
        return _hash(rp)
    except Exception:
        return None


def _evidence_drift(src_ref):
    """True when the raw file's hash differs from the recorded one. Missing
    source record or unresolvable raw → False (calendar tiers still apply)."""
    recorded = _source_hash(src_ref)
    if not recorded:
        return False
    actual = _raw_current_hash(src_ref)
    if not actual:
        return False
    return actual[:12] != str(recorded)[:12]


def _claim_evidence_tier(claim_path):
    """Combined tier for a claim: max(calendar tier, evidence-drift tier).
    Drift is tier 2 ('drifted' — evidence changed, claim needs re-verify)."""
    s = claim_path.read_text(encoding="utf-8", errors="replace")
    ra = re.search(r"review_after: (\S+)", s)
    sa = re.search(r"stale_after: (\S+)", s)
    tier, label, days = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
    if tier == 3:
        return 3, label or "stale", days
    for m in re.finditer(r'\[\[(src-[\w-]+)\]\]', s):
        if _evidence_drift(m.group(1)):
            return 2, "evidence drifted", 0
    return tier, label, days

def _cite_claim(claim_path, idx):
    """Format a footnote citation for a claim. Returns (inline_ref, footnote)."""
    s = claim_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^title: (.+)$", s, re.MULTILINE)
    if m:
        title = m.group(1)[:80].strip()
    else:
        title = claim_statement(claim_path)[:80].strip() or claim_path.stem
    ra = re.search(r"review_after: (\S+)", s)
    sa = re.search(r"stale_after: (\S+)", s)
    tier, _, overdue = _staleness(ra.group(1) if ra else None, sa.group(1) if sa else None)
    if tier == 2:
        return f"⚠️[{idx}]", f"[{idx}] {claim_path.stem.replace('claim-','').replace('-',' ')} — {title} ⚠️ review overdue {overdue}d"
    return f"[{idx}]", f"[{idx}] {claim_path.stem} — {title}"

# === topic selection: concepts with >= N claims become topic articles ===
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
    from extract_backends import parse_json_array, llm_config, LLM_TEMPERATURE, ARTICLE_MAX_TOKENS
    import openai, os
    cfg = llm_config(compiler=True)
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                           timeout=float(os.environ.get("WIKI_LLM_TIMEOUT", "600")))

    evidence_parts = []
    for i, cp in enumerate(claims, 1):
        statement = claim_statement(cp)
        locator = re.search(r'locator: "?([^\n]+?)"?\s*$', cp.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
        # claim-<raw-rel-slug>-NNN: the raw rel path's FIRST segment is the
        # project — the only unambiguous cut is the frontmatter's project
        # field (structural, not a regex guess over ambiguous dashes).
        pfm, _ = parse_frontmatter(cp)
        proj_field = str(pfm.get("project") or "")
        pfm_slug = claim_prefix_for_project(proj_field).removeprefix("claim-") if proj_field else ""
        m_proj = re.match(
            rf"claim-({re.escape(pfm_slug)})-" if pfm_slug
            else r"claim-([a-z0-9]+(?:-[a-z0-9]+)*?)-[a-z0-9-]+?-\d{3}$", cp.stem)
        project = m_proj
        evidence_parts.append(
            f"[{i}] {statement if statement else cp.stem} "
            f"(from {project.group(1) if project else '?'}"
            f"{', ' + locator.group(1) if locator else ''})")
    evidence_text = "\n".join(evidence_parts)

    prompt = WIKI_ARTICLE_PROMPT.format(title=topic["title"], evidence=evidence_text)
    resp = client.chat.completions.create(
        model=cfg["model"], temperature=LLM_TEMPERATURE, max_tokens=ARTICLE_MAX_TOKENS,
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
    from extract_backends import llm_config, LLM_TEMPERATURE, ARTICLE_MAX_TOKENS
    import openai, os
    cfg = llm_config(compiler=True)
    client = openai.OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"],
                           timeout=float(os.environ.get("WIKI_LLM_TIMEOUT", "600")))

    # evidence: durable claims (not transient)
    evidence_parts = []
    for i, cp in enumerate(claims, 1):
        statement = claim_statement(cp)
        evidence_parts.append(f"[{i}] {statement if statement else cp.stem}")
    evidence_text = "\n".join(evidence_parts[:30])  # cap at 30 for context

    topic_refs = "\n".join(f"- [[{slug}]] {title}" for slug, title in topic_links)
    insights_text = "\n".join(f"- {it[:120]}" for it in insight_takeaways) if insight_takeaways else "_(none)_"
    prompt = PROJECT_ARTICLE_PROMPT.format(
        project=project, evidence=evidence_text, topic_refs=topic_refs,
        patterns="\n".join(f"- [[{ps}] {pt}" for ps, pt in patterns) if patterns else "_(none yet)_",
        insights=insights_text)
    resp = client.chat.completions.create(
        model=cfg["model"], temperature=LLM_TEMPERATURE, max_tokens=ARTICLE_MAX_TOKENS,
        messages=[{"role": "system", "content": "You write project retrospectives. Return ONLY valid markdown."},
                  {"role": "user", "content": prompt}])
    return resp.choices[0].message.content or ""


def _generate_topic_article(topic, mode="mechanical", dry_run=False):
    """Generate one topic article from a concept + its claims."""
    title = topic["title"]
    slug = re.sub(r"[^a-z0-9-]+", "-", title.lower()).strip("-")
    claims = []
    for cs in topic["claims"]:
        cp = _layout.claims(_corpus()) / f"{cs}.md"
        if cp.exists():
            claims.append(cp)
    if not claims:
        return None, 0
    # staleness tiers (calendar + evidence-version drift, #143)
    current, flagged, stale = [], [], []
    for cp in claims:
        tier, _, _ = _claim_evidence_tier(cp)
        st = claim_statement(cp)
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
    claims = sorted(_layout.claims_for_project(_corpus(), project).parent.glob(
        _layout.claims_for_project(_corpus(), project).name))
    if not claims:
        return None, 0
    # staleness (calendar + evidence-version drift, #143)
    current, flagged, stale = [], [], []
    for cp in claims:
        tier, label, _ = _claim_evidence_tier(cp)
        st = claim_statement(cp)
        if tier == 3:
            stale.append((cp, st))
        elif tier == 2:
            flagged.append((cp, st))
        else:
            current.append((cp, st))

    # decisions
    decisions_dir = _layout.projects(_corpus()) / project / "decisions"
    decisions = sorted(decisions_dir.glob("*.md")) if decisions_dir.is_dir() else []

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
                    cp = claim_prefix_for_project(project)
                    if cp in tf_text:
                        title_m = re.search(r"^title: (.+)$", tf_text, re.MULTILINE)
                        topic_links.append((tf.stem, title_m.group(1) if title_m else tf.stem))

            # gather insight takeaways for this project
            insight_takeaways = []
            for ins_file in sorted((_layout.insights(_corpus())).glob("*.md")):
                ins_text = ins_file.read_text(encoding="utf-8", errors="replace")
                if project in ins_text:
                    for line in ins_text.splitlines():
                        if line.startswith("- **[") and "— " in line:
                            insight_takeaways.append(line.strip("- ").strip("*").strip())
            # gather promoted patterns — with known boundaries (#90c): the
            # article's pattern links carry the pattern's counterexamples so
            # the agent sees where the rule does NOT apply
            promoted = []
            for pf in sorted(Path("patterns").glob("pattern-*.md")):
                text = pf.read_text()
                pt = re.search(r"^title: (.+)$", text, re.MULTILINE)
                label = pt.group(1).strip() if pt else pf.stem
                ces = re.findall(r'^  - "?([^"\n]+)', text[text.find("## Counterexamples"):] if "## Counterexamples" in text else "")
                if ces:
                    label += f" (⚠ does not apply: {ces[0][:80]})"
                promoted.append((pf.stem, label))
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
    rows = _project_steering_outputs(project, rc, config)
    lines += ["", "## Produces", "", "| Output | Kind | Source |", "|---|---|---|"] \
        if rows["outputs"] else []
    KIND_LABEL = {"pypi": "package", "npm": "package", "cli": "CLI", "service": "container service",
                  "image": "container image", "docs": "generated docs", "mcp": "MCP server",
                  "wiki": "wiki", "declared": "declared"}
    for o in rows["outputs"][:14]:
        lines.append(f"| {o['name']} | {KIND_LABEL.get(o.get('kind', ''), o.get('kind', ''))} | {o.get('source', '')} |")
    if rows["decisions"]:
        lines += ["", "## Binding decisions", ""]
        for d in rows["decisions"][:10]:
            lines.append(f"- {d}")
    if rows["patterns"]:
        lines += ["", "## Patterns (maturity ladder)", ""]
        for st, label in rows["patterns"][:10]:
            lines.append(f"- ({st}) {label}")
    if rows["questions"]:
        lines += ["", "## Open questions (molding targets)", ""]
        for qid, q in rows["questions"][:8]:
            lines.append(f"- {q} — review via `wf promote-questions --apply {qid}`")
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




def _project_steering_outputs(project, rc, config):
    """#177 S1+S2: the steering rows for one project page — outputs,
    patterns, open questions, decisions; 0-token reads over the corpus +
    the repo tree. Returns dict of render rows."""
    rows = {"outputs": [], "patterns": [], "questions": [], "decisions": []}
    repo_path = rc.get("path") or ""
    repo = (fabric_config.FABRIC_ROOT / repo_path).resolve() if repo_path else None
    try:
        import outputs as _outputs
        if repo and repo.is_dir():
            fm, _ = __import__("wf_common").parse_frontmatter(repo / ".wiki-overlay.md") if (repo / ".wiki-overlay.md").exists() else ({}, "")
            rows["outputs"] = _outputs.effective_outputs(repo, fm)
    except Exception:
        pass  # scanner unavailable → outputs section omitted (never load-bearing)
    # patterns: candidates + recommended whose provenance/project touches repo
    patterns = []
    inbox = _layout.patterns(_corpus())
    if inbox.is_dir():
        for pf in sorted(inbox.glob("pattern-*.md")):
            t = pf.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"^status: (\S+)$", t, re.M)
            st = m.group(1) if m else "candidate"
            if project in t or st in ("recommended", "standard"):
                pt = re.search(r"^title: (.+)$", t, re.MULTILINE)
                patterns.append((st, pt.group(1)[:90] if pt else pf.stem))
    rows["patterns"] = patterns
    # open questions (global + domain) — dashed module, importlib form
    try:
        import importlib as _ilu2
        _pq = _ilu2.import_module("promote-questions")
        qs = _pq.list_open_questions()
        rows["questions"] = [(p.stem, str(fm.get("question") or fm.get("title") or "")[:90])
                             for p, fm in qs if project in str(fm.get("project") or "") or project in p.stem]
    except Exception:
        pass
    # decisions binding this project
    ddir = _layout.projects(_corpus()) / project / "decisions"
    if ddir.is_dir():
        for d in sorted(ddir.glob("*.md")):
            dm = re.search(r"^title: (.+)$", d.read_text(), re.MULTILINE)
            rows["decisions"].append(dm.group(1)[:100] if dm else d.stem)
    return rows


def _render_outputs_section(rows):
    """The Produces block (#177 S1): declared + observed in one table."""
    if not rows["outputs"]:
        return []
    KIND_LABEL = {"pypi": "package", "npm": "package", "cli": "CLI", "service": "container service",
                  "image": "container image", "docs": "generated docs", "mcp": "MCP server",
                  "wiki": "wiki", "declared": "declared"}
    lines = ["", "## Produces", "", "| Output | Kind | Source |", "|---|---|---|"]
    for o in rows["outputs"][:14]:
        lines.append(f"| {o['name']} | {KIND_LABEL.get(o.get('kind', ''), o.get('kind', ''))} | {o.get('source', '')} |")
    return lines




def _steering_rows():
    """#177 S2 dashboard rows: decisions, patterns ladder, open questions,
    commitments, pending promotions (escalated first), going-dark repos,
    negative knowledge. 0-token corpus reads; absent planes render no row."""
    import importlib as _ilu2
    corpus = _corpus()
    rows = []
    # decisions
    n_dec = 0
    latest_dec = None
    for ddir in sorted((_layout.projects(corpus)).glob("*/decisions")):
        for d in sorted(ddir.glob("*.md")):
            n_dec += 1
            latest_dec = d
    if n_dec:
        t = re.search(r"^title: (.+)$", latest_dec.read_text(), re.MULTILINE) if latest_dec else None
        rows.append(("📜", "Binding decisions", f"{n_dec} (latest: {t.group(1)[:70] if t else latest_dec.stem})"))
    # patterns by maturity
    promoted = recommended = candidates = 0
    pdir = _layout.patterns(corpus)
    if pdir.is_dir():
        for pf in pdir.glob("pattern-*.md"):
            if "_inbox" in pf.parts:
                continue
            st = re.search(r"^status: (\S+)$", pf.read_text(), re.M)
            st = (st.group(1) if st else "candidate")
            if st in ("standard",): promoted += 1
            elif st in ("recommended",): recommended += 1
            else: candidates += 1
        if promoted or recommended or candidates:
            rows.append(("📐", "Patterns", f"{promoted} standard, {recommended} recommended, {candidates} candidate"))
    # open questions
    try:
        pq = _ilu2.import_module("promote-questions")
        qs = pq.list_open_questions()
        if qs:
            rows.append(("❓", "Open questions", f"{len(qs)} awaiting answers — the molding targets"))
    except Exception:
        pass
    # due commitments
    n_commit = 0
    for cdir in (_layout.projects(corpus)).glob("*/commitments"):
        n_commit += len(list(cdir.glob("*.md"))) if cdir.is_dir() else 0
    if n_commit:
        rows.append(("⏳", "Commitments", f"{n_commit} deferred obligation(s) (context surfaces them by trigger)"))
    # pending promotions (escalated first)
    try:
        prom = _ilu2.import_module("promote")
        dossiers = prom.list_pending_promotions()
        if dossiers:
            rows.append(("◆", "Pending promotions", f"{len(dossiers)} dossier(s) — review: wf promote --list"))
    except Exception:
        pass
    # knowledge sources going dark (info tier)
    try:
        gate_mod = _ilu2.import_module("gate")
        rows_dark = gate_mod._gate_contributions()
        dark = [r for r in (rows_dark[1] or []) if r.get("stale_days") is not None]
        if dark:
            names = ", ".join(r["project"] for r in dark[:3])
            rows.append(("🌑", "Knowledge sources going dark", f"{len(dark)} project(s) — {names}"))
    except Exception:
        pass
    return rows


def _research_pages():
    """#177 S3: the research plane's pages — syntheses (spike notes) +
    non-project claims' sources. Ordered by date, newest first. Returns
    [{slug, title}]."""
    corpus = _corpus()
    syn = _layout.syntheses(corpus)
    out = []
    if syn.is_dir():
        for p in sorted(syn.glob("*.md"), reverse=True):
            t = re.search(r"^title: (.+)$", p.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
            out.append({"slug": p.stem, "title": (t.group(1) if t else p.stem)[:90]})
    return out


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

    # === Steering dashboard (#177 S2): where the project stands + where a
    # human is asked to mold it. Every row derives from a corpus plane; the
    # section is ABSENT when the plane is empty (never decorative). ===
    steering = _steering_rows()
    if steering:
        lines.append("")
        lines.append("## Where the project stands")
        lines.append("")
        for icon, label, detail in steering:
            lines.append(f"- {icon} {label}: {detail}")

    # === Research index (#177 S3): the non-project-anchored plane ===
    research = _research_pages()
    if research:
        lines.append("")
        lines.append("## Research")
        lines.append("")
        for r in research:
            lines.append(f"- [[{r['slug']}]] — {r['title']}")
    lines += ["", f"_Generated by `wf export wiki` on {TODAY.isoformat()}._"]
    out = _wiki_root() / "index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not dry_run:
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


_ONTOLOGY_VOCAB = None

def _ontology_vocab_cache():
    """Ontology machine-shape, cached per process (wiki export runs are
    batch; the corpus does not change mid-export)."""
    global _ONTOLOGY_VOCAB
    if _ONTOLOGY_VOCAB is None:
        import ontology as _o
        try:
            _ONTOLOGY_VOCAB = _o.parse(
                (_layout.domains(fabric_config.CORPUS_ROOT) / "ontology.md")
                .read_text(encoding="utf-8", errors="replace"))
        except OSError:
            _ONTOLOGY_VOCAB = {"domains": set(), "aliases": {}, "tags": set()}
    return _ONTOLOGY_VOCAB


def _spelled_domains(raw):
    """topic['domain'] raw string ('agent-systems, godot-systems') -> list."""
    return [d.strip() for d in re.split(r"[,\s]+", raw or "") if d.strip()]


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
        # canonical resolve through the ontology (aliases fold; an alias
        # spelling used to mint its own hub — agent-systems.md/godot-systems.md
        # — diverging from the ontology vocabulary)
        import ontology as _o
        onto = _ontology_vocab_cache()
        resolved = sorted(_o.canonicalize(_spelled_domains(t.get("domain")), onto))
        doms = resolved or ["misc"]
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
