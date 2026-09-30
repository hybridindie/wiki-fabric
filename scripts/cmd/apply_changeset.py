#!/usr/bin/env python3
# apply_changeset.py — Apply a change-set to the fabric (port of apply-changeset.sh,
# cross-platform; the S4 slow-region gate is code, not grep-on-a-diff).
#
# Usage:
#   python3 scripts/cmd/apply_changeset.py <change-set-slug> [--dry-run] [--override-slow]

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))

import argparse
import json
import re
import subprocess
from datetime import date
from pathlib import Path

from fabric_config import CORPUS_ROOT, VAULT_ROOT, get_config
from wf_common import parse_frontmatter


def parse_manifest(text):
    """Extract created/updated/deleted file lists from the manifest markdown.
    Backward-compatible with the bash parser's list-item regex."""
    created, updated, deleted = [], [], []
    section = None
    # tolerate section header variants: "## Pages created (staging)" etc.
    sec = None
    for line in text.splitlines():
        if re.match(r"^##\s+.*created", line, re.I):
            section, sec = "created", "created"
        elif re.match(r"^##\s+.*updated", line, re.I):
            section, sec = "updated", "updated"
        elif re.match(r"^##\s+.*deleted", line, re.I):
            section, sec = "deleted", "deleted"
        elif line.startswith("## "):
            section = None
    # (second pass — simple, deterministic)
    m_section, buf = None, []
    for line in text.splitlines():
        if re.match(r"^##\s+.*created", line, re.I):
            m_section = "created"
        elif re.match(r"^##\s+.*updated", line, re.I):
            m_section = "updated"
        elif re.match(r"^##\s+.*deleted", line, re.I):
            m_section = "deleted"
        elif line.startswith("## "):
            m_section = None
        m = re.match(r"^\-\s.*`([^`]+)`", line)
        if m and m_section:
            path = m.group(1).split(":")[0].strip().rstrip("/")
            path = path.split("*")[0].strip()
            if path.endswith(".md") and path not in {"evidence/sources/src-test-source"}:
                target = {"created": created, "updated": updated,
                          "deleted": deleted}[m_section]
                if path not in target:
                    target.append(path)
    return created, updated, deleted


def _stub(path, slug, created_by):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    stem = p.stem
    p.write_text(
        f"---\ntype: stub\ntitle: {stem}\ncreated: {date.today().isoformat()}\n"
        f"updated: {date.today().isoformat()}\n---\n\n# {path}\n\n"
        f"*Created by change-set {slug} — content pending*\n", encoding="utf-8")


def _fm_from_lines(lines):
    """(fm, body) from the post-diff line stream: find a `---` fence open and
    close, yaml-parse between them. Tolerant: no block → ({}, lines-as-text)."""
    try:
        import yaml
        have_yaml = True
    except ImportError:
        have_yaml = False
    text = "\n".join(lines) + "\n"
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, "\n".join(lines) + "\n"
    if not have_yaml:
        return {}, text
    try:
        return (yaml.safe_load(m.group(1)) or {}), text
    except Exception:
        return {}, text


def parse_frontmatter_text(text):
    """(fm, body) from raw text (e.g. a git-show pre-image)."""
    return _fm_from_lines(text.splitlines() + [""])


_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)
_SKIP_LINE_PREFIXES = ("diff --git", "index ", "new file", "deleted file",
                       "similarity ", "dissimilarity ", "rename ", "copy ",
                       "old mode", "new mode", "--- ", "+++ ", "Binary ")


