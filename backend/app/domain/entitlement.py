"""EntitlementGranted application service (C2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Entitlement, OutboxMessage, Room
from app.domain.schemas import (
    EntitlementGrantedRequest,
    EntitlementGrantedResponse,
    EntitlementStatus,
)

STAFFING_UNLOCKED_EVENT = "StaffingUnlocked"


class RoomNotFoundError(Exception):
    """No room for the given room_id."""


class EntitlementRoomConflictError(Exception):
    """entitlement_id already bound to a different room_id."""


@dataclass
class EntitlementResult:
    response: EntitlementGrantedResponse
    http_status: int


def _already_granted(room_id) -> EntitlementResult:
    return EntitlementResult(
        response=EntitlementGrantedResponse(
            room_id=room_id,
            staffing_unlocked=True,
            status=EntitlementStatus.already_granted,
        ),
        http_status=200,
    )


def _granted(room_id) -> EntitlementResult:
    return EntitlementResult(
        response=EntitlementGrantedResponse(
            room_id=room_id,
            staffing_unlocked=True,
            status=EntitlementStatus.granted,
        ),
        http_status=200,
    )


def _staffing_unlocked_outbox(
    room_id: uuid.UUID,
    entitlement_id: uuid.UUID,
    founder_sub: str | None,
    unlocked_at,
) -> OutboxMessage:
    """Outbox row for the first staffing unlock of a room.

    Idempotency key = `room:{id}:StaffingUnlocked`. Chosen over `str(room_id)`
    because `outbox_messages.idempotency_key` is globally unique and
    `RoomCreated` (C11) already uses `str(room_id)` for the same room.
    One transaction with the grant (added before `db.commit()`).
    """
    payload = {
        "room_id": str(room_id),
        "entitlement_id": str(entitlement_id),
        "founder_sub": founder_sub,
        "unlocked_at": unlocked_at.isoformat(),
        "staffing_unlocked": True,
    }
    return OutboxMessage(
        id=uuid.uuid4(),
        event_type=STAFFING_UNLOCKED_EVENT,
        idempotency_key=f"room:{room_id}:StaffingUnlocked",
        payload=payload,
        status="sent",
        sent_at=unlocked_at,
    )


def _ensure_unlocked(db: Session, room: Room) -> None:
    if not room.staffing_unlocked:
        room.staffing_unlocked = True
        db.commit()


def grant_entitlement(db: Session, body: EntitlementGrantedRequest) -> EntitlementResult:
    existing = db.get(Entitlement, body.entitlement_id)
    if existing is not None:
        if existing.room_id != body.room_id:
            raise EntitlementRoomConflictError(
                "entitlement_id already bound to a different room_id"
            )
        room = db.get(Room, existing.room_id)
        if room is not None:
            _ensure_unlocked(db, room)
        return _already_granted(existing.room_id)

    room = db.get(Room, body.room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")

    was_unlocked = room.staffing_unlocked
    unlocked_at = datetime.now(timezone.utc)
    db.add(
        Entitlement(
            entitlement_id=body.entitlement_id,
            room_id=room.id,
            source=body.source.value,
            order_id=body.order_id,
        )
    )
    room.staffing_unlocked = True
    if not was_unlocked:
        db.add(
            _staffing_unlocked_outbox(
                room.id, body.entitlement_id, room.founder_sub, unlocked_at
            )
        )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raced = db.get(Entitlement, body.entitlement_id)
        if raced is None:
            raise
        if raced.room_id != body.room_id:
            raise EntitlementRoomConflictError(
                "entitlement_id already bound to a different room_id"
            ) from exc
        room = db.get(Room, raced.room_id)
        if room is not None:
            _ensure_unlocked(db, room)
        return _already_granted(raced.room_id)

    db.refresh(room)
    return _granted(room.id)
