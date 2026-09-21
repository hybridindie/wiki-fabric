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
DEFAULT_DIR="$(pwd)/wiki-fabric"   # harness clone default: CWD (override with --dir)
SCRIPT_NAME="wf"
WF_VERSION="0.2.0"

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
    # Prefer a venv next to the fabric, else the harness venv (deps live with
    # the code), else system python3.
    local harness_dir
    harness_dir="$(find_harness || echo "${fabric_dir}")"
    if [[ -x "${fabric_dir}/.venv/bin/python" ]]; then
        "${fabric_dir}/.venv/bin/python" "$@"
    elif [[ -x "${harness_dir}/.venv/bin/python" ]]; then
        "${harness_dir}/.venv/bin/python" "$@"
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

# === Helpers: harness vs fabric roots ===
# Harness = this repo (code). Fabric = content + config, defaults to
# ~/.local/share/wiki-fabric (XDG). In dev mode the harness clone doubles as
# the fabric when it has fabric.yaml.
fabric_home() {
    echo "${XDG_DATA_HOME:-${HOME}/.local/share}/wiki-fabric"
}

find_harness() {
    # The harness (code) — wherever this script lives, or the default clone
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
    if [[ -d "${script_dir}/scripts" ]]; then
        echo "${script_dir}"
        return 0
    fi
    if [[ -d "${DEFAULT_DIR}/scripts" ]]; then
        echo "${DEFAULT_DIR}"
        return 0
    fi
    if [[ -d "${HOME}/wiki-fabric/scripts" ]]; then
        echo "${HOME}/wiki-fabric"
        return 0
    fi
    return 1
}

# === Helper: CLI sync check (installed ~/.local/bin/wf vs harness script) ===
cli_sync_state() {
    # Returns: "current" | "stale" | "missing" | "none"
    local harness_dir script_src dest
    harness_dir="$(find_harness)" || { echo "none"; return 0; }
    script_src="${harness_dir}/scripts/wiki-fabric.sh"
    local found=""
    for dest in "${HOME}/.local/bin/wf" "${HOME}/.local/bin/wiki-fabric"; do
        if [[ -f "${dest}" ]]; then found="${dest}"; break; fi
    done
    if [[ -z "${found}" ]]; then
        echo "none"
    elif ! cmp -s "${script_src}" "${dest}" 2>/dev/null; then
        echo "stale"
    else
        echo "current"
    fi
}

# === Helper: run a harness script with the fabric as cwd ===
# Scripts live in the harness (code); content lives in the fabric dir.
run_script() {
    local fabric_dir="$1"
    local script_rel="$2"     # e.g. scripts/lint.py
    shift 2
    local harness_dir
    harness_dir="$(find_harness || echo "${fabric_dir}")"
    run_python "${fabric_dir}" "${harness_dir}/${script_rel}" "$@"
}

# === Helper: find fabric root ===
find_fabric() {
    # 1. Env override
    if [[ -n "${WIKI_FABRIC_DIR:-}" ]] && [[ -d "${WIKI_FABRIC_DIR}" ]]; then
        echo "${WIKI_FABRIC_DIR}"
        return 0
    fi
    # 2. XDG default fabric (has fabric.yaml or content dirs)
    local fh; fh="$(fabric_home)"
    if [[ -f "${fh}/fabric.yaml" ]] || [[ -d "${fh}/evidence" ]] || [[ -d "${fh}/projects" ]]; then
        echo "${fh}"
        return 0
    fi
    # 3. Dev fallback: harness clone doubles as fabric when configured
    for cand in "${DEFAULT_DIR}" "${HOME}/wiki-fabric"; do
        if [[ -f "${cand}/fabric.yaml" ]]; then
            echo "${cand}"
            return 0
        fi
    done
    # 4. Bare harness clone: scripts still runnable (lint/tests/help), commands
    #    needing content will fail with a helpful message
    for cand in "${DEFAULT_DIR}" "${HOME}/wiki-fabric"; do
        if [[ -d "${cand}/scripts" ]]; then
            echo "${cand}"
            return 0
        fi
    done
    # 5. Sibling of current directory (dev checkouts)
    local parent="$(dirname "$(pwd)")"
    if [[ -d "${parent}/wiki-fabric/scripts" ]]; then
        echo "${parent}/wiki-fabric"
        return 0
    fi
    return 1
}

