"""C13 room health: read-only aggregate for the Strategy showcase.

Only SELECT/count over local PG (slots / tasks / leads). No mutations, no live
Strategy HTTP: `publish_room_health` persists an outbox row
(event_type=RoomHealthSnapshot, status=sent) — always a new row (snapshot history).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import OutboxMessage, Room, RoomFunctionSlot, RoomLead, RoomTask
from app.domain.schemas import (
    RoomHealthLeadsOut,
    RoomHealthOut,
    RoomHealthPublishResponse,
    RoomHealthPublishStatus,
    RoomHealthRoomOut,
    RoomHealthSlotsOut,
    RoomHealthTasksOut,
    RoomType,
)
from app.domain.strategy_accept import active_snapshot

ROOM_HEALTH_EVENT = "RoomHealthSnapshot"


class RoomNotFoundError(Exception):
    """No room for the given id."""


def _require_room(db: Session, room_id: uuid.UUID) -> Room:
    room = db.scalar(
        select(Room)
        .where(Room.id == room_id)
        .options(selectinload(Room.strategy_snapshots))
    )
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    return room


def _count_by_status(db: Session, model, room_id: uuid.UUID) -> dict[str, int]:
    rows = db.execute(
        select(model.status, func.count())
        .where(model.room_id == room_id)
        .group_by(model.status)
    ).all()
    return {status: count for status, count in rows}


def build_room_health(db: Session, room_id: uuid.UUID) -> RoomHealthOut:
    """Aggregate a single snapshot; empty entities are zeros, never 404."""
    room = _require_room(db, room_id)
    snap = active_snapshot(room)

    slot_counts = _count_by_status(db, RoomFunctionSlot, room.id)
    slots = RoomHealthSlotsOut(
        total=sum(slot_counts.values()),
        open=slot_counts.get("open", 0),
        filled=slot_counts.get("filled", 0),
        cancelled=slot_counts.get("cancelled", 0),
    )

    task_counts = _count_by_status(db, RoomTask, room.id)
    tasks = RoomHealthTasksOut(
        todo=task_counts.get("todo", 0),
        in_progress=task_counts.get("in_progress", 0),
        submitted=task_counts.get("submitted", 0),
        done=task_counts.get("done", 0),
    )

    lead_counts = _count_by_status(db, RoomLead, room.id)
    leads = RoomHealthLeadsOut(
        total=sum(lead_counts.values()),
        hot=lead_counts.get("hot", 0),
        handed_to_crm=lead_counts.get("handed_to_crm", 0),
    )

    return RoomHealthOut(
        room_id=room.id,
        captured_at=datetime.now(timezone.utc),
        room=RoomHealthRoomOut(
            room_type=RoomType(room.room_type),
            name=room.name,
            staffing_unlocked=room.staffing_unlocked,
            strategy_id=snap.strategy_id if snap is not None else None,
            strategy_version=snap.strategy_version if snap is not None else None,
        ),
        slots=slots,
        tasks=tasks,
        leads=leads,
    )


def publish_room_health(
    db: Session, room_id: uuid.UUID
) -> RoomHealthPublishResponse:
    """Stub publish: one new outbox row per call (history, no dedup)."""
    snapshot = build_room_health(db, room_id)
    outbox_id = uuid.uuid4()
    db.add(
        OutboxMessage(
            id=outbox_id,
            event_type=ROOM_HEALTH_EVENT,
            idempotency_key=str(outbox_id),
            payload=snapshot.model_dump(mode="json"),
            status="sent",
            sent_at=snapshot.captured_at,
        )
    )
    db.commit()
    return RoomHealthPublishResponse(
        outbox_id=outbox_id,
        event_type=ROOM_HEALTH_EVENT,
        status=RoomHealthPublishStatus.published,
        snapshot=snapshot,
    )
