from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db import db_path, get_conn
from app.schemas import AttachmentOut
from app.utils import new_id, now_iso

router = APIRouter(prefix="/messages/{message_id}/attachments", tags=["attachments"])


def _attachment_root() -> Path:
    return db_path().parent / "attachments"


def _kind_from_content_type(content_type: str | None) -> str:
    if not content_type:
        return "file"
    if content_type.startswith("image/"):
        return "image"
    if content_type.startswith("audio/"):
        return "voice"
    return "file"


@router.get("", response_model=list[AttachmentOut])
def list_attachments(message_id: str) -> list[dict]:
    with get_conn() as conn:
        message = conn.execute("SELECT id FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        rows = conn.execute(
            "SELECT * FROM attachments WHERE message_id = ? ORDER BY created_at ASC",
            (message_id,),
        ).fetchall()
        return [dict(row) for row in rows]


@router.post("", response_model=AttachmentOut, status_code=201)
def upload_attachment(message_id: str, file: UploadFile = File(...)) -> dict:
    ts = now_iso()
    attachment_id = new_id()
    filename = Path(file.filename or "attachment").name
    content_type = file.content_type
    kind = _kind_from_content_type(content_type)

    with get_conn() as conn:
        message = conn.execute("SELECT id FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        target_dir = _attachment_root() / message_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{attachment_id}-{filename}"
        with target_path.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        size = target_path.stat().st_size

        conn.execute(
            """
            INSERT INTO attachments (
                id, message_id, kind, original_name, local_path, mime_type, size, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (attachment_id, message_id, kind, filename, str(target_path), content_type, size, ts),
        )
        row = conn.execute("SELECT * FROM attachments WHERE id = ?", (attachment_id,)).fetchone()
        return dict(row)
