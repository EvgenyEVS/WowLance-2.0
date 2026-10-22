"""Public read API for a room (C3). Open, no Keycloak yet."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_optional_actor_sub
from app.db.session import get_db
from app.domain.room_read import RoomNotFoundError, get_room_read
from app.domain.schemas import RoomReadResponse

router = APIRouter(prefix="/api/v1", tags=["rooms"])


@router.get(
    "/rooms/{room_id}",
    response_model=RoomReadResponse,
    responses={
        200: {"description": "Room + strategy snapshot"},
        404: {"description": "room_id does not exist"},
    },
)
def read_room(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str | None = Depends(get_optional_actor_sub),
) -> RoomReadResponse:
    """GET /api/v1/rooms/{room_id} — read staffing_unlocked as stored."""
    try:
        return get_room_read(db, room_id, actor_sub=actor)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