def _reconstruct_post_state(base_text, file_diff):
    """Exact post-image of one file from its HEAD pre-image + unified diff
    hunks (default context). Hunks apply left-to-right with an offset; a missing
    pre-image (new file) means base is empty."""
    out = base_text.splitlines()
    result, pos, offset = [], 0, 0   # pos: next unconsumed base line (0-based)
    for hm in _HUNK_RE.finditer(file_diff):
        old_start = int(hm.group(1)) - 1          # 0-based
        old_len = int(hm.group(2) or "1")
        # hunk body: until next @@ or EOF
        rest = file_diff[hm.end():]
        nxt = _HUNK_RE.search(rest)
        body = rest[:nxt.start()] if nxt else rest
        hunk_pre, hunk_post = [], []
        for line in body.splitlines():
            if line.startswith("\\"):             # "\ No newline at end of file"
                continue
            if line.startswith("+"):
                hunk_post.append(line[1:])
            elif line.startswith("-"):
                hunk_pre.append(line[1:])
            elif line.startswith(" ") or line == "":
                hunk_pre.append(line[1:])
                hunk_post.append(line[1:])
        # splice: pre-consumed base + hunk post-image. Trust the pre-image
        # line count (old_len from @@ is the range start's line count but
        # context can differ after \ No-newline quirks; pre lines are exact).
        result.extend(out[pos:old_start])
        result.extend(hunk_post)
        pos = old_start + len(hunk_pre)
    result.extend(out[pos:])
    return "\n".join(result) + ("\n" if result else "")


