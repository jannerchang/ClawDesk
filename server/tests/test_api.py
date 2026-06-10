from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_and_crud_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWDESK_DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as client:
        assert client.get("/health").json() == {"ok": True}

        spaces = client.get("/spaces").json()
        assert len(spaces) >= 6
        inbox = next(space for space in spaces if space["type"] == "inbox")
        tech = next(space for space in spaces if space["type"] == "tech")
        inbox_channels = client.get(f"/spaces/{inbox['id']}/channels").json()
        tech_channels = client.get(f"/spaces/{tech['id']}/channels").json()
        assert any(channel["name"] == "随手聊" for channel in inbox_channels)
        assert any(channel["name"] == "技术聊天" for channel in tech_channels)
        space_id = spaces[0]["id"]

        channel = client.post(
            "/channels",
            json={"space_id": space_id, "name": "技术聊天", "type": "tech", "mode": "mixed"},
        ).json()
        channel_id = channel["id"]
        assert channel["name"] == "技术聊天"

        message = client.post(f"/channels/{channel_id}/messages", json={"content": "第一条测试消息"}).json()
        assert message["content"] == "第一条测试消息"

        messages = client.get(f"/channels/{channel_id}/messages").json()
        assert [item["id"] for item in messages] == [message["id"]]

        subchannel = client.post(
            f"/channels/{channel_id}/subchannels/from_messages",
            json={"name": "Apple 全平台工作台", "type": "tech", "source_message_ids": [message["id"]]},
        ).json()
        assert subchannel["parent_channel_id"] == channel_id
        assert subchannel["source_message_ids"] == [message["id"]]

        copied = client.get(f"/channels/{subchannel['id']}/messages").json()
        assert len(copied) == 1
        assert copied[0]["source_message_id"] == message["id"]

        original_messages = client.get(f"/channels/{channel_id}/messages").json()
        assert any(item["sender_type"] == "system" and "已从" in item["content"] for item in original_messages)
