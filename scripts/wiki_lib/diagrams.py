"""Mermaid fence extraction/validation/repair (#124.5a)."""
import re


MERMAID_REPAIR_COMMENT = "OPENWIKI-REPAIR"


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