# === Helper: ensure fabric.yaml exists ===
ensure_fabric_yaml() {
    local fabric_dir="$1"
    local enable_graphify="${2:-false}"
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

    # Enable optional integrations requested at install time
    if [[ "${enable_graphify}" == true ]]; then
        cat >> "${config_file}" << EOF

integrations:
  graphify:
    enabled: true
    graph_dir: graphify-out
EOF
        ok "Graphify integration enabled (set repos: with graph_dir per repo)"
        warn "Run graphify update/import per repo once repos are configured"
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
        registry/conflicts
        patterns
        anti-patterns
        skills
        concepts
        domains
        projects
        syntheses
        global/entities
        global/graphs
    )
    # templates/examples ship with the harness — don't recreate in the fabric

    for dir in "${dirs[@]}"; do
        mkdir -p "${dir}"
    done
}

# === Command: install ===

# === Interactive first-run setup: walks through fabric.yaml creation ===
interactive_setup() {
    local install_dir="$1"
    local cfg="${install_dir}/fabric.yaml"
    local cfg_dir="${install_dir}"

    echo ""
    echo "════════════════════════════════════════════"
    echo "   Wiki Fabric — First-Run Setup"
    echo "════════════════════════════════════════════"
    echo ""
    echo "  This walkthrough configures your fabric.yaml."
    echo "  Press Enter to accept the [default] at each step."
    echo ""

    # Owner
    local git_name
    git_name=$(git config --global user.name 2>/dev/null || echo "")
    read -p "  Your name/handle [${git_name:-you}]: " owner
    owner="${owner:-${git_name:-you}}"

    # LLM provider
    echo ""
    echo "  LLM endpoint — any OpenAI-compatible API works:"
    echo "    1) Ollama (local or cloud)   localhost:11434 — default"
    echo "    2) LM Studio                 localhost:1234/v1"
    echo "    3) vLLM                      localhost:8000/v1"
    echo "    4) OpenRouter                openrouter.ai/api/v1 (needs key)"
    echo "    5) Together AI               api.together.xyz/v1 (needs key)"
    echo "    6) Custom endpoint"
    read -p "  Endpoint [1]: " ep_choice
    local api_key="ollama"
    case "${ep:-1}" in
        2) base_url="http://localhost:1234/v1" ;;
        3) base_url="http://localhost:8000/v1" ;;
        4) base_url="https://openrouter.ai/api/v1"; read -p "  API key: " api_key ;;
        5) base_url="https://api.together.xyz/v1"; read -p "  API key: " api_key ;;
        6) read -p "  Base URL: " base_url; read -p "  API key [none]: " api_key ;;
        *) base_url="http://localhost:11434/v1" ;;
    esac

    read -p "  Compiler model [deepseek-v4.1-flash:cloud]: " compiler_model
    compiler_model="${compiler_model:-deepseek-v4.1-flash:cloud}"

    # Local model default (platform-split: MLX on Apple Silicon, GGUF elsewhere)
    local local_model
    local_model=$(run_python "${cfg_dir}" -c "
import sys; sys.path.insert(0, '${cfg_dir}/scripts')
from fabric_config import get_local_model; print(get_local_model())" 2>/dev/null)
    [[ -z "${local_model}" ]] && local_model="mlx-community/gemma-4-e4b-it-4bit"
    read -p "  Local model [${local_model}]: " local_model_in
    local_model="${local_model_in:-${local_model}}"

    # Extraction routing (local MLX option only on Apple Silicon)
    echo ""
    echo "  Default extraction route:"
    echo "    1) cloud — 4-6s/doc at 8 workers, recall 0.89 [default]"
    if [[ "$(uname)" == "Darwin" ]]; then
        echo "    2) local — gemma4 E4B MLX, 34s/doc, zero egress (Apple Silicon)"
    fi
    read -p "  Choice [1]: " extract_route
    case "${extract_route:-1}" in
        2) extract_route_note="# Per-repo: add 'extract: local' to repos that need privacy (requires macOS)" ;;
        *) extract_route_note="" ;;
    esac

    # Write fabric.yaml
    cat > "${cfg}" << CFG
