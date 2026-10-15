"""Read-only room + active strategy snapshot (C3/C5). GET does not write."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Room
from app.domain.schemas import (
    PendingStrategyOut,
    RoomDocumentOut,
    RoomReadResponse,
    RoomStrategyOut,
    RoomType,
)
from app.domain.strategy_accept import active_snapshot, pending_proposal


class RoomNotFoundError(Exception):
    """No room (or active snapshot) for the given id."""


def get_room_read(db: Session, room_id: uuid.UUID) -> RoomReadResponse:
    room = db.scalar(
        select(Room)
        .where(Room.id == room_id)
        .options(selectinload(Room.strategy_snapshots))
    )
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    snap = active_snapshot(room)
    if snap is None:
        raise RoomNotFoundError("room_id does not exist")

    payload = snap.strategy_payload or {}
    documents = None
    if snap.documents:
        documents = [RoomDocumentOut.model_validate(item) for item in snap.documents]

    pending = pending_proposal(db, room.id)
    pending_out = None
    if pending is not None:
        p_payload = pending.strategy_payload or {}
        pending_out = PendingStrategyOut(
            proposal_id=pending.id,
            strategy_version=pending.strategy_version,
            offer=p_payload.get("offer") or "",
            audience=p_payload.get("audience") or "",
            hot_criteria=p_payload.get("hot_criteria") or "",
            status="pending",
        )

    return RoomReadResponse(
        id=room.id,
        name=room.name,
        room_type=RoomType(room.room_type),
        timezone=room.timezone,
        founder_sub=room.founder_sub,
        handoff_id=room.handoff_id,
        staffing_unlocked=room.staffing_unlocked,
        created_at=room.created_at,
        pending_strategy=pending_out,
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
