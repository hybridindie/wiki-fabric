#!/usr/bin/env bash
# bootstrap-project.sh — Set up a new project to use the global Wiki Fabric
#
# Usage: bash scripts/bootstrap-project.sh <project-root> [--name NAME] [--slug SLUG] [--domain DOMAIN] [--skill SKILL] [--source-repo "path:raw_path:globs"] [--init-git]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FABRIC_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

PROJECT_ROOT=""
PROJECT_NAME=""
PROJECT_SLUG=""
DOMAINS=("agent-systems")
SKILLS=()
SOURCE_REPOS=()
INIT_GIT=false

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --slug)
            PROJECT_SLUG="$2"
            shift 2
            ;;
        --domain)
            DOMAINS+=("$2")
            shift 2
            ;;
        --skill)
            SKILLS+=("$2")
            shift 2
            ;;
        --source-repo)
            SOURCE_REPOS+=("$2")
            shift 2
            ;;
        --init-git)
            INIT_GIT=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 <project-root> [options]"
            echo "Options:"
            echo "  --name NAME         Human-readable project name"
            echo "  --slug SLUG         Project slug (used for namespace, e.g., my-project)"
            echo "  --domain DOMAIN     Domain to load (can repeat: agent-systems, godot-systems, etc.)"
            echo "  --skill SKILL       Global skill to auto-load (can repeat)"
            echo "  --source-repo 'path:raw_path:globs'  Upstream repo to capture"
            echo "  --init-git          Initialize git repo if not already"
            echo "  -h, --help          Show this help"
            exit 0
            ;;
        *)
            if [[ -z "${PROJECT_ROOT}" ]]; then
                PROJECT_ROOT="$1"
            else
                echo "Error: Unknown argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "${PROJECT_ROOT}" ]]; then
    echo "Error: project-root required" >&2
    echo "Usage: $0 <project-root> [options]" >&2
    exit 1
fi

PROJECT_ROOT="$(cd "${PROJECT_ROOT}" && pwd)"
PROJECT_NAME="${PROJECT_NAME:-$(basename "${PROJECT_ROOT}")}"
PROJECT_SLUG="${PROJECT_SLUG:-$(basename "${PROJECT_ROOT}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')}"

echo "=== Bootstrapping project: ${PROJECT_NAME} ==="
echo "Project root: ${PROJECT_ROOT}"
echo "Project slug: ${PROJECT_SLUG}"
echo "Domains: ${DOMAINS[*]}"
echo "Skills: ${SKILLS[*]}"
echo "Source repos: ${#SOURCE_REPOS[@]}"
echo ""

mkdir -p "${PROJECT_ROOT}"
cd "${PROJECT_ROOT}"

if [[ "${INIT_GIT}" == true ]] && [[ ! -d .git ]]; then
    git init -q
    echo "Initialized git repository"
fi

# 1. Create .wiki-overlay.md
OVERLAY_FILE=".wiki-overlay.md"
cat > "${OVERLAY_FILE}" <<'OVERLAY_EOF'
---
project: __PROJECT_NAME__
namespace: __PROJECT_SLUG__
description: __PROJECT_NAME__
domains:
__DOMAINS__
skills:
__SKILLS__
source_repos:
__SOURCE_REPOS__
created: __DATE__
updated: __DATE__
---

# Project Overlay: __PROJECT_NAME__

This file configures how the global Wiki Fabric connects to this project.

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| `project` | Yes | Human-readable project name |
| `namespace` | Yes | Projects folder name (e.g., `my-project` → `projects/my-project/`) |
| `description` | No | Brief project description |
| `domains` | Yes | Domains to load (see `02-Human/Concepts/` in global fabric) |
| `skills` | No | Global skills to auto-load (from `global/skills/`) |
| `source_repos` | No | Upstream repos to capture into `evidence/raw/<repo>/` |

## Example

```yaml
project: my-awesome-app
namespace: my-awesome-app
description: A web app for managing tasks
domains:
  - agent-systems
  - web-development
skills:
  - serialize-and-verify-writes
  - batch-mutations
source_repos:
  - path: ../my-upstream-lib
    raw_path: evidence/raw/my-upstream-lib
    globs:
      - "*.md"
      - "docs/**/*.md"
```
OVERLAY_EOF

