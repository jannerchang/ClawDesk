from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.db import dumps_json, get_conn
from app.schemas import (
    ModulePostBindingCreate,
    ModulePostBindingOut,
    ModulePostBindingUpdate,
    ModulePostSyncCreate,
    module_post_binding_from_row,
)
from app.utils import new_id, now_iso

router = APIRouter(prefix="/module-post-bindings", tags=["module-post-bindings"])


def _fetch_binding(conn, binding_id: str) -> dict:
    row = conn.execute("SELECT * FROM module_post_bindings WHERE id = ?", (binding_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Module post binding not found")
    return module_post_binding_from_row(dict(row)).model_dump()


@router.get("", response_model=list[ModulePostBindingOut])
def list_module_post_bindings(module_key: str | None = None, platform: str | None = None) -> list[dict]:
    clauses: list[str] = []
    params: list[str] = []
    if module_key:
        clauses.append("module_key = ?")
        params.append(module_key)
    if platform:
        clauses.append("platform = ?")
        params.append(platform)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM module_post_bindings {where} ORDER BY module_key ASC, updated_at DESC",
            params,
        ).fetchall()
        return [module_post_binding_from_row(dict(row)).model_dump() for row in rows]


@router.post("", response_model=ModulePostBindingOut, status_code=201)
def create_module_post_binding(payload: ModulePostBindingCreate) -> dict:
    ts = now_iso()
    binding_id = new_id()
    with get_conn() as conn:
        try:
            conn.execute(
                """
                INSERT INTO module_post_bindings (
                    id, module_key, module_label, platform, external_channel_id, external_post_id,
                    sync_mode, last_payload, last_synced_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
                """,
                (
                    binding_id,
                    payload.module_key,
                    payload.module_label,
                    payload.platform,
                    payload.external_channel_id,
                    payload.external_post_id,
                    payload.sync_mode,
                    ts,
                    ts,
                ),
            )
        except Exception as exc:
            raise HTTPException(status_code=409, detail="Module is already bound to this post") from exc
        return _fetch_binding(conn, binding_id)


@router.patch("/{binding_id}", response_model=ModulePostBindingOut)
def update_module_post_binding(binding_id: str, payload: ModulePostBindingUpdate) -> dict:
    ts = now_iso()
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM module_post_bindings WHERE id = ?", (binding_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Module post binding not found")
        data = dict(row)
        module_label = payload.module_label if payload.module_label is not None else data["module_label"]
        sync_mode = payload.sync_mode if payload.sync_mode is not None else data["sync_mode"]
        conn.execute(
            """
            UPDATE module_post_bindings
            SET module_label = ?, sync_mode = ?, updated_at = ?
            WHERE id = ?
            """,
            (module_label, sync_mode, ts, binding_id),
        )
        return _fetch_binding(conn, binding_id)


@router.post("/{binding_id}/sync", response_model=ModulePostBindingOut)
def sync_module_post_binding(binding_id: str, payload: ModulePostSyncCreate) -> dict:
    ts = now_iso()
    sync_payload = payload.model_dump(exclude_none=True)
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM module_post_bindings WHERE id = ?", (binding_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Module post binding not found")
        conn.execute(
            """
            UPDATE module_post_bindings
            SET last_payload = ?, last_synced_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (dumps_json(sync_payload), ts, ts, binding_id),
        )
        return _fetch_binding(conn, binding_id)


@router.delete("/{binding_id}", status_code=204)
def delete_module_post_binding(binding_id: str) -> None:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM module_post_bindings WHERE id = ?", (binding_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Module post binding not found")
