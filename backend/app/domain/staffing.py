"""C4 staffing seats: materialize from local snapshot intent. No Talent/matching."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Room, RoomFunctionSlot
from app.domain.schemas import (
    FunctionSlotOut,
    MaterializeStatus,
    SlotStatus,
    StaffingMaterializeResponse,
    StaffingSlotsListResponse,
)


class RoomNotFoundError(Exception):
    """No room for the given id."""


class StaffingLockedError(Exception):
    """staffing_unlocked is false."""


@dataclass
class PlannedSeat:
    role_key: str
    seat_index: int
    level_min: str | None


def _require_unlocked_room(db: Session, room_id: uuid.UUID) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    if not room.staffing_unlocked:
        raise StaffingLockedError("staffing_locked")
    return room


def _slot_out(row: RoomFunctionSlot) -> FunctionSlotOut:
    return FunctionSlotOut(
        id=row.id,
        room_id=row.room_id,
        role_key=row.role_key,
        seat_index=row.seat_index,
        level_min=row.level_min,
        status=SlotStatus(row.status),
        freelancer_sub=row.freelancer_sub,
    )


def _list_slot_rows(db: Session, room_id: uuid.UUID) -> list[RoomFunctionSlot]:
    return list(
        db.scalars(
            select(RoomFunctionSlot)
            .where(RoomFunctionSlot.room_id == room_id)
            .order_by(RoomFunctionSlot.role_key, RoomFunctionSlot.seat_index)
        ).all()
    )


def planned_seats_from_intent(staffing_intent: dict | None) -> list[PlannedSeat]:
    """Expand staffing_intent.slots into per-seat rows (count → seat_index 1..N)."""
    if not staffing_intent:
        return []
    raw_slots = staffing_intent.get("slots") or []
    planned: list[PlannedSeat] = []
    for item in raw_slots:
        if not isinstance(item, dict):
            continue
        role_key = item.get("role_key")
        count = item.get("count")
        if not role_key or not isinstance(count, int) or count < 1:
            continue
        level_min = item.get("level_min")
        if level_min is not None:
            level_min = str(level_min)
        for seat_index in range(1, count + 1):
            planned.append(
                PlannedSeat(
                    role_key=str(role_key),
                    seat_index=seat_index,
                    level_min=level_min,
                )
            )
    return planned


def list_slots(db: Session, room_id: uuid.UUID) -> StaffingSlotsListResponse:
    room = _require_unlocked_room(db, room_id)
    rows = _list_slot_rows(db, room.id)
    return StaffingSlotsListResponse(
        room_id=room.id,
        staffing_unlocked=True,
        slots=[_slot_out(row) for row in rows],
    )


def materialize_slots(db: Session, room_id: uuid.UUID) -> StaffingMaterializeResponse:
    room = _require_unlocked_room(db, room_id)
    snapshot = room.strategy_snapshot
    intent = snapshot.staffing_intent if snapshot is not None else None
    planned = planned_seats_from_intent(intent)
    existing = _list_slot_rows(db, room.id)
    existing_keys = {(row.role_key, row.seat_index) for row in existing}

    missing = [
        seat
        for seat in planned
        if (seat.role_key, seat.seat_index) not in existing_keys
    ]
    if not missing:
        return StaffingMaterializeResponse(
            room_id=room.id,
            status=(
                MaterializeStatus.already_materialized
                if existing
                else MaterializeStatus.materialized
            ),
            slots=[_slot_out(row) for row in existing],
        )

    for seat in missing:
        db.add(
            RoomFunctionSlot(
                id=uuid.uuid4(),
                room_id=room.id,
                role_key=seat.role_key,
                seat_index=seat.seat_index,
                level_min=seat.level_min,
                status=SlotStatus.open.value,
                freelancer_sub=None,
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        rows = _list_slot_rows(db, room.id)
        return StaffingMaterializeResponse(
            room_id=room.id,
            status=MaterializeStatus.already_materialized,
            slots=[_slot_out(row) for row in rows],
        )

    rows = _list_slot_rows(db, room.id)
    status = (
        MaterializeStatus.already_materialized
        if existing
        else MaterializeStatus.materialized
    )
    return StaffingMaterializeResponse(
        room_id=room.id,
        status=status,
        slots=[_slot_out(row) for row in rows],
    )
