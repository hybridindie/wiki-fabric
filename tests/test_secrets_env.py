"""Machine-local secrets layer: keys live in <fabric>/secrets.env (gitignored);
fabric.yaml stays shareable. Env vars win over the file."""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS / "cmd", _SCRIPTS / "lib", _SCRIPTS):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import fabric_config as FC


def test_secrets_env_loaded_and_env_wins(tmp_path, monkeypatch):
    froot = tmp_path / "fabric"
    froot.mkdir()
    (froot / "fabric.yaml").write_text("owner: t\nllm:\n  api_key: placeholder\n")
    (froot / "corpus").mkdir()
    (froot / "corpus" / "secrets.env").write_text(
        "WIKI_LLM_API_KEY=sk-file\nTYPESAFE_API_KEY=ts-file\n")
    # fabric root resolution must find THIS tmp fabric, not the dev vault
    monkeypatch.setattr(FC, "_find_config_file", lambda: froot / "fabric.yaml")
    for k in ("WIKI_LLM_API_KEY", "TYPESAFE_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    FC._SECRETS_LOADED = False
    FC._CONFIG_CACHE = None
    FC.load_secrets_env(_force=True)
    import os
    assert os.environ["WIKI_LLM_API_KEY"] == "sk-file"
    assert os.environ["TYPESAFE_API_KEY"] == "ts-file"
    cfg = FC.get_config()
    # llm.api_key resolves through the WIKI_LLM_API_KEY env override (set above)
    assert cfg["llm"]["api_key"] == "sk-file"
    # real env beats the file
    monkeypatch.setenv("WIKI_LLM_API_KEY", "sk-env")
    assert FC.get_config()["llm"]["api_key"] == "sk-env"


def test_idempotent_and_missing_ok(tmp_path, monkeypatch):
    froot = tmp_path / "fabric"
    froot.mkdir()
    (froot / "fabric.yaml").write_text("owner: t\n")
    monkeypatch.setattr(FC, "_find_config_file", lambda: froot / "fabric.yaml")
    FC._SECRETS_LOADED = False
    FC._CONFIG_CACHE = None
    FC.load_secrets_env()            # no file → no crash
    FC.load_secrets_env()            # idempotent
    FC.load_secrets_env(_force=True) # explicit re-read
