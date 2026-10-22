"""C20 room chat: list + create messages in a room.

Minimal immutable message store. No WebSocket / SSE — poll Refresh is enough.
Author = actor of the request (get_actor_sub). Editing/deletion out of scope.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Room, RoomMessage
from app.domain.schemas import (
    RoomMessageCreateRequest,
    RoomMessageListResponse,
    RoomMessageOut,
)

LIST_LIMIT = 100
LIST_DEFAULT = 50


class RoomNotFoundError(Exception):
    """No room for the given id."""


def _require_room(db: Session, room_id: uuid.UUID) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    return room


def _message_out(row: RoomMessage) -> RoomMessageOut:
    return RoomMessageOut(
        id=row.id,
        room_id=row.room_id,
        author_sub=row.author_sub,
        body=row.body,
        created_at=row.created_at,
    )


def list_messages(
    db: Session, room_id: uuid.UUID, limit: int = LIST_DEFAULT
) -> RoomMessageListResponse:
    """Last `limit` messages of a room, returned oldest-first."""
    room = _require_room(db, room_id)
    limit = max(1, min(limit, LIST_LIMIT))
    newest_first = list(
        db.scalars(
            select(RoomMessage)
            .where(RoomMessage.room_id == room.id)
            .order_by(RoomMessage.created_at.desc(), RoomMessage.id.desc())
            .limit(limit)
        ).all()
    )
    rows = list(reversed(newest_first))
    return RoomMessageListResponse(
        room_id=room.id,
        messages=[_message_out(row) for row in rows],
    )


def create_message(
    db: Session, room_id: uuid.UUID, actor_sub: str, payload: RoomMessageCreateRequest
) -> RoomMessageOut:
    """POST a new message; author = actor_sub."""
    room = _require_room(db, room_id)
    row = RoomMessage(
        id=uuid.uuid4(),
        room_id=room.id,
        author_sub=actor_sub,
        body=payload.body,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _message_out(row)
