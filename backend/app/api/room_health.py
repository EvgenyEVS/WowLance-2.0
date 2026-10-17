"""C13 room health API: GET aggregate (client) + publish stub (internal).

`GET /api/v1/rooms/{id}/health` — read-only snapshot for the Strategy showcase.
`POST /internal/v1/rooms/{id}/health/publish` — writes outbox RoomHealthSnapshot
(status=sent). Live Strategy HTTP is out of scope; /internal stays open (C11 note).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.room_health import (
    RoomNotFoundError,
    build_room_health,
    publish_room_health,
)
from app.domain.schemas import RoomHealthOut, RoomHealthPublishResponse

router = APIRouter(prefix="/api/v1/rooms", tags=["room-health"])
internal_router = APIRouter(prefix="/internal/v1/rooms", tags=["room-health-internal"])


def _map_errors(exc: Exception) -> None:
    if isinstance(exc, RoomNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raise exc


@router.get(
    "/{room_id}/health",
    response_model=RoomHealthOut,
    responses={
        200: {"description": "Room health snapshot (zeros for empty entities)"},
        404: {"description": "room_id does not exist"},
    },
)
def get_room_health(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RoomHealthOut:
    try:
        return build_room_health(db, room_id)
    except RoomNotFoundError as exc:
        _map_errors(exc)
        raise


@internal_router.post(
    "/{room_id}/health/publish",
    response_model=RoomHealthPublishResponse,
    responses={
        200: {"description": "outbox RoomHealthSnapshot row written (stub sent)"},
        404: {"description": "room_id does not exist"},
    },
)
def post_publish_room_health(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RoomHealthPublishResponse:
    try:
        return publish_room_health(db, room_id)
    except RoomNotFoundError as exc:
        _map_errors(exc)
        raise
