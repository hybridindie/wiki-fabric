"""Shared configuration for wiki-fabric scripts.

Reads fabric.yaml from the fabric root (or ~/.wiki-fabric/fabric.yaml fallback).
All scripts import `get_config()` instead of hardcoding repo paths, owner names,
or LLM settings.

fabric.yaml schema:
    owner: <your name>
    llm:
      base_url: http://localhost:11434/v1   # any OpenAI-compatible endpoint
      api_key: ollama                        # or a real key for cloud providers
      model: qwen2.5-coder:7b
      local_model: mlx-community/gemma-4-e4b-it-4bit   # resolves "local" routes
    repos:
      my-project:
        path: ../my-project          # relative to fabric root, or absolute
        graph_dir: graphify-out       # optional, for graphify integration
        extract: local               # route: "cloud" | "local" | explicit model
    domains:
      agent-systems:
        signals: [agent, mcp, fastmcp, opencode, claude]
      web-systems:
        signals: [fastapi, flask, react, nextjs, supabase, postgresql]
"""

import os
import sys
import re
from pathlib import Path

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

HARNESS_ROOT = Path(__file__).parent.parent


def _resolve_fabric_root():
    """Where the fabric (content + config) lives. Resolution chain:

    1. $WIKI_FABRIC_DIR                    — explicit override
    2. ~/.local/share/wiki-fabric          — default install target (contains
                                             fabric.yaml or content dirs)
    3. HARNESS_ROOT                        — dev mode: working in a harness
                                             clone that doubles as a fabric
                                             (has fabric.yaml) — or bare
                                             fallback so tests/scripts run
                                             from a checkout.

    Code (scripts/) always lives in HARNESS_ROOT; content (evidence/,
    projects/, patterns/, ...) lives in FABRIC_ROOT. In dev mode they are the
    same directory; in installed mode they are separate.
    """
    env = os.environ.get("WIKI_FABRIC_DIR")
    if env and Path(env).expanduser().is_dir():
        return Path(env).expanduser().resolve()

    xdg_data = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    default = Path(xdg_data) / "wiki-fabric"
    if default.is_dir() and ((default / CONFIG_FILENAME).exists()
                             or (default / "evidence").exists()
                             or (default / "projects").exists()):
        return default

    # Dev fallback: harness clone doubles as fabric when configured (or bare,
    # so scripts remain runnable from a checkout / tests work in CI).
    return HARNESS_ROOT


FABRIC_ROOT = _resolve_fabric_root()

# CORPUS_ROOT: where the knowledge content lives (evidence/, projects/,
# patterns/, etc). Inside the fabric dir, under corpus/ — keeps the fabric
# root clean (fabric.yaml at the root, content nested).
# Backwards compat: if content dirs exist directly at FABRIC_ROOT (pre-corpus
# layout), use FABRIC_ROOT as the corpus root.
_CORPUS_SUBDIR = "corpus"

def _resolve_corpus_root():
    corpus = FABRIC_ROOT / _CORPUS_SUBDIR
    # already nested?
    if (corpus / "evidence").exists() or (corpus / "fabric.yaml").exists():
        return corpus
    # legacy: content at fabric root?
    if (FABRIC_ROOT / "evidence").exists() or (FABRIC_ROOT / "projects").exists():
        return FABRIC_ROOT
    # fresh install: use corpus/
    return corpus

CORPUS_ROOT = _resolve_corpus_root()
CONFIG_FILENAME = "fabric.yaml"

# Local-model defaults (platform-split): MLX on Apple Silicon, GGUF elsewhere.
# mlx-community/... and unsloth/... repos are HuggingFace ids resolvable by
# mlx_lm.load / llama-cpp-python. See get_local_model() + ensure_local_model().
DEFAULT_LOCAL_MODELS = {
    "darwin": "mlx-community/gemma-4-e4b-it-4bit",
    "default": "unsloth/gemma-4-e4b-it-GGUF",
}

