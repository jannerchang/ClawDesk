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

BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"


def request(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers={"content-type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode()
        return json.loads(body) if body else None


def wait_ready(proc: subprocess.Popen[str]) -> None:
    deadline = time.time() + 20
    last_error = ""
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited early with code {proc.returncode}")
        try:
            if request("GET", "/health") == {"ok": True}:
                return
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = str(exc)
        time.sleep(0.3)
    raise RuntimeError(f"server did not become ready: {last_error}")


def main() -> int:
    db_path = SERVER / ".data" / "smoke.db"
    if db_path.exists():
        db_path.unlink()

    env = dict(os.environ, CLAWDESK_DB_PATH=str(db_path))
    proc = subprocess.Popen(
        ["uv", "run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=SERVER,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_ready(proc)
        spaces = cast(list[dict[str, Any]], request("GET", "/spaces"))
        assert len(spaces) >= 6, spaces
        inbox = next(space for space in spaces if space["type"] == "inbox")
        inbox_channels = cast(list[dict[str, Any]], request("GET", f"/spaces/{inbox['id']}/channels"))
        assert any(channel["name"] == "随手聊" for channel in inbox_channels), inbox_channels

        channel = cast(dict[str, Any], request(
            "POST",
            "/channels",
            {"space_id": inbox["id"], "name": "Smoke 技术聊天", "type": "tech", "mode": "mixed"},
        ))
        message = cast(dict[str, Any], request("POST", f"/channels/{channel['id']}/messages", {"content": "第一条 smoke 消息"}))
        subchannel = cast(dict[str, Any], request(
            "POST",
            f"/channels/{channel['id']}/subchannels/from_messages",
            {"name": "Smoke 子频道", "type": "tech", "source_message_ids": [message["id"]]},
        ))
        copied = cast(list[dict[str, Any]], request("GET", f"/channels/{subchannel['id']}/messages"))
        assert copied[0]["source_message_id"] == message["id"], copied
        print("SMOKE_OK", json.dumps({"space": inbox["name"], "channel": channel["name"], "subchannel": subchannel["name"]}, ensure_ascii=False))
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