def slow_region_gate(diff_text, allow_override):
    """S4: a diff touching protected slow-lane content on pattern pages is
    refused without the explicit override.

    The rule is the fingerprint contract in contracts.py (#151) — the SAME
    rule lint's check_slow_regions enforces; this implementation no longer
    greps the diff text (that copy matched any list item, false-positived on
    every bullet, and could disagree with lint about the same change-set).
    Mechanism: parse each touched pattern page's pre-image and post-image
    from the unified diff and compare protected_fingerprints — the diff's
    post-state is what will be committed, so that is what gets gated."""
    if not diff_text:
        return True
    diff_paths = re.findall(r"^diff --git a/((?:corpus/)?patterns/[^\s]+)",
                            diff_text, re.M)
    if not diff_paths:
        return True
    from contracts import protected_fingerprint, slow_update_justified

    def _post_state(diff_text, git_path):
        """The page's post-diff frontmatter: apply the file's hunks to its
        HEAD pre-image. For a brand-new page (no pre-image) the diff carries
        the whole file as additions."""
        chunk_re = re.compile(
            r"^diff --git a/(\S+) b/(\S+)\n(?s:.*?)(?=^diff --git a/|\Z)", re.M | re.S)
        for m in chunk_re.finditer(diff_text):
            if git_path in (m.group(1), m.group(2)):
                file_diff = m.group(0)
                break
        else:
            return {}
        old = subprocess.run(["git", "-C", str(VAULT_ROOT), "show", f"HEAD:{git_path}"],
                             capture_output=True, text=True)
        base = old.stdout if old.returncode == 0 else ""
        post = _reconstruct_post_state(base, file_diff)
        fm, _body = _fm_from_lines(post.splitlines())
        return fm

    changed = False
    for git_path in diff_paths:
        fm = _post_state(diff_text, git_path)
        if protected_fingerprint(fm) is None:
            continue
        # does the diff alter protected content vs HEAD?
        old = subprocess.run(["git", "-C", str(VAULT_ROOT), "show", f"HEAD:{git_path}"],
                             capture_output=True, text=True)
        old_fm, _ = parse_frontmatter_text(old.stdout if old.returncode == 0 else "")
        if protected_fingerprint(fm) != protected_fingerprint(old_fm):
            if not slow_update_justified(fm):
                changed = True
    if changed and not allow_override:
        print("BLOCKED: diff edits protected slow-lane content "
              "(applicability/counterexamples) on pattern pages", file=sys.stderr)
        print("Re-run with --override-slow and record a slow-update reason in verified.",
              file=sys.stderr)
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="Apply a change-set to the fabric (human-gate merge)")
    ap.add_argument("slug")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--override-slow", action="store_true",
                    help="allow edits to protected slow-lane content — record a slow-update reason in verified")
    args = ap.parse_args()

    cs_dir = Path(CORPUS_ROOT) / "evidence" / "traces" / "change-sets" / args.slug
    manifest = cs_dir / "manifest.md"
    diff_file = cs_dir / "diff.md"
    if not cs_dir.is_dir() or not manifest.exists():
        print(f"Error: change-set not found: {cs_dir}", file=sys.stderr)
        return 1

    print(f"=== Applying change-set: {args.slug} ===")
    print(f"Manifest: {manifest}\nDry run: {args.dry_run}\n")

    created, updated, deleted = parse_manifest(manifest.read_text(encoding="utf-8"))
    print(f"Pages to create: {len(created)}")
    print(f"Pages to update: {len(updated)}")
    print(f"Pages to delete: {len(deleted)}\n")

    diff_text = diff_file.read_text(encoding="utf-8") if diff_file.exists() else ""

    # Apply diff (with S4 gate)
    if diff_file.exists():
        print("Applying diff...")
        if args.dry_run:
            print(f"[DRY RUN] Would apply git apply: {diff_file}")
        else:
            if not slow_region_gate(diff_text, args.override_slow):
                return 1
            r = subprocess.run(["git", "apply", str(diff_file)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print("Error: failed to apply diff:", (r.stderr or "")[:300], file=sys.stderr)
                return 1
            print("Diff applied successfully")
    else:
        print("No diff file found, will create/update files from manifest")

    # Create/update/delete per manifest
    for f in created:
        fp = Path(f)
        if not fp.exists():
            if args.dry_run:
                print(f"[DRY RUN] Would create: {f}")
            else:
                _stub(fp, args.slug, True)
                print(f"Created: {f}")
        else:
            print(f"Exists: {f}")
    for f in updated:
        fp = Path(f)
        if fp.exists():
            print(f"Updated: {f}")
        elif args.dry_run:
            print(f"[DRY RUN] Would create (was missing): {f}")
        else:
            _stub(fp, args.slug, "updated")
            print(f"Created (was missing): {f}")
    for f in deleted:
        fp = Path(f)
        if args.dry_run:
            print(f"[DRY RUN] Would delete: {f}")
        elif fp.exists():
            subprocess.run(["git", "rm", str(fp)], capture_output=True)
            print(f"Deleted: {f}")
        else:
            print(f"Warning: delete target not found: {f}")

    if args.dry_run:
        print("\n[DRY RUN] no changes written")
        return 0

    # Rebuild registry (the python tool — not the legacy bash index)
    print("Rebuilding registry/catalog.json...")
    import subprocess as sp
    rr = sp.run([sys.executable, str(_HERE / "rebuild-index.py")],
                capture_output=True, text=True)
    if rr.returncode != 0:
        print(f"warn: rebuild-index failed: {(rr.stderr or '')[:200]}", file=sys.stderr)

    # Log
    log = Path(VAULT_ROOT) / "registry" / "log.md"
    if not log.parent.exists():
        log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a") as f:
        f.write(f"\n## {date.today().isoformat()}\n* **apply | {args.slug}**\n")
        f.write(f"- Applied change-set: {args.slug}\n")
        f.write(f"- Files created: {len(created)}, updated: {len(updated)}, "
                f"deleted: {len(deleted)}\n")

    # Lint
    print("\nRunning lint...")
    r = subprocess.run([sys.executable, str(_HERE / "lint.py"), "."],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("Error: lint failed", file=sys.stderr)
        print(r.stdout[-1500:], file=sys.stderr)
        return 1
    print("Lint: OK")

    # Commit
    print("\nCommitting...")
    subprocess.run(["git", "add", "-A"], capture_output=True)
    c = subprocess.run(["git", "commit", "-q",
                        "-m", f"apply: {args.slug} ({len(created)} created, "
                              f"{len(updated)} updated, {len(deleted)} deleted)"],
                       capture_output=True, text=True)
    if c.returncode != 0:
        print("nothing to commit (clean tree)")
    else:
        print("Committed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())