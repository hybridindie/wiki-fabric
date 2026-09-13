#!/usr/bin/env bash
# wiki-fabric — Install, update, and manage the Wiki Fabric
#
# One-liner install:
#   curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash
#
# Usage:
#   wf install [--repo URL] [--dir DIR]   # Clone + set up fabric
#   wf update                              # Pull latest + update entity index
#   wf status                              # Show fabric health
#   wf vault [PATH]                        # Create Obsidian vault symlink
#   wf bootstrap <project-path>            # Connect a project
#
# After install, the wiki-fabric CLI is available at ~/.local/bin/wiki-fabric

set -euo pipefail

# === Constants ===
FABRIC_REPO="${WIKI_FABRIC_REPO:-https://github.com/hybridindie/wiki-fabric.git}"
DEFAULT_DIR="${HOME}/Development/wiki-fabric"
DEFAULT_VAULT="${HOME}/Development/vault"
SCRIPT_NAME="wf"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}ℹ${NC}  $*"; }
ok() { echo -e "${GREEN}✓${NC}  $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
err() { echo -e "${RED}✗${NC}  $*" >&2; }

# === Helper: find fabric root ===
find_fabric() {
    # Check default location
    if [[ -d "${DEFAULT_DIR}/scripts" ]]; then
        echo "${DEFAULT_DIR}"
        return 0
    fi
    # Check sibling of current directory
    local parent="$(dirname "$(pwd)")"
    if [[ -d "${parent}/wiki-fabric/scripts" ]]; then
        echo "${parent}/wiki-fabric"
        return 0
    fi
    # Check home
    if [[ -d "${HOME}/wiki-fabric/scripts" ]]; then
        echo "${HOME}/wiki-fabric"
        return 0
    fi
    return 1
}

# === Helper: ensure fabric.yaml exists ===
ensure_fabric_yaml() {
    local fabric_dir="$1"
    local config_file="${fabric_dir}/fabric.yaml"

    if [[ -f "${config_file}" ]]; then
        return 0
    fi

    # Get owner from git config
    local owner
    owner=$(git config --global user.name 2>/dev/null || echo "you")

    # Create config from example
    if [[ -f "${fabric_dir}/fabric.yaml.example" ]]; then
        sed "s/owner: your-name/owner: ${owner}/" \
            "${fabric_dir}/fabric.yaml.example" > "${config_file}"
        ok "Created fabric.yaml (owner: ${owner})"
        warn "Edit ${config_file} to add your repos"
    else
        # Minimal config
        cat > "${config_file}" << EOF
owner: ${owner}
llm:
  base_url: http://localhost:11434/v1
  api_key: ollama
  model: qwen2.5-coder:7b
repos: {}
EOF
        ok "Created minimal fabric.yaml (owner: ${owner})"
    fi
}

# === Helper: create directory structure ===
ensure_directories() {
    local fabric_dir="$1"
    cd "${fabric_dir}"

    local dirs=(
        evidence/raw
        evidence/claims
        evidence/sources
        evidence/source-summaries
        evidence/experiments
        evidence/traces/change-sets
        evidence/_inbox
        registry/promotions
        patterns
        anti-patterns
        skills
        concepts
        projects
        syntheses
        global/entities
        global/graphs
        templates
        examples
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "${dir}"
        # .gitkeep for empty dirs
        if [[ -z "$(ls -A "${dir}" 2>/dev/null)" ]]; then
            touch "${dir}/.gitkeep"
        fi
    done
}

# === Command: install ===
cmd_install() {
    local repo_url="${WIKI_FABRIC_REPO}"
    local install_dir="${DEFAULT_DIR}"
    local skip_vault=false

    # Parse install args
    while [[ $# -gt 0 ]]; do
        case $1 in
            --repo) repo_url="$2"; shift 2 ;;
            --dir) install_dir="$2"; shift 2 ;;
            --no-vault) skip_vault=true; shift ;;
            *) shift ;;
        esac
    done

    echo ""
    echo "═══════════════════════════════════════════"
    echo "   Wiki Fabric — Install"
    echo "════════════════════════════════════════════"
    echo "  Repo:  ${repo_url}"
    echo "  Dir:   ${install_dir}"
    echo ""

    # Check if already installed
    if [[ -d "${install_dir}/.git" ]]; then
        warn "Fabric already installed at ${install_dir}"
        read -p "  Update instead? [Y/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z "$REPLY" ]]; then
            cmd_update
            return
        fi
        read -p "  Reinstall (overwrite)? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 0
        fi
        rm -rf "${install_dir}"
    fi

    # Clone
    info "Cloning ${repo_url} → ${install_dir}..."
    if ! git clone --depth 1 "${repo_url}" "${install_dir}" 2>/dev/null; then
        # If the default repo doesn't exist, initialize from scratch
        warn "Could not clone ${repo_url} (may not exist yet)"
        read -p "  Initialize fresh fabric at ${install_dir}? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ -n "$REPLY" ]]; then
            echo "Aborted."
            exit 0
        fi
        mkdir -p "${install_dir}"
        cd "${install_dir}"
        git init -q
        ok "Initialized fresh fabric at ${install_dir}"
    fi

    cd "${install_dir}"

    # Ensure directory structure
    ensure_directories

    # Ensure fabric.yaml
    ensure_fabric_yaml "${install_dir}"

    # Install CLI to local bin
    local bin_dir="${HOME}/.local/bin"
    mkdir -p "${bin_dir}"
    cp "${install_dir}/scripts/wiki-fabric.sh" "${bin_dir}/${SCRIPT_NAME}" 2>/dev/null || true
    chmod +x "${bin_dir}/${SCRIPT_NAME}" 2>/dev/null || true
    # Also create wiki-fabric alias for discoverability
    cp "${install_dir}/scripts/wiki-fabric.sh" "${bin_dir}/wiki-fabric" 2>/dev/null || true
    chmod +x "${bin_dir}/wiki-fabric" 2>/dev/null || true

    # Check if in PATH
    if ! command -v "${SCRIPT_NAME}" &>/dev/null; then
        warn "Add to PATH: export PATH=\"${bin_dir}:\$PATH\""
    fi

    echo ""
    ok "Wiki Fabric installed at ${install_dir}"
    echo ""

    # Set up vault
    if [[ "${skip_vault}" == false ]]; then
        local vault_path="$(dirname "${install_dir}")/vault"
        info "Setting up Obsidian vault at ${vault_path}..."
        bash "${install_dir}/scripts/setup-vault.sh" "${vault_path}"
        echo ""
    fi

    echo "────────────────────────────────────────────"
    echo "Next steps:"
    echo ""
    echo "  1. Edit fabric.yaml — add your repos:"
    echo "     ${install_dir}/fabric.yaml"
    echo ""
    echo "  2. Bootstrap a project:"
    echo "     ${SCRIPT_NAME} bootstrap /path/to/my-project"
    echo ""
    echo "  3. Ingest a source:"
    echo "     cd ${install_dir}"
    echo "     python3 scripts/ingest.py --extract-claims evidence/raw/<repo>/<doc>.md"
    echo ""
    echo "  4. Ask questions:"
    echo "     python3 scripts/query.py \"Why does X do Y?\""
    echo ""
    echo "  5. Log experience:"
    echo "     python3 scripts/log-experience.py --project <slug>"
    echo "────────────────────────────────────────────"
}

