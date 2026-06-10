from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.schemas import MessageCreate, MessageOut
from app.utils import new_id, now_iso

router = APIRouter(prefix="/channels/{channel_id}/messages", tags=["messages"])


def _ensure_channel(conn, channel_id: str) -> None:
    row = conn.execute("SELECT id FROM channels WHERE id = ?", (channel_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Channel not found")


@router.get("", response_model=list[MessageOut])
def list_messages(channel_id: str) -> list[dict]:
    with get_conn() as conn:
        _ensure_channel(conn, channel_id)
        rows = conn.execute(
            "SELECT * FROM messages WHERE channel_id = ? ORDER BY created_at ASC",
            (channel_id,),
        ).fetchall()
        return [dict(row) for row in rows]


@router.post("", response_model=MessageOut, status_code=201)
def create_message(channel_id: str, payload: MessageCreate) -> dict:
    ts = now_iso()
    message_id = new_id()
    with get_conn() as conn:
        _ensure_channel(conn, channel_id)
        conn.execute(
            """
            INSERT INTO messages (
                id, channel_id, sender_type, sender_name, content, content_type,
                reply_to_id, source_message_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                channel_id,
                payload.sender_type,
                payload.sender_name,
                payload.content,
                payload.content_type,
                payload.reply_to_id,
                payload.source_message_id,
                ts,
                ts,
            ),
        )
        row = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
        return dict(row)