# Replace placeholders
DOMAINS_YAML=$(printf '  - %s\n' "${DOMAINS[@]}")
SKILLS_YAML=$(if [[ ${#SKILLS[@]} -gt 0 ]]; then printf '  - %s\n' "${SKILLS[@]}"; else echo "  # - serialize-and-verify-writes"; fi)

SOURCE_REPOS_YAML=""
if [[ ${#SOURCE_REPOS[@]} -gt 0 ]]; then
    for repo in "${SOURCE_REPOS[@]}"; do
        IFS=':' read -r path raw_path globs <<< "$repo"
        SOURCE_REPOS_YAML+="  - path: ${path}\n"
        SOURCE_REPOS_YAML+="    raw_path: ${raw_path}\n"
        SOURCE_REPOS_YAML+="    globs: [$(echo "${globs}" | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$/"/')]\n"
    done
else
    SOURCE_REPOS_YAML="  # - path: ../upstream-repo\n    #   raw_path: evidence/raw/upstream-repo\n    #   globs:\n    #     - \"*.md\"\n    #     - \"docs/**/*.md\"\n"
fi

sed -i.bak "s|__PROJECT_NAME__|${PROJECT_NAME}|g" "${OVERLAY_FILE}"
sed -i "s|__PROJECT_SLUG__|${PROJECT_SLUG}|g" "${OVERLAY_FILE}"
sed -i "s|__DOMAINS__|${DOMAINS_YAML}|g" "${OVERLAY_FILE}"
sed -i "s|__SKILLS__|${SKILLS_YAML}|g" "${OVERLAY_FILE}"
sed -i "s|__SOURCE_REPOS__|${SOURCE_REPOS_YAML}|g" "${OVERLAY_FILE}"
sed -i "s|__DATE__|$(date +%Y-%m-%d)|g" "${OVERLAY_FILE}"
rm -f "${OVERLAY_FILE}.bak"

echo "Created ${OVERLAY_FILE}"

# 2. Create/Update opencode.json
OPENCODE_JSON="opencode.json"
if [[ -f "${OPENCODE_JSON}" ]]; then
    echo "opencode.json exists, backing up to ${OPENCODE_JSON}.bak"
    cp "${OPENCODE_JSON}" "${OPENCODE_JSON}.bak"
fi

cat > "${OPENCODE_JSON}" <<'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "bash": {
      "*": "allow",
      "git commit *": "ask",
      "git push *": "ask",
      "rm *": "ask"
    }
  },
  "references": {
    "wiki-fabric": {
      "path": "~/wiki-fabric",
      "description": "Global knowledge fabric (evidence-first wiki + cross-project promotion)"
    }
  },
  "instructions": [
    "~/wiki-fabric/00-System/AGENTS.md",
    ".wiki-overlay.md"
  ],
  "watcher": {
    "ignore": [
      ".obsidian/**",
      "evidence/raw/**",
      "node_modules/**",
      ".git/**"
    ]
  },
  "skills": {
    "paths": [
      "~/.opencode/skills",
      "~/wiki-fabric/00-System/.opencode/skills"
    ]
  }
}
EOF

echo "Created ${OPENCODE_JSON}"

# 3. Create .gitignore additions
GITIGNORE=".gitignore"
if [[ ! -f "${GITIGNORE}" ]]; then
    touch "${GITIGNORE}"
fi

grep -qxF "evidence/raw/" .gitignore 2>/dev/null || echo "evidence/raw/" >> "${GITIGNORE}"
grep -qxF ".obsidian/" .gitignore 2>/dev/null || echo ".obsidian/" >> "${GITIGNORE}"
grep -qxF ".DS_Store" .gitignore 2>/dev/null || echo ".DS_Store" >> "${GITIGNORE}"
grep -qxF "*.pyc" .gitignore 2>/dev/null || echo "*.pyc" >> "${GITIGNORE}"
grep -qxF "__pycache__/" .gitignore 2>/dev/null || echo "__pycache__/" >> "${GITIGNORE}"

echo "Updated .gitignore"

# 4. Create basic project structure
mkdir -p docs src tests

# 5. Initialize git if requested and not already
if [[ "${INIT_GIT:-false}" == true ]] && [[ ! -d .git ]]; then
    git init -q
    git add -A
    git commit -q -m "chore: initial commit from wiki-fabric bootstrap"
    echo "Initialized git repository with initial commit"
fi

# 6. Create initial project README
if [[ ! -f "README.md" ]]; then
    cat > README.md <<EOF
# ${PROJECT_NAME}

${PROJECT_NAME} — $(date +%Y-%m-%d)

## Overview

Add project description here.

## Quick Start

\`\`\`bash
# Install dependencies
# Run tests
# Start development server
\`\`\`

## Wiki Fabric

This project uses the global [Wiki Fabric](~/wiki-fabric) for knowledge management.

\`\`\`bash
# Ingest a source
python3 ~/wiki-fabric/scripts/ingest.py evidence/raw/<source>.md

# Run lint
python3 ~/wiki-fabric/scripts/lint.py .

# Query the fabric
# In opencode: "query Why does X do Y?"
\`\`\`

## License

Add license here.
EOF
fi

echo ""
echo "=== Project bootstrap complete ==="
echo ""
echo "Project: ${PROJECT_ROOT}"
echo ""
echo "Created files:"
echo "  .wiki-overlay.md          - Project overlay config"
echo "  opencode.json             - Opencode config with wiki-fabric reference"
echo "  .gitignore                - Updated with wiki-fabric ignores"
echo "  README.md                 - Project README"
echo ""
echo "Next steps:"
echo "  1. Edit .wiki-overlay.md with your project config"
echo "  2. Add source repos to .wiki-overlay.md"
echo "  3. Run: python3 ~/wiki-fabric/scripts/ingest.py evidence/raw/<source>.md"
echo "  4. Run: python3 ~/wiki-fabric/scripts/lint.py ."
echo "  5. Open in Obsidian: open the project root as a vault"
echo ""
echo "To connect to global wiki-fabric, ensure opencode.json has:"
echo '  "references": { "wiki-fabric": { "path": "~/wiki-fabric", "description": "Global knowledge fabric" } }'
echo '  "instructions": ["~/wiki-fabric/00-System/AGENTS.md", ".wiki-overlay.md"]'