# === Command: update ===
cmd_update() {
    local fabric_dir
    if ! fabric_dir=$(find_fabric); then
        err "Fabric not found. Run: ${SCRIPT_NAME} install"
        exit 1
    fi

    echo ""
    info "Updating fabric at ${fabric_dir}..."
    cd "${fabric_dir}"

    # Pull latest from remote
    if git remote get-url origin &>/dev/null; then
        local local_changes=$(git status --porcelain | wc -l | tr -d ' ')
        if [[ "${local_changes}" -gt 0 ]]; then
            warn "You have ${local_changes} uncommitted changes"
            read -p "  Stash and pull? [Y/n] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z "$REPLY" ]]; then
                git stash
                git pull --rebase origin main 2>/dev/null || git pull --rebase origin master 2>/dev/null
                git stash pop
                ok "Updated (changes stashed and restored)"
            fi
        else
            git pull --rebase origin main 2>/dev/null || git pull --rebase origin master 2>/dev/null
            ok "Pulled latest"
        fi
    else
        warn "No remote configured. Add one: git remote add origin <url>"
    fi

    # Update entity index if repos are configured
    if [[ -f "fabric.yaml" ]]; then
        echo ""
        info "Updating entity index..."
        python3 scripts/build-entity-index.py --skip-enrich 2>/dev/null || true
    fi

    # Rebuild index
    echo ""
    info "Rebuilding catalog..."
    python3 scripts/rebuild-index.py 2>/dev/null || true

    # Run lint
    echo ""
    info "Verifying health..."
    if python3 scripts/lint.py . 2>/dev/null; then
        ok "Lint clean"
    else
        warn "Lint has errors — run python3 scripts/lint.py . for details"
    fi

    # Update vault symlinks if vault exists
    local vault_path="$(dirname "${fabric_dir}")/vault"
    if [[ -d "${vault_path}" ]]; then
        echo ""
        info "Refreshing vault symlinks..."
        bash "scripts/setup-vault.sh" "${vault_path}" 2>/dev/null
    fi

    echo ""
    ok "Update complete"
}

