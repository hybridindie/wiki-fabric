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

# === Helper: ensure uv is available (install if missing) ===
ensure_uv() {
    if command -v uv &>/dev/null; then
        return 0
    fi
    info "uv not found — installing (official installer)..."
    if curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; then
        export PATH="${HOME}/.local/bin:${PATH}"
        if command -v uv &>/dev/null; then
            ok "uv installed: $(uv --version 2>/dev/null | head -1)"
            return 0
        fi
    fi
    warn "Could not install uv — falling back to system python3 (pip-based deps)"
    return 1
}

# === Helper: python runner — prefers `uv run` inside the fabric, falls back to python3 ===
# Usage: run_python "${fabric_dir}" script.py args...
run_python() {
    local fabric_dir="$1"
    shift
    if [[ -x "${fabric_dir}/.venv/bin/python" ]]; then
        "${fabric_dir}/.venv/bin/python" "$@"
    elif command -v uv &>/dev/null && [[ -f "${fabric_dir}/pyproject.toml" ]]; then
        (cd "${fabric_dir}" && uv run --no-sync python "$@")
    else
        python3 "$@"
    fi
}

# === Helper: sync python deps into the fabric venv (uv-first, pip fallback) ===
sync_deps() {
    local fabric_dir="$1"
    (
        cd "${fabric_dir}" || return 1
        if [[ ! -d .venv ]] && command -v uv &>/dev/null; then
            uv venv --quiet 2>/dev/null
        fi
        if [[ -d .venv ]] && command -v uv &>/dev/null; then
            uv pip install -q -r requirements.txt --python .venv/bin/python && \
                { ok "Python dependencies synced (uv)"; return 0; }
        fi
        # Fallback: plain pip into the venv or user site
        if [[ -x .venv/bin/pip ]]; then
            .venv/bin/pip install -q -r requirements.txt && { ok "Python dependencies synced (pip)"; return 0; }
        fi
        python3 -m pip install -q -r requirements.txt && ok "Python dependencies synced (pip)" || \
            warn "Could not install python deps — LLM features may be unavailable (core CLI still works)"
    ) || true
}

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
    local repo_url="${FABRIC_REPO}"
    local install_dir="${DEFAULT_DIR}"
    local skip_vault=false
    local corpus_url=""

    # Parse install args
    while [[ $# -gt 0 ]]; do
        case $1 in
            --repo) repo_url="$2"; shift 2 ;;
            --dir) install_dir="$2"; shift 2 ;;
            --no-vault) skip_vault=true; shift ;;
            --corpus) corpus_url="$2"; shift 2 ;;
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
    ensure_directories "${install_dir}"

    # Ensure fabric.yaml
    ensure_fabric_yaml "${install_dir}"

    # Ensure uv + python, then sync dependencies into .venv
    if ensure_uv; then
        sync_deps "${install_dir}"
    fi

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

    # Wire up team corpus sync if a remote was provided
    if [[ -n "${corpus_url}" ]]; then
        info "Configuring corpus sync → ${corpus_url}"
        run_python "${install_dir}" "${install_dir}/scripts/sync.py" init "${corpus_url}"
        echo ""
    else
        echo "────────────────────────────────────────────"
        echo "Team sharing (optional): point this fabric at a shared corpus"
        echo "remote so every machine reads the same source of truth:"
        echo ""
        echo "  ${SCRIPT_NAME} sync init git@github.com:your-org/wiki-fabric-corpus.git"
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
    echo "     wf ingest evidence/raw/<repo>/<doc>.md --extract-claims"
    echo ""
    echo "  4. Ask questions:"
    echo "     wf query \"Why does X do Y?\""
    echo ""
    echo "  5. Log experience:"
    echo "     wf log --project <slug> --problem \"...\" --intervention \"...\" --outcomes \"...\""
    echo ""
    echo "  6. Share with a team:"
    echo "     wf sync init git@github.com:your-org/wiki-fabric-corpus.git"
    echo "     wf sync push   # publish your corpus; teammates: wf sync pull"
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

    # Sync python deps (in case requirements changed)
    if [[ -f "requirements.txt" ]]; then
        sync_deps "${fabric_dir}"
    fi

    # Update entity index if repos are configured
    if [[ -f "fabric.yaml" ]]; then
        echo ""
        info "Updating entity index..."
        run_python "${fabric_dir}" scripts/build-entity-index.py --skip-enrich 2>/dev/null || true
    fi

    # Rebuild index
    echo ""
    info "Rebuilding catalog..."
    run_python "${fabric_dir}" scripts/rebuild-index.py 2>/dev/null || true

    # Run lint
    echo ""
    info "Verifying health..."
    if run_python "${fabric_dir}" scripts/lint.py . 2>/dev/null; then
        ok "Lint clean"
    else
        warn "Lint has errors — run: wf lint"
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
    if run_python "${fabric_dir}" scripts/lint.py . 2>/dev/null; then
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
    run_python "${fabric_dir}" "${fabric_dir}/scripts/bootstrap-project.py" "$@"
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
            run_python "$(find_fabric)" "$(find_fabric)/scripts/capture-git.py" "$project" --repo "$grepo" "$@"
        else
            run_python "$(find_fabric)" "$(find_fabric)/scripts/capture.py" "$@"
        fi
        ;;
    ingest)
        shift
        fdir=$(find_fabric)
        if [[ -z "${1:-}" ]]; then
            err "Usage: wf ingest <source-path> [--extract-claims]"
            exit 1
        fi
        run_python "${fdir}" "${fdir}/scripts/ingest.py" "$@"
        ;;
    query)
        shift
        run_python "$(find_fabric)" "$(find_fabric)/scripts/query.py" "$@"
        ;;
    lint)
        run_python "$(find_fabric)" "$(find_fabric)/scripts/lint.py" .
        ;;
    log)
        shift
        run_python "$(find_fabric)" "$(find_fabric)/scripts/log-experience.py" "$@"
        ;;
    sync)
        shift
        fdir=$(find_fabric)
        if [[ -z "${1:-}" ]]; then
            err "Usage: wf sync {init <git-url> | status | push [-m msg] | pull}"
            exit 1
        fi
        run_python "${fdir}" "${fdir}/scripts/sync.py" "$@"
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
        echo "          [--corpus GIT-URL]        Wire team corpus sync at install time"
        echo "  update                            Pull latest + rebuild entity index"
        echo "  status                            Show fabric health + inventory"
        echo "  vault [PATH]                      Create Obsidian vault (symlinks)"
        echo "  bootstrap <project-path>          Connect a project to the fabric"
        echo "  capture <project-slug>            Capture upstream repo docs → evidence/raw/"
        echo "                                    (--git owner/name or /path captures PR/issue history)"
        echo "  ingest <source-path>              Ingest a source (--extract-claims for LLM)"
        echo "  query \"<question>\"                 Ask the fabric a question"
        echo "  log --project <slug>              Log an experience event"
        echo "  sync {init|status|push|pull}      Share the corpus with a team via a git remote"
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