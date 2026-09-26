"""Gate notification seam (#67): webhook adapter, opt-in, never fails the gate.

Uses a raw socket responder (no http.server threads) to keep the test
single-threaded and hang-proof.

Run: python3 -m pytest tests/test_gate_notify.py -v
"""
import importlib.util
import json
import socket
import sys
import threading
from pathlib import Path

REPO = Path(__file__).parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load("gate", REPO / "scripts" / "cmd" / "gate.py")
import shutil
import tempfile
import os
from unittest import mock

received = []


def _serve_once(srv):
    conn, _ = srv.accept()
    data = conn.recv(65536).decode("utf-8", errors="replace")
    body = data.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in data else ""
    received.append(json.loads(body))
    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
    conn.close()
    srv.close()


class TestNotify:
    def _setup(self, tmp, notify_cfg=True):
        (tmp / "corpus" / "registry" / "promotions").mkdir(parents=True)
        (tmp / "corpus" / "fabric.yaml").write_text(
            "owner: t\n" + ("notify:\n  - kind: webhook\n    url_env: WF_GATE_WEBHOOK_URL\n"
                            if notify_cfg else "owner: t\n"))
        (tmp / "corpus" / "registry" / "promotions" / "promotion-test.md").write_text(
            "---\ntype: promotion-dossier\nstatus: pending-review\n---\n\nx\n")

    def test_webhook_receives_manifest(self, tmp_path):
        srv = socket.socket()
        srv.settimeout(30)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        threading.Thread(target=_serve_once, args=(srv,), daemon=True).start()
        self._setup(tmp_path)
        import fabric_config as _fc
        # fabric_config resolves FABRIC_ROOT/CORPUS_ROOT at import time (the
        # first test's env wins in-suite). Patch the resolved constants to
        # this test's fabric alongside the env.
        with mock.patch.dict(os.environ, {"WIKI_FABRIC_DIR": str(tmp_path),
                                          "WF_GATE_WEBHOOK_URL": f"http://127.0.0.1:{srv.getsockname()[1]}/gate"}), \
             mock.patch.object(_fc, "FABRIC_ROOT", tmp_path), \
             mock.patch.object(_fc, "CORPUS_ROOT", tmp_path / "corpus"):
            sections, actionable = gate.gate()
            mp = tmp_path / "corpus" / "registry" / "pending-gate.md"
            gate._write_manifest(mp, sections, actionable)
            gate._notify(mp, sections)
        import time as _time
        for _ in range(50):
            if received:
                break
            _time.sleep(0.1)
        assert len(received) == 1
        assert received[0]["kind"] == "wiki-fabric-gate"
        assert "manifest" in received[0]

    def test_no_url_env_silently_skips(self, tmp_path):
        self._setup(tmp_path, notify_cfg=False)
        with mock.patch.dict(os.environ, {"WIKI_FABRIC_DIR": str(tmp_path)}):
            os.environ.pop("WF_GATE_WEBHOOK_URL", None)
            sections, actionable = gate.gate()
            mp = tmp_path / "corpus" / "registry" / "pending-gate.md"
            gate._notify(mp, sections)  # no config → no adapter → no send, no crash

    def test_webhook_failure_never_fails_gate(self, tmp_path):
        srv = socket.socket()
        srv.settimeout(5)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        self._setup(tmp_path)
        with mock.patch.dict(os.environ, {"WIKI_FABRIC_DIR": str(tmp_path),
                                          "WF_GATE_WEBHOOK_URL": f"http://127.0.0.1:{srv.getsockname()[1]}/gone"}):
            sections, actionable = gate.gate()
            mp = tmp_path / "corpus" / "registry" / "pending-gate.md"
            gate._notify(mp, sections)  # unreachable — must not raise