# === Command: status ===
cmd_status() {
    local fabric_dir
    if ! fabric_dir=$(find_fabric); then
        err "Fabric not found. Run: ${SCRIPT_NAME} install"
        exit 1
    fi

    echo ""
    echo "════════════════════════════════════════════"
    echo "   Wiki Fabric — Status"
    echo "════════════════════════════════════════════"
    echo ""

    # Location
    ok "Fabric: ${fabric_dir}"

    # Vault
    local vault_path="$(dirname "${fabric_dir}")/vault"
    if [[ -d "${vault_path}" ]]; then
        ok "Vault:  ${vault_path}"
    else
        warn "Vault:  not set up (run: ${SCRIPT_NAME} vault)"
    fi

    # LLM
    if [[ -f "${fabric_dir}/fabric.yaml" ]]; then
        local llm_model=$(grep "model:" "${fabric_dir}/fabric.yaml" 2>/dev/null | head -1 | awk '{print $2}')
        ok "LLM:    ${llm_model:-not configured}"
    fi

    # Inventory counts
    cd "${fabric_dir}"
    local claims=$(find evidence/claims -name "claim-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local sources=$(find evidence/sources -name "src-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local concepts=$(find concepts -name "concept-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local patterns=$(find patterns -name "pattern-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local projects=$(find projects -maxdepth 1 -type d | wc -l | tr -d ' ')
    local entities=$(find global/entities -name "entity-*.md" 2>/dev/null | wc -l | tr -d ' ')

    echo ""
    echo "  Inventory:"
    echo "    Claims:             ${claims}"
    echo "    Sources:            ${sources}"
    echo "    Concepts:           ${concepts}"
    echo "    Patterns:           ${patterns}"
    echo "    Projects connected: ${projects}"
    echo "    Entity pages:       ${entities}"

    # Lint health
    echo ""
    if python3 scripts/lint.py . 2>/dev/null; then
        ok "Lint: clean"
    else
        warn "Lint: has errors"
    fi

    # Graphify
    if [[ -d "global/graphs" ]] && [[ -n "$(ls global/graphs/*.json 2>/dev/null)" ]]; then
        ok "Graphify: graphs imported"
    else
        info "Graphify: not configured (optional)"
    fi

    echo ""
}

# === Command: vault ===
cmd_vault() {
    local fabric_dir
    if ! fabric_dir=$(find_fabric); then
        err "Fabric not found. Run: ${SCRIPT_NAME} install"
        exit 1
    fi

    local vault_path="${1:-$(dirname "${fabric_dir}")/vault}"
    echo ""
    info "Setting up Obsidian vault at ${vault_path}..."
    bash "${fabric_dir}/scripts/setup-vault.sh" "${vault_path}"
}

# === Command: bootstrap ===
cmd_bootstrap() {
    local fabric_dir
    if ! fabric_dir=$(find_fabric); then
        err "Fabric not found. Run: ${SCRIPT_NAME} install"
        exit 1
    fi

    if [[ -z "${1:-}" ]]; then
        err "Usage: ${SCRIPT_NAME} bootstrap <project-path>"
        exit 1
    fi

    echo ""
    python3 "${fabric_dir}/scripts/bootstrap-project.py" "$@"
}

# === Main dispatcher ===
case "${1:-help}" in
    install)
        shift
        cmd_install "$@"
        ;;
    update)
        cmd_update
        ;;
    status)
        cmd_status
        ;;
    vault)
        shift
        cmd_vault "$@"
        ;;
    bootstrap)
        shift
        cmd_bootstrap "$@"
        ;;
    capture)
        shift
        if [[ -z "${1:-}" ]]; then
            err "Usage: wf capture <project-slug> [--repo <path>] [--git <owner/name|path>] [--since 6m] [--limit 30]"
            exit 1
        fi
        if [[ "${2:-}" == "--git" || "${2:-}" == "-g" ]]; then
            grepo="${3:-}"
            [[ -z "$grepo" ]] && { err "Usage: wf capture <project-slug> --git <owner/name-or-path>"; exit 1; }
            project="$1"
            shift 3
            python3 "$(find_fabric)/scripts/capture-git.py" "$project" --repo "$grepo" "$@"
        else
            python3 "$(find_fabric)/scripts/capture.py" "$@"
        fi
        ;;
    ingest)
        shift
        fdir=$(find_fabric)
        if [[ -z "${1:-}" ]]; then
            err "Usage: wf ingest <source-path> [--extract-claims]"
            exit 1
        fi
        python3 "${fdir}/scripts/ingest.py" "$@"
        ;;
    query)
        shift
        python3 "$(find_fabric)/scripts/query.py" "$@"
        ;;
    lint)
        python3 "$(find_fabric)/scripts/lint.py" .
        ;;
    log)
        shift
        python3 "$(find_fabric)/scripts/log-experience.py" "$@"
        ;;
    help|--help|-h)
        echo ""
        echo "════════════════════════════════════════════"
        echo "   Wiki Fabric CLI"
        echo "════════════════════════════════════════════"
        echo ""
        echo "Usage: ${SCRIPT_NAME} <command> [options]"
        echo ""
        echo "Commands:"
        echo "  install [--repo URL] [--dir DIR]  Install fabric from repo URL"
        echo "  update                            Pull latest + rebuild entity index"
        echo "  status                            Show fabric health + inventory"
        echo "  vault [PATH]                      Create Obsidian vault (symlinks)"
        echo "  bootstrap <project-path>          Connect a project to the fabric"
        echo "  capture <project-slug>            Capture upstream repo docs → evidence/raw/"
        echo "                                    (--git owner/name or /path captures PR/issue history)"
        echo "  ingest <source-path>              Ingest a source (--extract-claims for LLM)"
        echo "  query \"<question>\"                 Ask the fabric a question"
        echo "  log --project <slug>              Log an experience event"
        echo "  lint                              Run deterministic linter"
        echo ""
        echo "Environment:"
        echo "  WIKI_FABRIC_REPO  Git URL (default: ${FABRIC_REPO})"
        echo ""
        echo "One-liner install:"
        echo "  curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash"
        echo "  (installs as 'wf' + 'wiki-fabric' at ~/.local/bin/)"
        echo ""
        ;;
    *)
        err "Unknown command: $1"
        echo "Run: ${SCRIPT_NAME} help"
        exit 1
        ;;
esac