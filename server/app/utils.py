from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return uuid4().hex


def row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row)
