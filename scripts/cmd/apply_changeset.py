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


def slow_region_gate(diff_text, allow_override):
    """S4: a diff touching protected slow-lane content on pattern pages is
    refused without the explicit override."""
    if not diff_text:
        return True
    pattern_paths = re.findall(r"^diff --git a/((?:corpus/)?patterns/[^\s]+)",
                               diff_text, re.M)
    if not pattern_paths:
        return True
    touched = re.findall(r"^[+-](?:applicability:|counterexamples:|\s+excludes:|\s+- )",
                         diff_text, re.M)
    if touched and not allow_override:
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