# Defaults when no fabric.yaml exists
_DEFAULTS = {
    "owner": "you",
    "llm": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        # ops model: cheap queries, capture, status
        "model": "qwen2.5-coder:7b",
        # compiler model: claim extraction, synthesis, promotion mining.
        # Policy (eval-stability G4): compiler runs need the most capable model —
        # cross-model extraction disagreement is capability-correlated.
        "compiler_model": "deepseek-v4.1-flash:cloud",
        # local model: resolves repos.<slug>.<stage>="local" routes.
        # Platform default (see DEFAULT_LOCAL_MODELS) or explicit HF id.
        "local_model": None,
    },
    "repos": {},
    "integrations": {
        # Optional integrations; each is off until explicitly enabled here.
        # When active, skills/scripts gain graph-aware steps (see system/skills).
        "graphify": {"enabled": False, "graph_dir": "graphify-out"},
        "embeddings": {"enabled": False, "model": "all-MiniLM-L6-v2"},
    },
    "domains": {
        "agent-systems": {"signals": ["agent", "mcp", "fastmcp", "opencode", "claude"]},
        "godot-systems": {"signals": ["godot", "gdscript", "voxel"]},
        "web-systems": {"signals": ["fastapi", "flask", "react", "nextjs", "supabase", "postgresql"]},
    },
}


def get_integrations(config):
    """Merged integrations dict with defaults (enabled: False)."""
    merged = {}
    for name, cfg in _DEFAULTS.get("integrations", {}).items():
        merged[name] = dict(cfg)
        user_cfg = (config.get("integrations") or {}).get(name) or {}
        merged[name].update(user_cfg if isinstance(user_cfg, dict) else {})
    for name, cfg in (config.get("integrations") or {}).items():
        if name not in merged:
            merged[name] = cfg if isinstance(cfg, dict) else {"enabled": bool(cfg)}
    return merged


def is_integration_active(config, name):
    """True when an optional integration is explicitly enabled in fabric.yaml."""
    integ = get_integrations(config)
    return bool((integ.get(name) or {}).get("enabled", False))


