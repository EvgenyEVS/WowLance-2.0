"""Room chat API (C20). Mutations require the actor (X-Actor-Sub stub / JWT sub)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.rbac_deps import require_member
from app.db.session import get_db
from app.domain.chat import (
    RoomNotFoundError,
    create_message,
    list_messages,
)
from app.domain.schemas import (
    RoomMessageCreateRequest,
    RoomMessageListResponse,
    RoomMessageOut,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["chat"])


def _map_errors(exc: Exception) -> None:
    if isinstance(exc, RoomNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raise exc


@router.get(
    "/{room_id}/messages",
    response_model=RoomMessageListResponse,
    responses={
        200: {"description": "Messages of the room, oldest first"},
        404: {"description": "room_id does not exist"},
    },
)
def get_room_messages(
    room_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> RoomMessageListResponse:
    """GET /api/v1/rooms/{room_id}/messages — last N messages, oldest first."""
    try:
        return list_messages(db, room_id, limit=limit)
    except RoomNotFoundError as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/messages",
    response_model=RoomMessageOut,
    status_code=201,
    responses={
        201: {"description": "Message created"},
        404: {"description": "room_id does not exist"},
        422: {"description": "validation or missing actor (X-Actor-Sub)"},
    },
)
def post_room_message(
    room_id: uuid.UUID,
    payload: RoomMessageCreateRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_member),
) -> RoomMessageOut:
    """POST /api/v1/rooms/{room_id}/messages — author = actor."""
    try:
        return create_message(db, room_id, actor, payload)
    except RoomNotFoundError as exc:
        _map_errors(exc)
        raise
