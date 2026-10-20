"""C17 member termination: расторжение участника с причиной + освобождение слота + outbox для Talent.

Одна транзакция: слот(ы) -> room_terminations -> outbox MemberTerminated.
Не откатывает начисления (C16), не удаляет roster, не вызывает live Talent.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OutboxMessage, Room, RoomFunctionSlot, RoomTermination
from app.domain.staffing import SlotNotFilledError

MEMBER_TERMINATED_EVENT = "MemberTerminated"


class RoomNotFoundError(Exception):
    """No room for the given id."""


class NotSeatedError(Exception):
    """freelancer_sub has no filled slot in this room (not_seated)."""


def _require_room(db: Session, room_id: uuid.UUID) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    return room


def _filled_slots_for_sub(
    db: Session, room_id: uuid.UUID, freelancer_sub: str
) -> list[RoomFunctionSlot]:
    return list(
        db.scalars(
            select(RoomFunctionSlot).where(
                RoomFunctionSlot.room_id == room_id,
                RoomFunctionSlot.freelancer_sub == freelancer_sub,
                RoomFunctionSlot.status == "filled",
            )
        ).all()
    )


def terminate_member(
    db: Session,
    room_id: uuid.UUID,
    freelancer_sub: str,
    reason: str,
    terminated_by_sub: str,
    slot_id: uuid.UUID | None = None,
) -> dict:
    """Terminate a seated freelancer: clear slot(s), journal + outbox in one transaction.

    Returns { status, freelancer_sub, slot_ids }.
    Raises RoomNotFoundError / NotSeatedError / SlotNotFilledError.
    """
    _require_room(db, room_id)

    if slot_id is not None:
        slot = db.get(RoomFunctionSlot, slot_id)
        if slot is None or slot.room_id != room_id:
            raise NotSeatedError("not_seated")
        if slot.status != "filled" or slot.freelancer_sub != freelancer_sub:
            if slot.status != "filled":
                raise SlotNotFilledError("slot_not_filled")
            raise NotSeatedError("not_seated")
        target_slots = [slot]
    else:
        target_slots = _filled_slots_for_sub(db, room_id, freelancer_sub)
        if not target_slots:
            raise NotSeatedError("not_seated")

    slot_ids = [s.id for s in target_slots]
    for slot in target_slots:
        slot.freelancer_sub = None
        slot.status = "open"

    terminated_at = datetime.now(timezone.utc)
    termination_id = uuid.uuid4()
    db.add(
        RoomTermination(
            id=termination_id,
            room_id=room_id,
            freelancer_sub=freelancer_sub,
            reason=reason,
            terminated_by_sub=terminated_by_sub,
            slot_ids=[str(s) for s in slot_ids],
        )
    )
    db.add(
        OutboxMessage(
            id=uuid.uuid4(),
            event_type=MEMBER_TERMINATED_EVENT,
            idempotency_key=str(termination_id),
            payload={
                "room_id": str(room_id),
                "freelancer_sub": freelancer_sub,
                "reason": reason,
                "terminated_by_sub": terminated_by_sub,
                "terminated_at": terminated_at.isoformat(),
                "slot_ids": [str(s) for s in slot_ids],
            },
            status="sent",
            sent_at=terminated_at,
        )
    )
    db.commit()

    return {
        "status": "terminated",
        "freelancer_sub": freelancer_sub,
        "slot_ids": slot_ids,
    }


def list_terminations(
    db: Session, room_id: uuid.UUID
) -> list[RoomTermination]:
    """List termination journal entries for a room (newest first)."""
    room = db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    return list(
        db.scalars(
            select(RoomTermination)
            .where(RoomTermination.room_id == room_id)
            .order_by(RoomTermination.created_at.desc(), RoomTermination.id.desc())
        ).all()
    )