def _find_config_file():
    """Find fabric.yaml in fabric root or home directory."""
    candidates = [
        FABRIC_ROOT / _CORPUS_SUBDIR / CONFIG_FILENAME,
        FABRIC_ROOT / CONFIG_FILENAME,
        Path.home() / ".wiki-fabric" / CONFIG_FILENAME,
        Path.home() / CONFIG_FILENAME,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


_CONFIG_CACHE = None  # (fingerprint, config)


def _config_fingerprint():
    """Cheap identity of the config inputs: file mtime+size and the env vars
    that get_config() folds in. Invalidates the per-process cache when either
    changes (tests flip env vars; nothing else mutates mid-run)."""
    import hashlib
    config_file = _find_config_file()
    stat = config_file.stat() if (config_file and config_file.exists()) else None
    file_sig = f"{stat.st_mtime_ns}:{stat.st_size}" if stat else "none"
    env_sig = "|".join(f"{k}={os.environ.get(k, '')}" for k in (
        "WIKI_LLM_BASE_URL", "WIKI_LLM_API_KEY", "WIKI_LLM_MODEL",
        "WIKI_LLM_COMPILER_MODEL", "WIKI_LLM_LOCAL_MODEL"))
    return hashlib.sha1(f"{file_sig}|{env_sig}".encode()).hexdigest()


def _merge_user_config(base, user_config):
    """Merge a user config into a (already deep-copied) defaults dict.
    Top-level keys: owner/llm/repos/domains/ignore/integrations/corpus.
    Dicts merge shallowly at the top level; scalars/lists replace.
    Does NOT mutate `base`."""
    for key in ("owner", "llm", "repos", "domains", "ignore", "integrations", "corpus"):
        if key in user_config and user_config[key] is not None:
            if isinstance(base.get(key), dict) and isinstance(user_config[key], dict):
                base[key].update(user_config[key])
            else:
                base[key] = user_config[key]
    return base


def get_config():
    """Load fabric.yaml, merged with defaults. Returns dict.

    Memoized per process, keyed on the config file's mtime/size + the LLM env
    overrides — batch runs (ingest workers, mine-promotions) parse the YAML
    once instead of on every call. Call get_config.invalidate() (or flip an
    env var) when you need a guaranteed re-read."""
    global _CONFIG_CACHE
    fp = _config_fingerprint()
    if _CONFIG_CACHE is not None and _CONFIG_CACHE[0] == fp:
        return _CONFIG_CACHE[1]

    config_file = _find_config_file()

    # Deep copy: _DEFAULTS contains nested dicts (llm/integrations/domains) and
    # the merge below .update()s them — a shallow copy leaked user config into
    # _DEFAULTS for the life of the process (visible once results are cached).
    import copy
    config = copy.deepcopy(_DEFAULTS)

    if config_file and HAVE_YAML:
        try:
            user_config = yaml.safe_load(config_file.read_text()) or {}
            config = _merge_user_config(config, user_config)
        except Exception:
            pass

    # Env var overrides for LLM
    config["llm"]["base_url"] = os.environ.get("WIKI_LLM_BASE_URL", config["llm"]["base_url"])
    config["llm"]["api_key"] = os.environ.get("WIKI_LLM_API_KEY", config["llm"]["api_key"])
    config["llm"]["model"] = os.environ.get("WIKI_LLM_MODEL", config["llm"]["model"])
    config["llm"]["compiler_model"] = os.environ.get(
        "WIKI_LLM_COMPILER_MODEL", config["llm"].get("compiler_model") or config["llm"]["model"])
    config["llm"]["local_model"] = os.environ.get(
        "WIKI_LLM_LOCAL_MODEL", config["llm"].get("local_model") or None)

    _CONFIG_CACHE = (fp, config)
    return config


def get_config_clear_cache():
    """Force the next get_config() to re-read from disk (tests, long-running
    processes that must observe fabric.yaml edits)."""
    global _CONFIG_CACHE
    _CONFIG_CACHE = None


def resolve_repo_path(config, repo_name):
    """Resolve a repo path from fabric.yaml config (relative to fabric root or absolute)."""
    repo_cfg = get_repo_config(config, repo_name)
    path_str = repo_cfg.get("path", "")
    if not path_str:
        return None
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (FABRIC_ROOT / p).resolve()


def get_all_repo_names(config):
    """Return list of configured repo names (explicit + discovered)."""
    merged = get_discovered_repos(config)
    names = list(config.get("repos", {}).keys())
    for slug in merged:
        if slug not in names:
            names.append(slug)
    return names


# === Overlay-as-config + sibling discovery ================================
# Per-project config lives in the project's .wiki-overlay.md (written by
# bootstrap, versioned with the project repo). fabric.yaml keeps fabric-global
# settings; repos entries are only needed for exceptions. Discovery scans the
# fabric's sibling directories for overlays and merges their `routing:` block.

_OVERLAY_CACHE = None  # (fingerprint, {slug: overlay_dict})


def _overlay_fingerprint():
    """Cheap identity of the discovery inputs: fabric parent dir + overlay mtimes."""
    import hashlib
    parent = FABRIC_ROOT.parent
    sig = [str(parent)]
    try:
        for overlay in sorted(parent.glob("*/.wiki-overlay.md")):
            st = overlay.stat()
            sig.append(f"{overlay}:{st.st_mtime_ns}")
    except OSError:
        pass
    return hashlib.sha1("|".join(sig).encode()).hexdigest()


def get_discovered_repos(config):
    """Scan fabric siblings for project overlays. Returns {slug: repo_cfg} for
    every sibling with a .wiki-overlay.md. Cached per-process on mtimes;
    respects repos.auto_discover: false. Explicit repos entries always win on
    key conflicts (see get_repo_config)."""
    global _OVERLAY_CACHE
    repos_cfg = config.get("repos") or {}
    if repos_cfg.get("auto_discover") is False:
        return {}
    fp = _overlay_fingerprint()
    if _OVERLAY_CACHE is not None and _OVERLAY_CACHE[0] == fp:
        return _OVERLAY_CACHE[1]

    found = {}
    parent = FABRIC_ROOT.parent
    try:
        overlays = sorted(parent.glob("*/.wiki-overlay.md"))
    except OSError:
        overlays = []
    for overlay in overlays:
        try:
            text = overlay.read_text(encoding="utf-8", errors="replace")
            if not HAVE_YAML:
                continue
            m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
            if not m:
                continue
            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            continue
        slug = str(fm.get("namespace") or "").strip()
        if not slug or slug in found:
            continue  # sibling name collision: first found wins; lint flags ambiguity
        found[slug] = {
            "path": str(overlay.parent),
            "discovered": True,
            "routing": fm.get("routing") or {},
            "overlay_path": str(overlay),
        }
    _OVERLAY_CACHE = (fp, found)
    return found


def get_repo_config(config, repo_name):
    """Effective per-repo config: explicit fabric.yaml entry merged over the
    discovered overlay (explicit wins on every key; routing from the overlay
    applies unless the fabric.yaml entry sets the same key). Returns {} for
    unknown repos."""
    repos_cfg = config.get("repos") or {}
    explicit = repos_cfg.get(repo_name) or {}
    discovered = get_discovered_repos(config).get(repo_name) or {}
    if not explicit and not discovered:
        return {}
    merged = dict(discovered)
    overlay_routing = dict(discovered.get("routing") or {})
    for k, v in explicit.items():
        merged[k] = v
        if isinstance(v, dict) and k == "routing":
            overlay_routing = {**overlay_routing, **v}  # explicit routing keys win
    # promote overlay routing to the standard keys consumers read, without
    # clobbering explicit fabric.yaml stage keys
    for k, v in overlay_routing.items():
        merged.setdefault(k, v)
    merged.setdefault("routing", overlay_routing)
    return merged


def get_domain_signals(config):
    """Return {domain_name: [signal, ...]} from config."""
    result = {}
    for domain, cfg in config.get("domains", {}).items():
        if isinstance(cfg, dict):
            result[domain] = cfg.get("signals", [])
        elif isinstance(cfg, list):
            result[domain] = cfg
    return result


def get_owner(config):
    """Return the configured owner name."""
    return config.get("owner", "you")




def get_local_model(config=None):
    """Resolve the local-model default: llm.local_model from fabric.yaml, then
    WIKI_LLM_LOCAL_MODEL (env), then the platform default — MLX on Apple
    Silicon, GGUF elsewhere. Returns a HuggingFace model id."""
    if config is None:
        config = get_config()
    explicit = (config.get("llm", {}) or {}).get("local_model")
    if explicit and str(explicit).strip():
        return str(explicit).strip()
    env = os.environ.get("WIKI_LLM_LOCAL_MODEL")
    if env and env.strip():
        return env.strip()
    return DEFAULT_LOCAL_MODELS.get(sys.platform, DEFAULT_LOCAL_MODELS["default"])


def get_stage_route(config, repo_name=None, stage="extract"):
    """Resolve the LLM model for a workflow stage in a repo.

    Routing keys (per-repo override in repos.<slug>.<stage>):
        extract:    summarize + claim extraction (sees raw docs - highest sensitivity)
        synthesize: concept synthesis from claims (sees sanitized statements)
        dossier:    promotion dossier generation (sees experience events)

    Resolution order:
        1. repos.<repo>.<stage>          (per-repo override: "local" | "cloud" | model name)
        2. repos.<repo>.extract           (fallback for any unconfigured stage)
        3. llm.compiler_model            (cloud default)
    Returns a model string. "local" maps to llm.local_model (see
    get_local_model); "cloud" maps to llm.compiler_model. A local_model set in
    fabric.yaml overrides the WIKI_MLX_MODEL env default for mlx routes.
    """
    cloud = (config.get("llm", {}).get("compiler_model")
             or config.get("llm", {}).get("model") or "deepseek-v4.1-flash:cloud")
    if not repo_name:
        return cloud
    repo_cfg = get_repo_config(config, repo_name)
    route = repo_cfg.get(stage) or repo_cfg.get("extract") or "cloud"
    if route == "local":
        # Cross-platform: MLX on Apple Silicon, GGUF elsewhere (local_llm.py
        # picks the backend from the model-id shape).
        return os.environ.get("WIKI_MLX_MODEL") or get_local_model(config)
    if route == "cloud":
        return cloud
    return route  # explicit model name


def find_local_model_path(model_id):
    """Return a local filesystem path when model_id points at a local dir, or a
    cached HuggingFace snapshot path for an hf id. None when not present locally."""
    p = Path(model_id).expanduser()
    if p.is_dir():
        return p
    if "/" not in model_id or model_id.startswith("http"):
        return None
    hf_home = os.environ.get("HF_HOME") or str(Path.home() / ".cache" / "huggingface")
    hub_dir = Path(os.environ.get("HF_HUB_CACHE") or (Path(hf_home) / "hub"))
    repo_dir = hub_dir / ("models--" + model_id.replace("/", "--"))
    if not repo_dir.is_dir():
        return None
    snapshots = repo_dir / "snapshots"
    if snapshots.is_dir():
        for snap in sorted(snapshots.iterdir()):
            if ((snap / "config.json").exists() or (snap / "tokenizer_config.json").exists()
                    or any(snap.glob("*.gguf"))):
                return snap
    return None


# Quantization preference when a GGUF repo ships multiple splits. Regexes
# matched (case-insensitive) against root-level filenames, in order.
GGUF_QUANT_PREFERENCE = [r"q4_k_m", r"q4_k_s", r"pq2_0", r"q4[^_]*_", r"q4", r"ptq1_0"]


def gguf_preferred_file(model_id):
    """Preferred root-level .gguf filename in a HF repo (None when unlistable)."""
    import re
    try:
        from huggingface_hub import HfApi
        files = HfApi().list_repo_files(model_id)
        root_ggufs = sorted(f for f in files if f.lower().endswith(".gguf") and "/" not in f)
        for rx in GGUF_QUANT_PREFERENCE:
            hits = [f for f in root_ggufs if re.search(rx, f.lower())]
            if hits:
                return hits[0]
        return root_ggufs[0] if root_ggufs else None
    except Exception:
        return None


_ENSURE_LOCK = None


def _ensure_lock():
    """Process-wide lock so concurrent ingest workers don't prompt/download twice."""
    global _ENSURE_LOCK
    if _ENSURE_LOCK is None:
        import threading
        _ENSURE_LOCK = threading.Lock()
    return _ENSURE_LOCK


def ensure_local_model(model_id=None, assume_yes=False, config=None):
    """Check the local model is present (local dir or HF cache); offer to
    download it when missing. Returns (path_or_None, downloaded_bool).

    Human-gated: prompts before any network write unless assume_yes (CI /
    non-tty). Never raises — callers degrade to cloud on (None, False).
    Thread-safe: concurrent workers serialize here.
    """
    model_id = model_id or get_local_model(config)
    if find_local_model_path(model_id) or Path(model_id).exists():
        return model_id, False
    with _ensure_lock():
        # Re-check inside the lock: another worker may have finished while we waited.
        if find_local_model_path(model_id) or Path(model_id).exists():
            return model_id, False

        is_tty = False
        try:
            is_tty = sys.stdin.isatty() and sys.stdout.isatty()
        except Exception:
            pass
        if not (assume_yes or is_tty):
            print(f"local model '{model_id}' not found locally; "
                  f"download with: wf models ensure (or --yes)", file=sys.stderr)
            return None, False

        size_hint = "~2-4 GB" if "4bit" in model_id or "GGUF" in model_id else "multi-GB"
        if not assume_yes:
            try:
                answer = input(f"Local model '{model_id}' not found — download from "
                               f"HuggingFace ({size_hint})? [y/N] ")
            except (EOFError, KeyboardInterrupt):
                answer = ""
            if answer.strip().lower() not in ("y", "yes"):
                print("Skipping download — local routes will fall back or fail.", file=sys.stderr)
                return None, False

        print(f"Downloading {model_id} from HuggingFace ({size_hint})...", file=sys.stderr)
        try:
            from huggingface_hub import snapshot_download, hf_hub_download
            if "gguf" in model_id.lower():
                # GGUF repos ship many quantization splits; fetch only the
                # preferred one (root-level, Q4_K_M first) — a blanket
                # snapshot_download("*.gguf") would pull every split.
                filename = gguf_preferred_file(model_id)
                if filename:
                    hf_hub_download(model_id, filename)
                    print(f"Downloaded: {model_id} ({filename})", file=sys.stderr)
                    return model_id, True
            snapshot_download(model_id)
            print(f"Downloaded: {model_id}", file=sys.stderr)
            return model_id, True
        except Exception as e:
            print(f"download failed: {e}\n"
                  f"Install huggingface_hub (pip install huggingface_hub) or download manually.",
                  file=sys.stderr)
            return None, False


def is_local_route(config, repo_name=None, stage="extract"):
    """True when the stage's route resolves to an on-device model (MLX/GGUF)."""
    model = get_stage_route(config, repo_name, stage)
    return looks_like_local_model(model)


# Known OpenAI-compatible provider prefixes whose "/"-namespaced ids are NOT
# on-device HF repos (e.g. openai/gpt-4o on OpenRouter).
_PROVIDER_PREFIXES = {
    "openai", "anthropic", "google", "mistralai", "meta-llama", "microsoft",
    "deepseek", "qwen", "openrouter", "together", "cohere", "x-ai", "amazon",
    "azure", "perplexity", "groq", "fireworks", "deepseek-ai", "moonshot",
    "baichuan", "zai", "liquid", "nousresearch", "sao10k", "undi95",
}


def looks_like_local_model(model_id):
    """Heuristic: True when a model string should run on-device.
    Matches the local backend's own shapes: local paths, .gguf ids, mlx ids,
    and '<org>/<repo>' HF ids that are not a known cloud-provider namespace."""
    m = str(model_id or "")
    if not m or m.startswith("http"):
        return False
    if Path(m).expanduser().is_dir() or m.lower().endswith(".gguf"):
        return True
    if "mlx" in m.lower() or "gguf" in m.lower():
        return True
    if "/" not in m:
        return False
    first = m.split("/", 1)[0].lower()
    if first in _PROVIDER_PREFIXES:
        return False
    # HF org ids: second segment must look like a repo name (no ':' port),
    # and the whole id must not be a host:port/base-url string.
    if ":" in m.split("/", 1)[1]:
        return False
    return True


def actor(config, kind="agent", model=None):
    """OKF v0.2 §7 actor convention string.

    kind="agent"   -> agent/<script-name>/<model>   (fabric scripts run by an LLM)
    kind="process" -> process/<id>                  (hooks, cron, CI — deterministic)
    kind="human"   -> human:<id>                    (owner from fabric.yaml)
    Model omitted from process actors: they are deterministic, model-independent.
    """
    owner = get_owner(config) or "unknown"
    if kind == "human":
        return f"human:{owner}"
    if kind == "process":
        return f"process:{model or 'script'}"
    # agent kind: model = llm model in use (ops or compiler)
    m = model or (config.get("llm", {}).get("compiler_model")
                  or config.get("llm", {}).get("model") or "unknown")
    return f"agent/{owner}/{m}"

def get_llm_config(config, compiler=False):
    """Return LLM configuration dict. compiler=True returns the compiler model
    (falls back to llm.model when unset) — claim extraction, synthesis, and
    promotion mining must run on the policy-designated compiler model."""
    llm = dict(config.get("llm", {}))
    if compiler:
        cm = llm.get("compiler_model")
        if cm and cm.strip():
            llm["model"] = cm
    return llm


# Characters that signal a regex rather than a glob. Globs legitimately
# contain * ? [ ] — anything beyond that (backslash classes, anchors, groups)
# reads as regex intent.
_REGEX_HINT_CHARS = set("\\(){}+|^$<>")
_REGEX_HINT_EXPLICIT = ("regex:", "re:")


def _classify_ignore_pattern(pattern):
    """Auto-classify an ignore pattern as "glob" or "regex".

    Explicit prefix wins: a pattern starting with `regex:` or `re:` is always
    a regex (strips the prefix) — the escape hatch for ambiguous strings like
    a literal filename containing `*`. Everything else is a regex when it
    contains a regex-only metacharacter (\\ ( ) { } + | ^), else a glob.
    """
    p = str(pattern)
    low = p.lower()
    for prefix in _REGEX_HINT_EXPLICIT:
        if low.startswith(prefix):
            return "regex", p[len(prefix):].strip()
    if any(c in p for c in _REGEX_HINT_CHARS):
        return "regex", p
    return "glob", p


def get_ignores(config, repo_name=None):
    """Return merged ignore patterns from fabric.yaml.

    Schema:
        ignore:
          patterns: ["vendor/**", "regex:_archive\\d+/"]   # auto-classified
          globs:   ["vendor/**", "docs/generated/**"]       # explicit fnmatch w/ ** support
          regexes: ["_archive\\d+/"]                        # explicit re.search on posix path
          projects:                                          # per-repo overrides (merged)
            <slug>:
              patterns: [...]
              globs: [...]
              regexes: [...]

    `patterns` is the unified list — every entry is auto-classified: globs
    (fnmatch-style, ** crosses dirs) are the default; a pattern containing a
    regex-only metacharacter (\\ ( ) { } + | ^) is compiled as a regex; prefix
    any entry with `regex:` to force regex matching. The separate globs/regexes
    keys keep working (and take precedence for ambiguous strings).

    Returns {"globs": [...], "regexes": [...], "compiled": [...re.Pattern...]}.
    Global patterns apply to all repos; per-repo patterns union with global.
    """
    raw = config.get("ignore") or {}
    globs = list(raw.get("globs") or [])
    regexes = list(raw.get("regexes") or [])
    for pat in raw.get("patterns") or []:
        kind, value = _classify_ignore_pattern(pat)
        (globs if kind == "glob" else regexes).append(value)
    if repo_name:
        per = (raw.get("projects") or {}).get(repo_name) or {}
        globs.extend(per.get("globs") or [])
        regexes.extend(per.get("regexes") or [])
        for pat in per.get("patterns") or []:
            kind, value = _classify_ignore_pattern(pat)
            (globs if kind == "glob" else regexes).append(value)
    compiled = []
    for r in regexes:
        try:
            compiled.append(re.compile(r))
        except re.error:
            pass  # invalid regex: skipped silently here; lint's config check reports it
    return {"globs": globs, "regexes": regexes, "compiled": compiled}


def is_ignored(rel_posix, ignores):
    """Shared ignore predicate. globs are fnmatch-style with ** support:
    '**' crosses directory separators (we translate to a regex)."""
    import fnmatch as _fn
    if not rel_posix:
        return False
    posix = rel_posix.replace("\\", "/")
    for g in ignores.get("globs", []):
        g_norm = g.replace("\\", "/").lstrip("/").rstrip("/")
        if "**" in g_norm:
            # dir/** pattern: prefix + anything under it (incl. the dir itself)
            if g_norm.endswith("/**"):
                base = re.escape(g_norm[:-3])
                if re.match(base + "(?:/.*)?$", posix):
                    return True
            else:
                # a/**/b: a/(anything/)*b
                pre, post = g_norm.split("**", 1)
                pat = re.escape(pre) + "(?:[^/]+/)*" + re.escape(post.lstrip("/"))
                if re.fullmatch(pat, posix):
                    return True
        else:
            # single-level glob: fnmatch on full posix path or basename
            if _fn.fnmatch(posix, g_norm) or _fn.fnmatch(posix.rsplit("/", 1)[-1], g_norm):
                return True
    for c in ignores.get("compiled", []):
        if c.search(posix):
            return True
    return False


def compiler_eval_recorded(config, log_path=None):
    """True when registry/log.md contains a PASS compiler eval for the current
    compiler model (eval-stability G4 / eval.py). Promotion mining + promotion
    refuse without it — the model-sensitivity finding made model swaps compiler
    changes; this enforces the regression-guard rule."""
    import re
    llm = get_llm_config(config, compiler=True)
    compiler_model = llm.get("model", "")
    log_path = Path(log_path or (FABRIC_ROOT / "registry" / "log.md"))
    if not log_path.exists():
        return False, "no registry/log.md — run eval-stability/eval.py for the compiler model first"
    text = log_path.read_text()
    # accept: any eval-stability/eval entry naming the compiler model.
    # Log headings are OKF §9 shape (## YYYY-MM-DD with '* **eval | ...**' body);
    # accept both the legacy '## [date] op | subject' and the current form.
    short = compiler_model.split(":")[0]
    block_re = re.compile(r"(?:## \[[\d-]+\] (?:eval-stability|eval) \||## \d{4}-\d{2}-\d{2}.*?eval).*?(?=\n## |\Z)", re.DOTALL)
    for m in block_re.finditer(text):
        block = m.group(0)
        if compiler_model in block or short in block:
            return True, f"compiler eval recorded for {compiler_model}"
    return False, (f"no compiler eval recorded for '{compiler_model}' — run: "
                   f"python3 scripts/eval-stability.py --models {compiler_model} --record")


def get_repo_graph_dir(config, repo_name):
    """Get the graphify graph directory for a repo. Priority: explicit repo
    graph_dir > overlay routing.graph_dir > integrations.graphify.graph_dir
    > 'graphify-out'."""
    repo_cfg = get_repo_config(config, repo_name)
    default = get_integrations(config).get("graphify", {}).get("graph_dir", "graphify-out")
    return repo_cfg.get("graph_dir") or (repo_cfg.get("routing") or {}).get("graph_dir") or default