# Wiki Fabric configuration
# Generated by wf install --interactive on $(date +%Y-%m-%d)

owner: ${owner}

llm:
  base_url: ${base_url}
  api_key: ${api_key}
  model: qwen2.5-coder:7b
  compiler_model: ${compiler_model}
  local_model: ${local_model}

repos: {}
${extract_route_note}

domains:
  agent-systems:
    signals: [agent, mcp, fastmcp, opencode, claude]
  web-systems:
    signals: [fastapi, flask, react, nextjs, supabase, postgresql]
CFG

    ok "Configured: ${cfg}"
    echo ""
}
cmd_install() {
    local repo_url="${FABRIC_REPO}"
    local install_dir="${DEFAULT_DIR}"
    local skip_vault=false
    local corpus_url=""
    local with_graphify=false
    local interactive=false

    # Parse install args
    while [[ $# -gt 0 ]]; do
        case $1 in
            --repo) repo_url="$2"; shift 2 ;;
            --dir) install_dir="$2"; shift 2 ;;
            --no-vault) skip_vault=true; shift ;;
            --corpus) corpus_url="$2"; shift 2 ;;
            --with-graphify) with_graphify=true; shift ;;
            --interactive|-i) interactive=true; shift ;;
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

    # Harness needs no content dirs — they live in the fabric (created below)

    # === Fabric dir: content + config live SEPARATELY from the harness clone ===
    # WIKI_FABRIC_DIR overrides the XDG default.
    local fabric_dir="${WIKI_FABRIC_DIR:-$(fabric_home)}"
    if [[ ! -f "${fabric_dir}/fabric.yaml" ]]; then
        mkdir -p "${fabric_dir}"
        info "Creating fabric at ${fabric_dir} (content + config; harness code stays in ${install_dir})"
    fi

    # Ensure fabric.yaml in the FABRIC dir (the harness clone keeps none)
    ensure_fabric_yaml "${fabric_dir}" "${with_graphify}"

    # Interactive first-run configuration
    if [[ -t 0 ]] && [[ ! -f "${fabric_dir}/fabric.yaml" || "${interactive}" == "true" ]]; then
        interactive_setup "${fabric_dir}"
    fi

    # Ensure content dirs in the fabric (evidence/, projects/, patterns/, ...)
    ensure_directories "${fabric_dir}"

    # The fabric is a git repo — `wf sync init` needs commits to publish the
    # initial corpus, and a local history lets you diff/revert knowledge.
    if [[ ! -d "${fabric_dir}/.git" ]]; then
        (cd "${fabric_dir}" && git init -q && git add -A && \
         git -c user.name="${owner:-wf}" -c user.email="${owner:-wf}@fabric.local" \
             commit -q -m "chore: initialize fabric" 2>/dev/null || true)
        ok "Fabric initialized as a git repo (corpus sync ready: wf sync init <url>)"
    fi

    # Ensure uv + python, then sync dependencies into the HARNESS venv
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
    ok "Wiki Fabric installed (harness: ${install_dir}; fabric: ${fabric_dir})"
    echo ""

    # Set up vault (beside the fabric by default — relative to where the
    # fabric actually lives, never a hard-coded home path)
    if [[ "${skip_vault}" == false ]]; then
        local vault_path="$(dirname "${fabric_dir}")/vault"
        info "Setting up Obsidian vault at ${vault_path}..."
        bash "${install_dir}/scripts/setup-vault.sh" "${vault_path}" 2>/dev/null || true
        run_script "${fabric_dir}" "scripts/vault-refresh.py" "${vault_path}" 2>/dev/null || true
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
    local with_graphify=false
    # Accept flag passthrough so `wf update --with-graphify` enables integrations
    local passthrough=()
    for arg in "$@"; do
        if [[ "${arg}" == "--with-graphify" ]]; then
            with_graphify=true
        else
            passthrough+=("${arg}")
        fi
    done
    if ! fabric_dir=$(find_fabric); then
        err "Fabric not found. Run: ${SCRIPT_NAME} install"
        exit 1
    fi

    echo ""
    info "Updating fabric at ${fabric_dir}..."
    cd "${fabric_dir}"

    # Enable integrations on existing fabric.yaml if requested
    if [[ "${with_graphify}" == true ]] && ! grep -q 'graphify:' fabric.yaml 2>/dev/null; then
        cat >> fabric.yaml <<'EOF'

