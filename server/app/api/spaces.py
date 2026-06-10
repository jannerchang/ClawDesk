from __future__ import annotations

from fastapi import APIRouter

from app.db import get_conn
from app.schemas import SpaceCreate, SpaceOut
from app.utils import new_id, now_iso

router = APIRouter(prefix="/spaces", tags=["spaces"])


@router.get("", response_model=list[SpaceOut])
def list_spaces() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM spaces ORDER BY sort_order ASC, created_at ASC").fetchall()
        return [dict(row) for row in rows]


@router.post("", response_model=SpaceOut, status_code=201)
def create_space(payload: SpaceCreate) -> dict:
    ts = now_iso()
    space_id = new_id()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO spaces (id, name, type, icon, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (space_id, payload.name, payload.type, payload.icon, payload.sort_order, ts, ts),
        )
        row = conn.execute("SELECT * FROM spaces WHERE id = ?", (space_id,)).fetchone()
        return dict(row)


@router.get("/{space_id}/channels")
def list_space_channels(space_id: str) -> list[dict]:
    from app.schemas import channel_from_row

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM channels
            WHERE space_id = ? AND parent_channel_id IS NULL
            ORDER BY created_at ASC
            """,
            (space_id,),
        ).fetchall()
        return [channel_from_row(dict(row)).model_dump() for row in rows]
