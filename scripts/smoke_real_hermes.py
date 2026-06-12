#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

BASE_URL = "http://127.0.0.1:8001"
ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"


def request(method: str, path: str, payload: dict[str, Any] | None = None, timeout: int = 60) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"content-type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode()
        return json.loads(body) if body else None


def wait_ready(proc: subprocess.Popen[str]) -> None:
    deadline = time.time() + 20
    last_error = ""
    while time.time() < deadline:
        if proc.poll() is not None:
            output = proc.communicate(timeout=1)[0] or ""
            raise RuntimeError(f"server exited early with code {proc.returncode}\n{output}")
        try:
            if request("GET", "/health", timeout=10).get("ok") is True:
                return
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = str(exc)
        time.sleep(0.3)
    raise RuntimeError(f"server did not become ready: {last_error}")


def main() -> int:
    db_path = SERVER / ".data" / "smoke-real-hermes.db"
    if db_path.exists():
        db_path.unlink()

    env = dict(
        os.environ,
        CLAWDESK_DB_PATH=str(db_path),
        CLAWDESK_HERMES_MODE="cli",
        CLAWDESK_HERMES_TIMEOUT_SECONDS="180",
        CLAWDESK_HERMES_FALLBACK_TO_STUB="0",
    )
    proc = subprocess.Popen(
        ["uv", "run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
        cwd=SERVER,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_ready(proc)
        health = request("GET", "/health")
        assert health["ok"] is True, health
        assert health["hermes_mode"] == "cli", health

        spaces = cast(list[dict[str, Any]], request("GET", "/spaces"))
        inbox = next(space for space in spaces if space["type"] == "inbox")
        channel = cast(dict[str, Any], request(
            "POST",
            "/channels",
            {"space_id": inbox["id"], "name": "Smoke Real Hermes", "type": "tech", "mode": "mixed"},
        ))
        user_message = cast(dict[str, Any], request(
            "POST",
            f"/channels/{channel['id']}/messages",
            {"content": "请只回复 CLAWDESK_REAL_HERMES_OK，不要添加其他内容"},
        ))
        assert user_message["sender_type"] == "user", user_message

        hermes = cast(dict[str, Any], request("POST", f"/channels/{channel['id']}/agent/hermes", {}, timeout=180))
        run = cast(dict[str, Any], hermes["agent_run"])
        hermes_message = cast(dict[str, Any], hermes["message"])
        assert run["status"] == "succeeded", run
        assert hermes_message["sender_type"] == "hermes", hermes
        assert "CLAWDESK_REAL_HERMES_OK" in hermes_message["content"], hermes_message
        assert "session_id:" not in hermes_message["content"], hermes_message

        print("REAL_HERMES_SMOKE_OK", json.dumps({"channel": channel["name"], "status": run["status"], "reply": hermes_message["content"][:80]}, ensure_ascii=False))
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
