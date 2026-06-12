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


def upload_file(path: str, filename: str, content: bytes, content_type: str) -> Any:
    boundary = "----ClawDeskSmokeBoundary"
    body = b"\r\n".join(
        [
            f"--{boundary}".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode(),
            f"Content-Type: {content_type}".encode(),
            b"",
            content,
            f"--{boundary}--".encode(),
            b"",
        ]
    )
    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers={"content-type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def wait_ready(proc: subprocess.Popen[str]) -> None:
    deadline = time.time() + 20
    last_error = ""
    while time.time() < deadline:
        if proc.poll() is not None:
            output = proc.communicate(timeout=1)[0] or ""
            raise RuntimeError(f"server exited early with code {proc.returncode}\n{output}")
        try:
            if request("GET", "/health").get("ok") is True:
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
        env=dict(env, CLAWDESK_HERMES_MODE="stub"),
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
        members = cast(list[dict[str, Any]], request("GET", f"/channels/{channel['id']}/members"))
        assert [member["name"] for member in members] == ["Janner", "Hermes"], members
        message = cast(dict[str, Any], request("POST", f"/channels/{channel['id']}/messages", {"content": "第一条 smoke 消息"}))
        attachment = cast(dict[str, Any], upload_file(
            f"/messages/{message['id']}/attachments",
            "smoke.txt",
            b"smoke attachment",
            "text/plain",
        ))
        assert attachment["message_id"] == message["id"], attachment
        assert attachment["original_name"] == "smoke.txt", attachment
        hermes = cast(dict[str, Any], request("POST", f"/channels/{channel['id']}/agent/hermes", {}))
        hermes_message = cast(dict[str, Any], hermes["message"])
        assert hermes_message["sender_type"] == "hermes", hermes
        assert hermes_message["content"].startswith("[Hermes stub]"), hermes
        subchannel = cast(dict[str, Any], request(
            "POST",
            f"/channels/{channel['id']}/subchannels/from_messages",
            {"name": "Smoke 子频道", "type": "tech", "source_message_ids": [message["id"]]},
        ))
        copied = cast(list[dict[str, Any]], request("GET", f"/channels/{subchannel['id']}/messages"))
        assert copied[0]["source_message_id"] == message["id"], copied
        print("SMOKE_OK", json.dumps({"space": inbox["name"], "channel": channel["name"], "members": [member["name"] for member in members], "subchannel": subchannel["name"], "hermes": hermes_message["sender_type"], "attachment": attachment["original_name"]}, ensure_ascii=False))
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
