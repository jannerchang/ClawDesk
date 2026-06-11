from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import dumps_json, get_conn, seed_default_channel_members
from app.schemas import ChannelCreate, ChannelOut, SubchannelFromMessagesCreate, UserOut, channel_from_row
from app.utils import new_id, now_iso

router = APIRouter(prefix="/channels", tags=["channels"])


def _fetch_channel(conn, channel_id: str):
    row = conn.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Channel not found")
    return row


@router.post("", response_model=ChannelOut, status_code=201)
def create_channel(payload: ChannelCreate) -> dict:
    ts = now_iso()
    channel_id = new_id()
    with get_conn() as conn:
        space = conn.execute("SELECT id FROM spaces WHERE id = ?", (payload.space_id,)).fetchone()
        if not space:
            raise HTTPException(status_code=404, detail="Space not found")
        if payload.parent_channel_id:
            _fetch_channel(conn, payload.parent_channel_id)
        conn.execute(
            """
            INSERT INTO channels (
                id, space_id, parent_channel_id, name, type, mode, status, description,
                tags, agent_config_id, source_message_ids, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
            """,
            (
                channel_id,
                payload.space_id,
                payload.parent_channel_id,
                payload.name,
                payload.type,
                payload.mode,
                payload.status,
                payload.description,
                dumps_json(payload.tags),
                dumps_json(payload.source_message_ids),
                ts,
                ts,
            ),
        )
        row = _fetch_channel(conn, channel_id)
        seed_default_channel_members(conn)
        return channel_from_row(dict(row)).model_dump()


@router.get("/{channel_id}", response_model=ChannelOut)
def get_channel(channel_id: str) -> dict:
    with get_conn() as conn:
        row = _fetch_channel(conn, channel_id)
        return channel_from_row(dict(row)).model_dump()


@router.get("/{channel_id}/members", response_model=list[UserOut])
def list_channel_members(channel_id: str) -> list[dict]:
    with get_conn() as conn:
        _fetch_channel(conn, channel_id)
        rows = conn.execute(
            """
            SELECT users.id, users.name, users.kind, users.avatar, users.description,
                   channel_members.role, users.created_at, users.updated_at
            FROM channel_members
            JOIN users ON users.id = channel_members.user_id
            WHERE channel_members.channel_id = ?
            ORDER BY CASE channel_members.role WHEN 'owner' THEN 0 WHEN 'bot' THEN 1 ELSE 2 END,
                     users.name ASC
            """,
            (channel_id,),
        ).fetchall()
        return [dict(row) for row in rows]


@router.get("/{channel_id}/subchannels", response_model=list[ChannelOut])
def list_subchannels(channel_id: str) -> list[dict]:
    with get_conn() as conn:
        _fetch_channel(conn, channel_id)
        rows = conn.execute(
            "SELECT * FROM channels WHERE parent_channel_id = ? ORDER BY created_at ASC",
            (channel_id,),
        ).fetchall()
        return [channel_from_row(dict(row)).model_dump() for row in rows]


@router.post("/{channel_id}/subchannels/from_messages", response_model=ChannelOut, status_code=201)
def create_subchannel_from_messages(channel_id: str, payload: SubchannelFromMessagesCreate) -> dict:
    if not payload.source_message_ids:
        raise HTTPException(status_code=400, detail="source_message_ids cannot be empty")
    ts = now_iso()
    new_channel_id = new_id()
    with get_conn() as conn:
        parent = dict(_fetch_channel(conn, channel_id))
        placeholders = ",".join("?" for _ in payload.source_message_ids)
        rows = conn.execute(
            f"SELECT * FROM messages WHERE channel_id = ? AND id IN ({placeholders}) ORDER BY created_at ASC",
            (channel_id, *payload.source_message_ids),
        ).fetchall()
        if len(rows) != len(set(payload.source_message_ids)):
            raise HTTPException(status_code=400, detail="Some source messages were not found in the channel")

        conn.execute(
            """
            INSERT INTO channels (
                id, space_id, parent_channel_id, name, type, mode, status, description,
                tags, agent_config_id, source_message_ids, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_channel_id,
                parent["space_id"],
                channel_id,
                payload.name,
                payload.type,
                payload.mode,
                payload.status,
                payload.description,
                dumps_json(payload.tags),
                parent.get("agent_config_id"),
                dumps_json(payload.source_message_ids),
                ts,
                ts,
            ),
        )

        for row in rows:
            copied_id = new_id()
            conn.execute(
                """
                INSERT INTO messages (
                    id, channel_id, sender_type, sender_name, content, content_type,
                    reply_to_id, source_message_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                (
                    copied_id,
                    new_channel_id,
                    row["sender_type"],
                    row["sender_name"],
                    row["content"],
                    row["content_type"],
                    row["id"],
                    ts,
                    ts,
                ),
            )

        system_message = f"已从 {len(rows)} 条消息创建子频道：{payload.name}"
        conn.execute(
            """
            INSERT INTO messages (id, channel_id, sender_type, sender_name, content, content_type, created_at, updated_at)
            VALUES (?, ?, 'system', 'ClawDesk', ?, 'system', ?, ?)
            """,
            (new_id(), channel_id, system_message, ts, ts),
        )
        new_row = _fetch_channel(conn, new_channel_id)
        seed_default_channel_members(conn)
        return channel_from_row(dict(new_row)).model_dump()
