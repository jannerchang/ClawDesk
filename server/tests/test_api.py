from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import get_conn
from app.main import app


def test_health_and_crud_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWDESK_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("CLAWDESK_HERMES_MODE", "stub")
    monkeypatch.setenv("CLAWDESK_LOCAL_AGENT_MODE", "stub")
    monkeypatch.setenv("CLAWDESK_LOCAL_AGENT_WORKSPACE_ROOT", str(tmp_path))
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["ok"] is True
        assert "hermes_mode" in health

        spaces = client.get("/spaces").json()
        assert len(spaces) >= 6
        inbox = next(space for space in spaces if space["type"] == "inbox")
        tech = next(space for space in spaces if space["type"] == "tech")
        inbox_channels = client.get(f"/spaces/{inbox['id']}/channels").json()
        tech_channels = client.get(f"/spaces/{tech['id']}/channels").json()
        assert any(channel["name"] == "随手聊" for channel in inbox_channels)
        assert any(channel["name"] == "技术聊天" for channel in tech_channels)
        local_work = next(channel for channel in tech_channels if channel["name"] == "Local Work")
        local_bindings = client.get(f"/channels/{local_work['id']}/bot-bindings").json()
        local_agent_binding = next(binding for binding in local_bindings if binding["user_name"] == "LocalAgent")
        assert local_agent_binding["bot_kind"] == "local-agent"
        assert local_agent_binding["listen_mode"] == "channel"
        assert local_agent_binding["session_key"].startswith("local-agent:")
        space_id = spaces[0]["id"]

        channel = client.post(
            "/channels",
            json={"space_id": space_id, "name": "技术聊天", "type": "tech", "mode": "mixed"},
        ).json()
        channel_id = channel["id"]
        assert channel["name"] == "技术聊天"

        message = client.post(f"/channels/{channel_id}/messages", json={"content": "第一条测试消息"}).json()
        assert message["content"] == "第一条测试消息"

        upload = client.post(
            f"/messages/{message['id']}/attachments",
            files={"file": ("hello.txt", b"hello attachment", "text/plain")},
        ).json()
        assert upload["message_id"] == message["id"]
        assert upload["kind"] == "file"
        assert upload["original_name"] == "hello.txt"
        assert upload["size"] == len(b"hello attachment")

        attachments = client.get(f"/messages/{message['id']}/attachments").json()
        assert [item["id"] for item in attachments] == [upload["id"]]

        messages = client.get(f"/channels/{channel_id}/messages").json()
        assert [item["id"] for item in messages] == [message["id"]]

        members = client.get(f"/channels/{channel_id}/members").json()
        assert [member["name"] for member in members] == ["Janner", "Hermes", "LocalAgent"]
        assert members[0]["kind"] == "human"
        assert members[1]["kind"] == "bot"
        assert members[2]["kind"] == "bot"

        bindings = client.get(f"/channels/{channel_id}/bot-bindings").json()
        assert {binding["user_name"] for binding in bindings} == {"Hermes", "LocalAgent"}
        hermes_binding = next(binding for binding in bindings if binding["user_name"] == "Hermes")
        assert hermes_binding["listen_mode"] == "mention"
        updated_binding = client.patch(
            f"/channels/{channel_id}/bot-bindings/{hermes_binding['id']}",
            json={"listen_mode": "channel", "session_key": "hermes:test-session", "config": {"profile": "default"}},
        ).json()
        assert updated_binding["listen_mode"] == "channel"
        assert updated_binding["session_key"] == "hermes:test-session"
        assert updated_binding["config"] == {"profile": "default"}

        subchannel = client.post(
            f"/channels/{channel_id}/subchannels/from_messages",
            json={"name": "Apple 全平台工作台", "type": "tech", "source_message_ids": [message["id"]]},
        ).json()
        assert subchannel["parent_channel_id"] == channel_id
        assert subchannel["source_message_ids"] == [message["id"]]

        sub_members = client.get(f"/channels/{subchannel['id']}/members").json()
        assert [member["name"] for member in sub_members] == ["Janner", "Hermes", "LocalAgent"]

        copied = client.get(f"/channels/{subchannel['id']}/messages").json()
        assert len(copied) == 1
        assert copied[0]["source_message_id"] == message["id"]

        original_messages = client.get(f"/channels/{channel_id}/messages").json()
        assert any(item["sender_type"] == "system" and "已从" in item["content"] for item in original_messages)

        hermes = client.post(f"/channels/{channel_id}/agent/hermes", json={"prompt": "请简短回复"}).json()
        assert hermes["agent_run"]["status"] == "stubbed"
        assert hermes["agent_run"]["output_text"].startswith("[Hermes stub]")
        assert hermes["message"]["sender_type"] == "hermes"
        assert hermes["message"]["sender_name"] == "Hermes"
        assert hermes["message"]["content"].startswith("[Hermes stub]")

        local = client.post(
            f"/channels/{channel_id}/agent/local",
            json={"prompt": "printf local-ok", "agent": "shell", "workspace": str(tmp_path)},
        ).json()
        assert local["agent_run"]["status"] == "stubbed"
        assert local["agent_run"]["agent"] == "local-agent"
        assert local["agent_run"]["model"] == "shell"
        assert local["message"]["sender_type"] == "local-agent"
        assert local["message"]["sender_name"] == "LocalAgent"
        assert local["message"]["content"].startswith("[LocalAgent stub]")
        assert local["command"] == ["/bin/bash", "-lc", "printf local-ok"]
        assert local["workspace"] == str(tmp_path)

        with get_conn() as conn:
            run_count = conn.execute("SELECT COUNT(*) AS c FROM agent_runs WHERE id = ?", (hermes["agent_run"]["id"],)).fetchone()["c"]
            assert run_count == 1
