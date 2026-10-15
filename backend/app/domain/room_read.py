"""Read-only room + strategy snapshot (C3). GET does not write."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Room
from app.domain.schemas import (
    RoomDocumentOut,
    RoomReadResponse,
    RoomStrategyOut,
    RoomType,
)


class RoomNotFoundError(Exception):
    """No room (or snapshot) for the given id."""


def get_room_read(db: Session, room_id: uuid.UUID) -> RoomReadResponse:
    room = db.scalar(
        select(Room)
        .where(Room.id == room_id)
        .options(joinedload(Room.strategy_snapshot))
    )
    if room is None or room.strategy_snapshot is None:
        raise RoomNotFoundError("room_id does not exist")

    snap = room.strategy_snapshot
    payload = snap.strategy_payload or {}
    documents = None
    if snap.documents:
        documents = [RoomDocumentOut.model_validate(item) for item in snap.documents]

    return RoomReadResponse(
        id=room.id,
        name=room.name,
        room_type=RoomType(room.room_type),
        timezone=room.timezone,
        founder_sub=room.founder_sub,
        handoff_id=room.handoff_id,
        staffing_unlocked=room.staffing_unlocked,
        created_at=room.created_at,
        strategy=RoomStrategyOut(
            strategy_id=snap.strategy_id,
            strategy_version=snap.strategy_version,
            offer=payload.get("offer") or "",
            audience=payload.get("audience") or "",
            hot_criteria=payload.get("hot_criteria") or "",
            utp=payload.get("utp"),
            documents=documents,
            staffing_intent=snap.staffing_intent,
        ),
    )