integrations:
  graphify:
    enabled: true
    graph_dir: graphify-out
EOF
        ok "Graphify integration enabled"
    fi

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
        run_script "${fabric_dir}" "scripts/build-entity-index.py" --skip-enrich 2>/dev/null || true

        # Refresh wiki-fabric hooks in connected repos (version-stamped blocks)
        if command -v python3 >/dev/null 2>&1; then
            run_script "${fabric_dir}" "scripts/hooks.py" reinstall --repos-from-config 2>/dev/null || true
        fi

        # Self-update: refresh the installed CLI (it's a copy of this script)
        local script_src="${fabric_dir}/scripts/wiki-fabric.sh"
        for dest in "${HOME}/.local/bin/wf" "${HOME}/.local/bin/wiki-fabric"; do
            if [[ -f "${dest}" ]] && ! cmp -s "${script_src}" "${dest}" 2>/dev/null; then
                cp "${script_src}" "${dest}" && chmod +x "${dest}" && ok "CLI refreshed: ${dest}"
            fi
        done
    fi

    # Rebuild index
    echo ""
    info "Rebuilding catalog..."
    run_script "${fabric_dir}" "scripts/rebuild-index.py" 2>/dev/null || true

    # Run lint
    echo ""
    info "Verifying health..."
    if run_script "${fabric_dir}" "scripts/lint.py" . 2>/dev/null; then
        ok "Lint clean"
    else
        warn "Lint has errors — run: wf lint"
    fi

    # Update vault symlinks + structure if vault exists
    local vault_path="$(dirname "${fabric_dir}")/vault"
    if [[ -d "${vault_path}" ]]; then
        echo ""
        info "Refreshing vault..."
        bash "scripts/setup-vault.sh" "${vault_path}" 2>/dev/null || true
        run_script "${fabric_dir}" "scripts/vault-refresh.py" "${vault_path}" || true
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
        local vault_state
        vault_state=$(run_script "${fabric_dir}" "scripts/vault-refresh.py" "${vault_path}" --check --quiet 2>/dev/null; echo "exit=$?")
        if [[ "$vault_state" == *"exit=0"* ]]; then
            ok "Vault:  ${vault_path} (fresh)"
        else
            warn "Vault:  ${vault_path} (structure drift — run: wf vault)"
        fi
    else
        warn "Vault:  not set up (run: ${SCRIPT_NAME} vault)"
    fi

    # CLI sync (installed ~/.local/bin/wf vs this harness script)
    local cli_state; cli_state="$(cli_sync_state)"
    case "${cli_state}" in
        current) ok "CLI:     current (v${WF_VERSION})" ;;
        stale)   warn "CLI:   STALE - installed wf differs from harness; run: wf update" ;;
        missing) warn "CLI:   not installed - run: wf install (or copy scripts/wiki-fabric.sh to ~/.local/bin/wf)" ;;
        *)       info "CLI:   dev mode (running from harness)" ;;
    esac

    # LLM
    if [[ -f "${fabric_dir}/fabric.yaml" ]]; then
        local llm_model=$(grep "^  model:" "${fabric_dir}/fabric.yaml" 2>/dev/null | head -1 | awk '{print $2}')
        local compiler_model=$(grep "^  compiler_model:" "${fabric_dir}/fabric.yaml" 2>/dev/null | head -1 | awk '{print $2}')
        ok "LLM:    ${llm_model:-not configured}"
        ok "Compiler: ${compiler_model:-${llm_model:-not configured}} (claim extraction, synthesis, promotion)"
        local local_model
        local_model=$(run_python "${fabric_dir}" -c "
import sys; sys.path.insert(0, '${fabric_dir}/scripts')
from fabric_config import get_local_model; print(get_local_model())" 2>/dev/null)
        if [[ -n "${local_model}" ]]; then
            if run_python "${fabric_dir}" -c "
import sys, os; sys.path.insert(0, '${fabric_dir}/scripts')
from fabric_config import find_local_model_path
mid = sys.argv[1]
sys.exit(0 if find_local_model_path(mid) or os.path.isdir(os.path.expanduser(mid)) else 1)" "${local_model}" 2>/dev/null; then
                ok "Local:  ${local_model} (cached)"
            else
                warn "Local:  ${local_model} (not downloaded — run: ${SCRIPT_NAME} models ensure)"
            fi
        fi
    fi

    # Inventory counts
    cd "${fabric_dir}"
    local claims=$(find evidence/claims -name "claim-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local sources=$(find evidence/sources -name "src-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local concepts=$(find concepts -name "concept-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local patterns=$(find patterns -name "pattern-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local projects=$(find projects -maxdepth 1 -type d | wc -l | tr -d ' ')
    local entities=$(find global/entities -name "entity-*.md" 2>/dev/null | wc -l | tr -d ' ')
    local discovered
    discovered=$(run_python "${fabric_dir}" -c "
import sys; sys.path.insert(0, '${fabric_dir}/scripts')
from fabric_config import get_config, get_discovered_repos
print(len(get_discovered_repos(get_config())))" 2>/dev/null || echo 0)

    echo ""
    echo "  Inventory:"
    echo "    Claims:             ${claims}"
    echo "    Sources:            ${sources}"
    echo "    Concepts:           ${concepts}"
    echo "    Patterns:           ${patterns}"
    echo "    Projects connected: ${projects}"
    echo "    Discovered:         ${discovered} (overlay auto-discovery)"
    echo "    Entity pages:       ${entities}"

    # Lint health
    echo ""
    if run_script "${fabric_dir}" "scripts/lint.py" . 2>/dev/null; then
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
    # --check: report drift only; --quiet: no output (used by status/update)
    local check=false quiet=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --check) check=true; shift ;;
            --quiet) quiet=true; shift ;;
            *) vault_path="$1"; shift ;;
        esac
    done
    echo ""
    if [[ "$check" == true ]]; then
        info "Checking Obsidian vault at ${vault_path}..."
        run_script "${fabric_dir}" "scripts/vault-refresh.py" "${vault_path}" --check
    else
        info "Setting up / refreshing Obsidian vault at ${vault_path}..."
        bash "${fabric_dir}/scripts/setup-vault.sh" "${vault_path}" 2>/dev/null || true
        run_script "${fabric_dir}" "scripts/vault-refresh.py" "${vault_path}"
    fi
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
    run_script "${fabric_dir}" "scripts/bootstrap-project.py" "$@"
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
        if [[ "${1:-}" == "chat" ]]; then
            shift
            fdir=$(find_fabric)
            [[ -z "${1:-}" ]] && { err "Usage: wf capture chat <project-slug> [--since 30d] [--limit 20] [--harness opencode|claude|all] [--dry-run]"; exit 1; }
            run_script "${fdir}" "scripts/capture-chat.py" "$@"
            exit 0
        fi
        if [[ -z "${1:-}" ]]; then
            err "Usage: wf capture <project-slug> [--repo <path>] [--git <owner/name|path>] [--since 6m] [--limit 30]"
            exit 1
        fi
        if [[ "${2:-}" == "--git" || "${2:-}" == "-g" ]]; then
            grepo="${3:-}"
            [[ -z "$grepo" ]] && { err "Usage: wf capture <project-slug> --git <owner/name-or-path>"; exit 1; }
            project="$1"
            shift 3
            run_script "$(find_fabric)" "scripts/capture-git.py" "$project" --repo "$grepo" "$@"
        else
            run_script "$(find_fabric)" "scripts/capture.py" "$@"
        fi
        ;;
    ingest)
        shift
        fdir=$(find_fabric)
        if [[ -z "${1:-}" ]]; then
            err "Usage: wf ingest <source-path> [--extract-claims]"
            exit 1
        fi
        run_script "${fdir}" "scripts/ingest.py" "$@"
        ;;
    query)
        shift
        run_script "$(find_fabric)" "scripts/query.py" "$@"
        ;;
    context)
        shift
        fdir=$(find_fabric)
        if [[ -z "${1:-}" ]]; then
            err "Usage: wf context --task \"<task>\" [--paths <code/path>] [--project <slug>] [--format json] [--max N]"
            exit 1
        fi
        run_script "${fdir}" "scripts/context.py" "$@"
        ;;
    lint)
        run_script "$(find_fabric)" "scripts/lint.py" .
        ;;
    hook)
        shift
        fdir=$(find_fabric)
        subcmd="${1:-status}"
        shift 2>/dev/null
        export WIKI_FABRIC_DIR="${fdir}"
        run_script "${fdir}" "scripts/hooks.py" "${subcmd}" "$@"
        ;;
    claude|harness)
        shift
        fdir=$(find_fabric)
        subcmd="${1:-status}"
        shift 2>/dev/null || true
        case "${subcmd}" in
            install|status)
                run_script "${fdir}" "scripts/harnesses.py" "${subcmd}" "$@"
                ;;
            legacy)
                run_script "${fdir}" "scripts/always_on.py" "$@"
                ;;
            *)
                err "Usage: ${SCRIPT_NAME} harness {install|status} [--all|--only k1,k2] [--force]"
                exit 1
                ;;
        esac
        ;;
    okf)
        shift
        fdir=$(find_fabric)
        subcmd="${1:-export}"
        shift 2>/dev/null
        case "${subcmd}" in
            export)
                run_script "${fdir}" "scripts/okf_export.py" "$@"
                ;;
            import)
                run_script "${fdir}" "scripts/okf_import.py" "$@"
                ;;
            *)
                err "Usage: ${SCRIPT_NAME} okf {export|import} [options]"
                exit 1
                ;;
        esac
        ;;
    log)
        shift
        run_script "$(find_fabric)" "scripts/log-experience.py" "$@"
        ;;
    skill)
        shift
        fdir=$(find_fabric)
        run_script "${fdir}" "scripts/skill.py" "$@"
        ;;
    review)
        shift
        fdir=$(find_fabric)
        run_script "${fdir}" "scripts/review.py" "$@"
        ;;
    mine)
        shift
        fdir=$(find_fabric)
        subcmd="${1:-chats}"
        shift 2>/dev/null || true
        case "${subcmd}" in
            chats)
                run_script "${fdir}" "scripts/mine-chats.py" "$@"
                ;;
            *)
                err "Usage: ${SCRIPT_NAME} mine chats <project> [--since 90d] [--llm] [--dry-run]"
                exit 1
                ;;
        esac
        ;;
    models)
        shift
        fdir=$(find_fabric)
        subcmd="${1:-ensure}"
        shift 2>/dev/null || true
        case "${subcmd}" in
            ensure)
                run_script "${fdir}" "scripts/ensure-local-model.py" "$@"
                ;;
            *)
                err "Usage: ${SCRIPT_NAME} models {ensure} [--model <hf-id>] [--yes]"
                exit 1
                ;;
        esac
        ;;
    repos)
        shift
        fdir=$(find_fabric)
        subcmd="${1:-migrate}"
        shift 2>/dev/null || true
        case "${subcmd}" in
            migrate)
                run_script "${fdir}" "scripts/repos-migrate.py" "$@"
                ;;
            *)
                err "Usage: ${SCRIPT_NAME} repos migrate [--dry-run|--apply]"
                exit 1
                ;;
        esac
        ;;
    sync)
        shift
        fdir=$(find_fabric)
        if [[ -z "${1:-}" ]]; then
            err "Usage: wf sync {init <git-url> | status | push [-m msg] | pull}"
            exit 1
        fi
        run_script "${fdir}" "scripts/sync.py" "$@"
        ;;
    integrations)
        fdir=$(find_fabric)
        echo ""
        echo "Optional integrations (config: ${fdir}/fabric.yaml → integrations:)"
        echo ""
        if grep -q 'graphify:' "${fdir}/fabric.yaml" 2>/dev/null && grep -A2 'graphify:' "${fdir}/fabric.yaml" | grep -q 'enabled: true'; then
            ok "graphify: ENABLED (call-graph staleness, claim enrichment, graph expansion)"
            echo "     commands: graphify-bridge.py --all | --diff | --status"
        else
            info "graphify: inactive"
            echo "     enable: wf update --with-graphify (or fabric.yaml integrations.graphify.enabled: true)"
            echo "     effect when active: skills gain graph staleness/enrichment steps; query gains call-graph expansion"
        fi
        echo ""
        ;;
    version)
        echo "wf ${WF_VERSION} (harness: $(find_harness 2>/dev/null || echo unknown))"
        echo "installed CLI: $(cli_sync_state)"
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
        echo "          [--corpus GIT-URL] [--interactive]  Wire team corpus + force config walkthrough"
        echo "  update                            Pull latest + rebuild entity index"
        echo "  status                            Show fabric health + inventory"
        echo "  version                           Show wf version + CLI sync state"
        echo "  vault [PATH]                      Create Obsidian vault (symlinks)"
        echo "  bootstrap <project-path>          Connect a project to the fabric"
        echo "  capture <project-slug>            Capture upstream repo docs → evidence/raw/"
        echo "                                    (--git owner/name or /path captures PR/issue history)"
        echo "  capture chat <project-slug>       Capture agent chat sessions → evidence/raw/<slug>/chats/"
        echo "                                    (--since 30d --limit 20 --harness opencode|claude|all)"
        echo "  ingest <source-path>              Ingest a source (--extract-claims for LLM)"
        echo "  query \"<question>\"                 Ask the fabric a question"
        echo "  context --task \"<task>\"             Compile a task context manifest (0 tokens)"
        echo "  log --project <slug>              Log an experience event"
        echo "  models ensure [--model <hf-id>] [--yes]  Check the local model; offer download if missing"
        echo "  sync {init|status|push|pull}      Share the corpus with a team via a git remote"
        echo "  hook {install|uninstall|status}   Git post-commit auto-capture+ingest in a project"
        echo "                                    (--extract-claims: LLM runs on drift)"
        echo "  skill [--list] [<name>]           Print the procedure for a workflow (ingest, promote, ..."
        echo "                                    refresh) — universal across agent harnesses"
        echo "  review --check [--project <slug>] Staleness report: what's due, overdue, stale"
        echo "  review --verify <claim>           Re-verify a claim (rolls review_after forward)"
        echo "  mine chats <project>              Distill captured chats into durable takeaways"
        echo "                                    (patterns, anti-patterns, workflows; transients filtered)"
        echo "  harness {install|status}          Install always-on + procedures into detected agent"
        echo "                                    harnesses (--all|--only claude,copilot| --force)"
        echo "                                    (alias: claude — legacy always_on.py via 'claude legacy')"
        echo "  okf export --out DIR            Export fabric as a portable OKF v0.2 bundle"
        echo "  okf import <bundle>             Ingest an external OKF bundle as evidence"
        echo "                                    (--user for ~/.claude/CLAUDE.md)"
        echo "  lint                              Run deterministic linter"
        echo "  integrations                      Show optional integrations (graphify) status"
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