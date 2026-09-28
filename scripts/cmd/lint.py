#!/usr/bin/env python3
"""Deterministic lint for an evidence-first LLM wiki vault.

Usage:
  python3 scripts/cmd/lint.py [VAULT_ROOT]
  python3 scripts/cmd/lint.py --okf [VAULT_ROOT]      OKF v0.2 conformance (floor)
  python3 scripts/cmd/lint.py --hash <path>
  python3 scripts/cmd/lint.py --orphans

Exit 1 on any ERROR. Warnings do not fail.
Standard library only; PyYAML used for frontmatter if present.
"""
import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
# Explicit import bootstrap: this script's own dir (same-dir siblings)
# + scripts/lib (shared modules). No shotgun path injection.
for _dir in (_HERE, _HERE.parent / "lib"):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))
import re
import hashlib
from pathlib import Path

from fabric_config import get_config, get_ignores, is_ignored

import sys
import re
import hashlib
from pathlib import Path

try:
    import yaml
    HAVE_YAML = True
except Exception:
    HAVE_YAML = False

VALID_TYPES = {
     "source", "source-summary", "claim", "concept", "question", "synthesis",
     "decision", "experience-event", "pattern", "anti-pattern", "experiment",
     "change-set", "change-set-diff", "promotion-dossier", "ontology", "registry", "index", "log",
     "skill", "commitment",
     "attested-computation", "wiki-article", "rejection-tombstone",
}
PATTERN_STATUSES = {"candidate", "recommended", "standard", "deprecated"}
# Claim relation types: synthesis semantics (supports/contradicts/...) plus
# evidence-plane provenance (#79): originated_in (chat capture), decided_in /
# validated_in (PR/issue capture). Provenance edges never replace claims as atoms.
REL_TYPES = {
    "supports", "contradicts", "refines", "supersedes", "depends_on",
    "originated_in", "decided_in", "validated_in", "answers",
}
EXCLUDE_DIRS = {".git", ".obsidian", ".opencode", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", "graphify-out", "docs/site", "wiki", "build", "dist", "src"}
EXCLUDE_DIR_PREFIXES = ("evidence/traces", "system/always-on")
TEMPLATE_DIRS = {"global/templates", "schemas", "templates"}
HUB_KINDS = {"ontology", "registry", "index", "log"}
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
FENCE_RE = re.compile(r"^```")
INLINE_RE = re.compile(r"`[^`]+`")


def parse_frontmatter(path, _cache=None):
    """Return (fm_dict_or_None, body, error_or_None).

    #108: pass _cache to reuse a parsed entry across sections — lint walks
    the corpus 9-10× per run and YAML dominated everything (22s of 25s at
    2k files). _cache: {(path, mtime, size): (fm, body, err)}."""
    if _cache is not None:
        try:
            st = path.stat()
            key = (str(path), st.st_mtime_ns, st.st_size)
            if key in _cache:
                return _cache[key]
        except OSError:
            pass
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        out = (None, text, "missing frontmatter block")
    else:
        raw, body = m.group(1), m.group(2)
        if HAVE_YAML:
            try:
                fm = yaml.safe_load(raw)
                out = ((fm or {}), body, None)
            except Exception as e:
                out = (None, body, "yaml parse error: " + str(e)[:80])
        else:
            fm = {}
            for line in raw.splitlines():
                mm = re.match(r"([\w-]+):\s*(.*)$", line)
                if mm:
                    val = mm.group(2).strip().strip("'\"")
                    fm[mm.group(1)] = val or None
            out = fm, body, None
    if _cache is not None:
        try:
            st = path.stat()
            _cache[(str(path), st.st_mtime_ns, st.st_size)] = out
        except (OSError, NameError):
            pass
    return out


def strip_code(body):
    """Drop fenced code blocks and inline code spans."""
    out, in_fence = [], False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(INLINE_RE.sub(" ", line))
    return "\n".join(out)


def is_placeholder(target):
    return len(target) < 3 or "..." in target or any(c in target for c in "<>{}")


def sha256(path):
    h = hashlib.sha256()
    h.update(Path(path).read_bytes())
    return h.hexdigest()


_GLOBAL_IGNORES = None


def _ignores():
    global _GLOBAL_IGNORES
    if _GLOBAL_IGNORES is None:
        try:
            from fabric_config import get_config, get_ignores
            _GLOBAL_IGNORES = get_ignores(get_config())
        except Exception:
            _GLOBAL_IGNORES = {"globs": [], "compiled": []}
    return _GLOBAL_IGNORES


def md_files(vault):
    ig = _ignores()
    # Fixture bundles (tests/fixtures/okf/*) are external to the fabric vault:
    # they only participate in --okf mode when passed explicitly as --root.
    # fixture bundles (tests/fixtures/okf/*) are external to the fabric vault:
    # skip them when walking the fabric repo, but they still lint via --root pass
    for p in vault.rglob("*.md"):
        rel = p.relative_to(vault).as_posix()
        if "fixtures/okf" in rel:
            continue  # fixture bundles: only lint when explicitly passed as --root
        if ig.get("globs") or ig.get("compiled"):
            try:
                rp = p.relative_to(vault).as_posix()
            except ValueError:
                rp = p.as_posix()
            if is_ignored(rp, ig):
                continue
        rel = p.relative_to(vault)
        parts = rel.parts
        if any(x in EXCLUDE_DIRS for x in parts):
            continue
        # two-level excludes ('docs/site'): match when the file's leading
        # path segments equal the excluded dir's segments
        skip = False
        for d in EXCLUDE_DIRS:
            segs = tuple(d.split("/"))
            if len(segs) > 1 and parts[:len(segs)] == segs:
                skip = True
                break
        if skip:
            continue
        rel_posix = rel.as_posix()
        if any(rel_posix.startswith(pref) for pref in EXCLUDE_DIR_PREFIXES):
            continue
        if "raw" in parts:
             continue
        if "evaluations" in parts and "fixtures" in parts:
            continue
        # Entity pages are reference-only (no wikilinks needed)
        if "entities" in parts and "global" in parts:
            continue
        yield p, rel


def is_tpl(rel):
    return ("templates" in rel.parts or rel.as_posix().startswith("schemas/")
            or rel.name in ("README.md", "CONTRIBUTING.md", "LICENSE"))


def scope_for(rel):
    """Derive the expected scope from a page's path (AGENTS.md scope mapping)."""
    s = rel.as_posix()
    if s.startswith(("global/", "registry/", "schemas/", "evaluations/", "syntheses/", "concepts/",
                     "patterns/", "anti-patterns/", "skills/", "system/", "tests/", "templates/",
                     "questions/", "evidence/")):
        return "global"
    if s.startswith("domains/"):
        return "domain"
    if s.startswith("projects/"):
        return "project"
    return "global"


def validate_scope(fm, rel):
    """Frontmatter scope (when present) must match the path-implied scope.
    Transitional proposal artifacts (change-set / promotion-dossier /
    domain-proposal dossiers) are exempt: their scope names the TARGET of
    the proposal (e.g. scope: domains on a dossier awaiting merge), not
    the file's own location — found when propose-domains wrote dossiers
    into registry/domain-proposals/."""
    declared = fm.get("scope")
    if not declared:
        return None
    if str(fm.get("type")) in ("change-set", "promotion-dossier"):
        return None
    expected = scope_for(rel)
    if declared != expected:
        return "SCOPE %s: declared %r but path implies %r" % (rel, declared, expected)
    return None


def check_staleness(fm, rel, today):
    """Pages with review_after in the past are stale (warning; error when far past)."""
    ra = fm.get("review_after")
    if not ra:
        return None, None
    try:
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", str(ra).strip())
        if not m:
            return "REVIEW-AFTER %s: invalid date %r (expected YYYY-MM-DD)" % (rel, ra), None
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        import datetime as _dt
        review = _dt.date(y, mo, d)
    except (ValueError, TypeError):
        return "REVIEW-AFTER %s: invalid date %r" % (rel, ra), None
    if review < today:
        overdue = (today - review).days
        if overdue > 90:
            return None, "REVIEW-AFTER %s: overdue %d days (review_after: %s) — review or re-verify" % (rel, overdue, ra)
        return None, "REVIEW-AFTER %s: overdue %d day(s) (review_after: %s)" % (rel, overdue, ra)
    return None, None


def okf_conformance(vault):
    """OKF v0.2 §11 conformance (the floor view).

    Conformant if:
      1. Every non-reserved .md has a parseable YAML frontmatter block
      2. Every frontmatter has a non-empty `type`
      3. Reserved files follow their shapes when present:
         index.md (§8): sections listing concepts; root index may carry okf_version
         log.md  (§9): date headings in ISO-8601 YYYY-MM-DD form
    All other OKF rules are soft guidance — nothing else may fail the gate.
    Returns (violations, meta) where violations is a list of (code, rel, msg).
    """
    import datetime as _dt
    violations = []
    index_files, log_files = [], []
    reserved = {"index.md", "log.md"}
    date_re = re.compile(r"^#{1,3}\s*(\d{4}-\d{2}-\d{2})\s*$")
    list_re = re.compile(r"^[-*]\s+\[.+\]\(.+\)")

    # OKF concepts live in content dirs only. Scripts/tests/system are the
    # compiler, not the bundle — they don't participate in OKF conformance.
    # Exception: fixture bundles passed via --root (tests) — any .md under
    # the vault root is a concept there.
    CONCEPT_DIR_PREFIXES = (
        "evidence", "patterns", "anti-patterns", "skills", "concepts",
        "global", "registry", "domains", "projects", "syntheses",
    )
    for p, rel in md_files(vault):
        posix = rel.as_posix()
        in_concept_dir = posix.startswith(CONCEPT_DIR_PREFIXES)
        # A fixture bundle (tests/fixtures/okf/*) is itself the vault: all md files
        # under it are concepts regardless of prefix.
        is_fixture = "fixtures/okf" in str(vault)
        if not (in_concept_dir or is_fixture):
            continue
        name = rel.name
        if name in reserved:
            if name == "index.md":
                index_files.append((p, rel))
            else:
                log_files.append((p, rel))
            continue
        fm, body, err = parse_frontmatter(p)
        if err:
            violations.append(("OKF-FRONTMATTER", rel, err))
            continue
        t = fm.get("type")
        if t is None or (isinstance(t, str) and not t.strip()):
            violations.append(("OKF-TYPE", rel, "frontmatter missing non-empty `type`"))
        if name in ("AGENTS.md", "CLAUDE.md") and t is None:
            # these are instruction files, not concepts — OKF §11 requires
            # frontmatter only for concept docs; tolerate marker-managed blocks
            # by checking for our always-on markers only when parse failed above
            pass

    # index.md shape (§8) + okf_version exception
    for p, rel in index_files:
        fm, body, err = parse_frontmatter(p)
        root_okf = rel.as_posix() == "index.md"
        if err:
            if not root_okf:
                violations.append(("OKF-INDEX", rel, "index.md must parse (no frontmatter except okf_version in root)"))
        else:
            # frontmatter permitted ONLY for okf_version at root
            allowed = {"okf_version"}
            extra = set(fm.keys()) - allowed
            if not root_okf and fm:
                violations.append(("OKF-INDEX", rel, "non-root index.md must not carry frontmatter"))
            if root_okf and extra:
                violations.append(("OKF-INDEX", rel, "root index frontmatter limited to okf_version, got: %s" % sorted(extra)))
            if root_okf and fm.get("okf_version") and str(fm.get("okf_version")) != "0.2":
                violations.append(("OKF-INDEX", rel, "okf_version %r not recognized (expected '0.2')" % fm.get("okf_version")))
        # entries should be markdown links (progressive disclosure)
        listing_lines = [l for l in body.splitlines() if l.strip()]
        if listing_lines and not any(list_re.match(l) for l in listing_lines):
            violations.append(("OKF-INDEX", rel, "index lists concepts as markdown links; none found"))

    # log.md shape (§9): date headings ISO-8601
    for p, rel in log_files:
        _, body, _ = parse_frontmatter(p)
        in_fence = False
        seen_title = False
        for line in body.splitlines():
            if FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence or not line.strip():
                continue
            if line.startswith("#"):
                # §9: entry headings MUST be `## YYYY-MM-DD`. A single page-title
                # heading (e.g. `# Log`) is tolerated; anything else malformed fails.
                stripped = line.strip()
                if date_re.match(stripped):
                    continue
                if re.match(r"^#\s*\d{4}-\d{2}-\d{2}", stripped) or re.match(r"^#{2,3}\s+\[", stripped):
                    violations.append(("OKF-LOG", rel, "date heading not ISO-8601 YYYY-MM-DD: %r" % stripped[:60]))
                    break
                # tolerate one title heading only
                if stripped.count("#") == 1 and seen_title:
                    violations.append(("OKF-LOG", rel, "non-date heading in log: %r" % stripped[:60]))
                    break
                seen_title = True

    meta = {
        "okf_version": "0.2",
        "reserved_files_checked": {"index.md": len(index_files), "log.md": len(log_files)},
    }
    return violations, meta


def check_stale_after(fm, rel, today):
    """OKF v0.2 §5.5: content is stale on/after stale_after (ISO-8601 instant).
    Warning when overdue (same policy as REVIEW-AFTER)."""
    sa = fm.get("stale_after")
    if not sa:
        return None, None
    import datetime as _dt
    v = str(sa).strip()
    try:
        # date-only or full instant both accepted
        if re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            when = _dt.date(int(v[:4]), int(v[5:7]), int(v[8:10]))
        else:
            when = _dt.datetime.fromisoformat(v.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        return "STALE-AFTER %s: invalid instant %r (expected ISO-8601)" % (rel, sa), None
    if when <= today:
        overdue = (today - when).days
        if overdue > 30:
            return ("STALE-AFTER %s: overdue %d days (stale_after: %s) — review or re-verify"
                    % (rel, overdue, sa)), None
        return None, "STALE-AFTER %s: overdue %d day(s) (stale_after: %s)" % (rel, overdue, sa)
    return None, None


# Types whose native `status` field uses a NON-lifecycle vocabulary. The OKF
# lifecycle status (draft|stable|deprecated) is omitted on these to avoid
# collision (schemas/frontmatter.md — status mapping decision).
_LIFECYCLE_STATUS_TYPES = {"pattern", "anti-pattern", "source", "source-summary", "log", "ontology", "commitment"}
ACTOR_RE = re.compile(r"^(agent/[\w.@-]+/[\w.@:-]+|human:[\w.@-]+|process:[\w.@-]+)$")


def check_actors(fm, rel):
    """OKF §7 actor convention + §5.2 trust fields (best-effort, warning-level)."""
    problems = []
    gen = fm.get("generated")
    if isinstance(gen, dict):
        by = str(gen.get("by", ""))
        if by and not ACTOR_RE.match(by):
            problems.append("GENERATED %s: generated.by %r not actor convention (agent/<owner>/<model> | human:<id> | process:<id>)" % (rel, by))
    verified = fm.get("verified")
    if isinstance(verified, dict):
        verified = [verified]
    if isinstance(verified, list):
        for v in verified:
            if not isinstance(v, dict):
                continue
            by = str(v.get("by", ""))
            if by and not ACTOR_RE.match(by):
                problems.append("VERIFIED %s: verified.by %r not actor convention" % (rel, by))
    # Promotion gate ↔ OKF trust tier: maturity >= 2 requires a human: verification
    t = fm.get("type")
    if t in ("pattern", "anti-pattern"):
        st, mat = fm.get("status"), fm.get("maturity")
        if st in ("recommended", "standard") and isinstance(mat, int) and mat >= 2:
            vs = fm.get("verified") or []
            if isinstance(vs, dict):
                vs = [vs]
            humans = [v for v in (vs or []) if isinstance(v, dict) and str(v.get("by", "")).startswith("human:")]
            if not humans:
                problems.append("TRUST-TIER %s: maturity>=2 + %s requires a human: verification event (promotion gate)" % (rel, st))
    return problems


def check_ignore_config(config):
    """Deterministic ignore.* checks. Invalid regex patterns are skipped
    silently by get_ignores (so capture/lint can't crash) — but they should be
    loud in lint. Also flags entries that classify as neither glob nor regex
    shape (empty strings, regex: prefixes with no payload)."""
    probs = []
    raw = (config.get("ignore") or {}) if isinstance(config, dict) else {}

    def _scan(patterns, where):
        from fabric_config import _classify_ignore_pattern
        for pat in patterns or []:
            kind, value = _classify_ignore_pattern(pat)
            if not value:
                probs.append(f"IGNORE-CONFIG {where}: empty pattern in {kind} list")
                continue
            if kind == "regex":
                try:
                    import re as _re
                    _re.compile(value)
                except _re.error as e:
                    probs.append(f"IGNORE-CONFIG {where}: invalid regex {value!r} ({e})")

    for key in ("globs", "regexes", "patterns"):
        vals = raw.get(key) or []
        _scan(vals if isinstance(vals, list) else [vals], f"ignore.{key}")
    for slug, per in (raw.get("projects") or {}).items():
        if not isinstance(per, dict):
            continue
        for key in ("globs", "regexes", "patterns"):
            vals = per.get(key) or []
            _scan(vals if isinstance(vals, list) else [vals], f"ignore.projects.{slug}.{key}")
    return probs


def check_llm_config(config):
    """Deterministic fabric.yaml llm.* checks. Returns list of problems.
    Shape rules:
      - llm.local_model must be an on-device model id (HF '<org>/<repo>' with
        an on-device org/repo shape, .gguf file/repo, or an existing local path)
        — ollama-style tags ('name:tag') and provider namespaced ids
        ('openai/gpt-4o') are rejected: they can never run on-device.
    """
    probs = []
    llm = (config.get("llm") or {}) if isinstance(config, dict) else {}
    lm = llm.get("local_model")
    if lm in (None, "", "local"):
        return probs
    lm = str(lm).strip()
    from pathlib import Path as _P
    if _P(lm).expanduser().exists():
        return probs  # existing path: fine
    from fabric_config import looks_like_local_model
    if not looks_like_local_model(lm):
        probs.append(f"LLM-CONFIG llm.local_model: '{lm}' does not look like an "
                     f"on-device model id (expected '<org>/<repo>' HF id, *.gguf, "
                     f"or an existing local path)")
    return probs




class LintState:
    """Shared state across the lint check sections (#124.3)."""

    def __init__(self, vault, today, only_orphans=False):
        self.vault = vault
        self.errors: list = []
        self.warnings: list = []
        self.pages: dict = {}
        self.INDEX: set = set()
        self.today = today
        self.only_orphans = only_orphans
        # #108: one frontmatter parse per file per run
        self._fm_cache = {}


def _section_collect(state):
    """1. collect pages + frontmatter/type validation."""
    import yaml
    for p, rel in md_files(state.vault):
        fm, body, err = parse_frontmatter(p, _cache=state._fm_cache)
        if err and not is_tpl(rel):
            state.errors.append("FRONTMATTER %s: %s" % (rel, err))
        state.pages[rel.stem.lower()] = p
        if not isinstance(fm, dict):
            fm = {}
        t = fm.get("type")
        if t is not None and t not in VALID_TYPES and not is_tpl(rel):
            proposed = []
            try:
                proposed = (yaml.safe_load((state.vault / "fabric.yaml").read_text()) or {}).get("proposed_types") or []
            except Exception:
                proposed = []
            if t in proposed:
                state.warnings.append("PROPOSED-TYPE %s: %r is proposed, not adopted "
                                      "(add to VALID_TYPES via PR to adopt)" % (rel, t))
            else:
                state.errors.append("TYPE %s: unknown type %r" % (rel, t))
        if t in ("registry", "index"):
            for m in LINK_RE.finditer(strip_code(body)):
                state.INDEX.add(m.group(1).strip().lower())


def _section_wikilinks(state):
    """2. wikilinks resolve (skip fences, placeholders, templates)."""
    for p, rel in md_files(state.vault):
        fm, body, _ = parse_frontmatter(p, _cache=state._fm_cache)
        if is_tpl(rel):
            continue
        for m in LINK_RE.finditer(strip_code(body)):
            target = m.group(1).strip().lower()
            if is_placeholder(target):
                continue
            if target not in state.pages:
                state.errors.append("BROKEN-LINK %s: [[%s]] -> no page" % (rel, m.group(1)))


def _section_invariants(state):
    """3. claim / concept / pattern invariants + scope + staleness + relations."""
    from datetime import date as _date
    today = state.today
    for p, rel in md_files(state.vault):
        fm, _, err = parse_frontmatter(p, _cache=state._fm_cache)
        if not isinstance(fm, dict):
            continue
        scope_err = validate_scope(fm, rel)
        if scope_err:
            state.errors.append(scope_err)
        e, w = (None, None)
        if not is_tpl(rel):
            e, w = check_staleness(fm, rel, today)
        if e:
            state.errors.append(e)
        if w:
            state.warnings.append(w)
        if not is_tpl(rel):
            e2, w2 = check_stale_after(fm, rel, today)
            if e2:
                state.errors.append(e2)
            if w2:
                state.warnings.append(w2)
            for prob in check_actors(fm, rel):
                (state.errors if prob.startswith(("TRUST-TIER", "VERIFIED")) else state.warnings).append(prob)
        t = fm.get("type")
        if t == "claim":
            if not fm.get("id"):
                state.errors.append("CLAIM %s: missing id" % rel)
            if not fm.get("source_refs") and fm.get("status") != "proposed":
                state.errors.append("CLAIM %s: status!=proposed requires source_refs" % rel)
            if fm.get("status") == "superseded" and not fm.get("superseded_by"):
                state.errors.append("CLAIM %s: superseded requires superseded_by" % rel)
            for ref in (fm.get("source_refs") or []):
                if isinstance(ref, dict) and not ref.get("locator"):
                    state.warnings.append("CLAIM %s: source_ref without locator: %s" %
                                          (rel, ref.get("source", "?")))
            rels = fm.get("relations")
            if rels not in (None, []):
                if not isinstance(rels, list):
                    state.errors.append("CLAIM %s: relations must be a list" % rel)
                else:
                    for r in rels:
                        if not isinstance(r, dict) or not r.get("type") or not r.get("target"):
                            state.errors.append("CLAIM %s: relation needs {type, target}: %r" % (rel, r))
                            continue
                        if r["type"] not in REL_TYPES:
                            state.errors.append("CLAIM %s: relation type %r not in %s" %
                                                (rel, r["type"], sorted(REL_TYPES)))
                        target = str(r["target"]).strip()
                        if target.startswith("[[") and target.endswith("]]"):
                            stem = target[2:-2].split("|")[0].strip().lower()
                            if stem not in state.pages and not is_placeholder(stem):
                                state.errors.append("BROKEN-LINK %s: relation target [[%s]] -> no page" %
                                                    (rel, stem))
        if t == "question":
            qst = str(fm.get("status") or "open").lower()
            if qst not in ("proposed", "open", "answered", "superseded", "rejected"):
                state.errors.append("QUESTION %s: status %r not in proposed|open|answered|superseded|rejected" % (rel, qst))
            if qst in ("answered", "superseded") and not fm.get("answered_by"):
                state.errors.append("QUESTION %s: %s requires answered_by ([[claim-...]])" % (rel, qst))
            if not fm.get("question") and not fm.get("title"):
                state.errors.append("QUESTION %s: missing question/title" % rel)
            if qst == "open" and not fm.get("priority"):
                state.warnings.append("QUESTION %s: open without priority (P0|P1|P2 expected)" % rel)
        if t == "concept" and not fm.get("claims"):
            state.errors.append("CONCEPT %s: must link >=1 claim to draw from" % rel)
        if t == "commitment":
            if not str(fm.get("trigger") or "").strip():
                state.errors.append("COMMITMENT %s: missing trigger (condition/state that should surface it)" % rel)
            if not fm.get("owner"):
                state.errors.append("COMMITMENT %s: missing owner" % rel)
            st = str(fm.get("status") or "").lower()
            if fm.get("status") is not None and st not in ("open", "done", "cancelled", "superseded"):
                state.errors.append("COMMITMENT %s: status %r not in open|done|cancelled|superseded" % (rel, st))
            if fm.get("status") == "superseded" and not fm.get("superseded_by"):
                state.errors.append("COMMITMENT %s: superseded requires superseded_by" % rel)
            due = fm.get("due")
            if due is not None and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(due).strip()):
                state.errors.append("COMMITMENT %s: invalid due %r (expected YYYY-MM-DD)" % (rel, due))
            dep = fm.get("depends_on")
            if dep is not None and not (isinstance(dep, list) and all(isinstance(x, str) and x.startswith("[[") for x in dep)):
                state.errors.append("COMMITMENT %s: depends_on must be a list of [[wikilinks]]" % rel)
        if t in ("pattern", "anti-pattern"):
            mat, st = fm.get("maturity"), fm.get("status")
            if st in PATTERN_STATUSES:
                if st == "recommended" and not (isinstance(mat, int) and mat >= 2):
                    state.errors.append("PATTERN %s: recommended needs maturity>=2" % rel)
                if st == "standard" and not (isinstance(mat, int) and mat >= 3):
                    state.errors.append("PATTERN %s: standard needs maturity>=3" % rel)
            ce = fm.get("counterexamples")
            if st in ("recommended", "standard") and not ce:
                state.warnings.append("PATTERN %s: %s without counterexamples (boundaries expected)" % (rel, st))


def _section_dup_ids(state):
    """4. duplicate ids."""
    seen = {}
    for p, rel in md_files(state.vault):
        fm, _, _ = parse_frontmatter(p, _cache=state._fm_cache)
        if not isinstance(fm, dict):
            continue
        fm_id = fm.get("id")
        if fm_id and str(fm_id).lower() in seen:
            state.errors.append("DUP-ID %s: id %r already used by %s" %
                                (rel, fm_id, seen[str(fm_id).lower()]))
        elif fm_id:
            seen[str(fm_id).lower()] = rel


def _section_sources(state):
    """5. source hash check (templates excluded)."""
    for p, rel in md_files(state.vault):
        fm, _, _ = parse_frontmatter(p, _cache=state._fm_cache)
        if not isinstance(fm, dict):
            continue
        if fm.get("type") == "source" and not is_tpl(rel):
            sp, sh = fm.get("source_path"), fm.get("sha256")
            if not sp or not sh:
                state.errors.append("SOURCE %s: missing source_path or sha256" % rel)
                continue
            if isinstance(sh, str) and "<multi-file>" in sh:
                continue
            rp = state.vault / sp
            if not rp.exists() and (state.vault / "corpus").is_dir() and (state.vault / "corpus" / sp).exists():
                rp = state.vault / "corpus" / sp
            if not rp.exists():
                state.errors.append("SOURCE %s: raw missing: %s" % (rel, sp))
                continue
            actual = sha256(rp)
            if actual[:12] != str(sh)[:12]:
                state.errors.append("SOURCE-DRIFT %s: %s != %s" % (rel, sh[:12], actual[:12]))
        if fm.get("type") == "source" and str(fm.get("status")) == "ingested" and not is_tpl(rel):
            slug = rel.stem[4:] if rel.stem.startswith("src-") else rel.stem
            claims_dir = state.vault / "evidence" / "claims"
            found = claims_dir.is_dir() and any(claims_dir.glob(f"claim-{slug}-*.md"))
            if not found:
                state.warnings.append("SOURCE-EMPTY %s: ingested with zero claims (recover: wf ingest --reclaim <project>)" % rel)


def _section_orphans(state):
    """6. orphans (no inbound link; hubs/templates/index excluded)."""
    inbound = {}
    for p, rel in md_files(state.vault):
        fm, body, _ = parse_frontmatter(p, _cache=state._fm_cache)
        key = rel.stem.lower()
        iid = fm.get("id") if isinstance(fm, dict) else None
        if iid:
            inbound[str(iid).lower()] = inbound.get(str(iid).lower(), 0)
        for m in LINK_RE.finditer(strip_code(body)):
            tt = m.group(1).strip().lower()
            inbound[tt] = inbound.get(tt, 0) + 1
    for p, rel in md_files(state.vault):
        fm, _, _ = parse_frontmatter(p, _cache=state._fm_cache)
        if not isinstance(fm, dict):
            continue
        t = fm.get("type")
        if t in HUB_KINDS or t == "ontology" or is_tpl(rel) or rel.stem.lower() == "home-moc":
            continue
        key = rel.stem.lower()
        iid = fm.get("id") and str(fm["id"]).lower()
        linked = inbound.get(key, 0) + (inbound.get(iid, 0) if iid else 0)
        if linked == 0:
            state.warnings.append("ORPHAN %s: no inbound links" % rel)


def _section_conflicts(state):
    """6b. sync conflicts (unresolved block commit/push)."""
    conflicts_dir = state.vault / "registry" / "conflicts"
    if conflicts_dir.exists():
        for cp in conflicts_dir.glob("**/*.md"):
            fm, _, err = parse_frontmatter(cp)
            st = fm.get("status") if isinstance(fm, dict) else None
            if st == "unresolved":
                state.errors.append("SYNC-CONFLICT %s: unresolved (review, fix source page, delete, then sync push)" % cp.relative_to(state.vault))


def _section_receipts(state):
    """6c. context receipts: envelope + required fields."""
    import json as _json
    receipts_dirs = [state.vault / "registry" / "receipts"]
    projects_root = state.vault / "projects"
    if projects_root.is_dir():
        receipts_dirs.extend(sorted(projects_root.glob("*/receipts")))
    for receipts_dir in receipts_dirs:
        if not receipts_dir.is_dir():
            continue
        for rp in sorted(receipts_dir.glob("*.json")):
            try:
                data = _json.loads(rp.read_text(encoding="utf-8"))
            except Exception as e:
                state.errors.append("RECEIPT %s: not valid JSON (%s)" % (rp.relative_to(state.vault), e))
                continue
            if not isinstance(data, dict):
                state.errors.append("RECEIPT %s: not a JSON object" % rp.relative_to(state.vault))
                continue
            if data.get("$schema") != "wiki-fabric/receipt-v1":
                state.errors.append("RECEIPT %s: $schema must be 'wiki-fabric/receipt-v1', got %r"
                                    % (rp.relative_to(state.vault), data.get("$schema")))
            for field in ("receipt_id", "task", "selected", "excluded", "precedence", "namespace", "revision"):
                if field not in data:
                    state.errors.append("RECEIPT %s: missing required field %r" % (rp.relative_to(state.vault), field))
            rid = data.get("receipt_id")
            if isinstance(rid, str) and rid and rp.stem != rid:
                state.errors.append("RECEIPT %s: filename must match receipt_id (%s)" % (rp.relative_to(state.vault), rid))



def main():
    argv = sys.argv[1:]
    only_orphans = False
    only_okf = False
    out_format = "text"
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--orphans":
            only_orphans = True
        elif a == "--okf":
            only_okf = True
        elif a == "--format" and i + 1 < len(argv):
            out_format = argv[i + 1]
            i += 1
        elif a.startswith("--format="):
            out_format = a.split("=", 1)[1]
        else:
            positional.append(a)
        i += 1
    if positional:
        vault = Path(positional[0]).resolve()
    else:
        # default to the corpus root (the vault/corpus content), not the harness
        from fabric_config import CORPUS_ROOT
        vault = Path(CORPUS_ROOT).resolve()

    if positional and positional[0] == "--hash":
        print(sha256(positional[1]))
        return

    # --okf: OKF v0.2 conformance floor (§11). Suppresses wiki-fabric profile
    # checks (orphans, hash drift, maturity gates) entirely.
    if only_okf:
        import json as _json
        violations, meta = okf_conformance(vault)
        conformant = not violations
        if out_format == "json":
            print(_json.dumps({
                "vault": vault.name,
                "mode": "okf",
                "okf_version": meta["okf_version"],
                "conformant": conformant,
                "violations": [{"code": c, "page": str(r), "message": m} for c, r, m in violations],
                "reserved_files_checked": meta["reserved_files_checked"],
            }, indent=2))
        else:
            print("# OKF v0.2 conformance — %s (mode: floor)" % vault.name)
            for c, r, m in violations:
                print("VIOLATION %s %s: %s" % (c, r, m))
            if conformant:
                print("OK — conformant with OKF v0.2 §11")
            print("%d violation(s)" % len(violations))
        return 0 if conformant else 1

    if out_format not in ("text", "json"):
        print("Unknown --format: %s (expected text|json)" % out_format, file=sys.stderr)
        return 2
    import datetime as _dt
    today = _dt.date.today()

    errors, warnings = [], []
    pages = {}
    INDEX = set()
    # #108: one frontmatter parse per file per run — all check sections share
    # this cache instead of re-parsing (9-10× per run was the lint bottleneck)
    _fm_cache = {}

    # config checks
    try:
        errors.extend(check_llm_config(get_config()))
    except Exception:
        pass
    try:
        errors.extend(check_ignore_config(get_config()))
    except Exception:
        pass

    # check sections (#124.3): each section a function on shared state
    state = LintState(vault, today, only_orphans=only_orphans)
    state._fm_cache = _fm_cache
    _section_collect(state)
    _section_wikilinks(state)
    _section_invariants(state)
    _section_dup_ids(state)
    _section_sources(state)
    _section_orphans(state)
    _section_conflicts(state)
    _section_receipts(state)
    errors = state.errors
    warnings = state.warnings
    pages = state.pages
    INDEX = state.INDEX

    # 7. report
    if out_format == "json":
        import json
        okf_v, okf_meta = okf_conformance(vault)
        report = {
            "vault": vault.name,
            "pages": len(pages),
            "yaml": bool(HAVE_YAML),
            "today": today.isoformat(),
            "errors": [{"code": e.split(" ", 1)[0], "page": (e.split(" ", 1)[1].split(":", 1)[0].strip()
                                                             if " " in e else ""), "message": e}
                       for e in errors if not only_orphans],
            "warnings": [{"code": w.split(" ", 1)[0], "page": (w.split(" ", 1)[1].split(":", 1)[0].strip()
                                                                if " " in w else ""), "message": w}
                         for w in warnings],
            "counts": {"errors": len(errors), "warnings": len(warnings)},
            "okf_conformance": {
                "conformant": not okf_v,
                "okf_version": okf_meta["okf_version"],
                "violations": [{"code": c, "page": str(r), "message": m} for c, r, m in okf_v],
            },
            "ok": not errors,
        }
        print(json.dumps(report, indent=2))
        return 1 if errors else 0

    print("# Lint — %s  (pages %d, yaml %s)" % (vault.name, len(pages), HAVE_YAML))
    for e in errors if not only_orphans else []:
        print("ERROR   " + e)
    for w in warnings:
        print("WARN    " + w)
    if not errors and not warnings:
        print("OK — clean")
    print("%d error(s), %d warning(s)" % (len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())