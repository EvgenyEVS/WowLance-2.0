"""FounderHandoff application service (C1)."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Room, StrategySnapshot, User
from app.domain.schemas import (
    FounderHandoffRequest,
    FounderHandoffResponse,
    HandoffStatus,
)


class HandoffConflictError(Exception):
    """Same handoff_id already bound to a different payload."""


def fingerprint_payload(body: FounderHandoffRequest) -> str:
    """Stable hash of the semantic handoff payload (for idempotency / 409)."""
    data = body.model_dump(mode="json", exclude_none=False)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class HandoffResult:
    response: FounderHandoffResponse
    http_status: int


def process_founder_handoff(db: Session, body: FounderHandoffRequest) -> HandoffResult:
    fp = fingerprint_payload(body)
    existing = db.scalar(select(Room).where(Room.handoff_id == body.handoff_id))
    if existing is not None:
        if existing.request_fingerprint != fp:
            raise HandoffConflictError(
                "handoff_id already bound to a different payload"
            )
        # Immutable: do not touch StrategySnapshot or staffing_unlocked on replay.
        return HandoffResult(
            response=FounderHandoffResponse(
                room_id=existing.id,
                status=HandoffStatus.already_exists,
                staffing_unlocked=existing.staffing_unlocked,
            ),
            http_status=200,
        )

    user = db.get(User, body.founder_sub)
    if user is None:
        user = User(sub=body.founder_sub)
        db.add(user)

    room = Room(
        id=uuid.uuid4(),
        room_type=body.room_type.value,
        name=body.project.name,
        timezone=body.project.timezone or "Europe/Moscow",
        founder_sub=body.founder_sub,
        handoff_id=body.handoff_id,
        staffing_unlocked=False,
        request_fingerprint=fp,
    )
    snapshot = StrategySnapshot(
        id=uuid.uuid4(),
        room_id=room.id,
        strategy_id=body.strategy_id,
        strategy_version=body.strategy_version,
        strategy_payload=body.strategy.model_dump(mode="json"),
        documents=(
            [d.model_dump(mode="json") for d in body.documents]
            if body.documents is not None
            else None
        ),
        staffing_intent=(
            body.staffing_intent.model_dump(mode="json")
            if body.staffing_intent is not None
            else None
        ),
        commercial=(
            body.commercial.model_dump(mode="json")
            if body.commercial is not None
            else None
        ),
    )
    # Link before flush so relationship is consistent in-session.
    room.strategy_snapshot = snapshot
    db.add(room)
    db.commit()
    db.refresh(room)

    return HandoffResult(
        response=FounderHandoffResponse(
            room_id=room.id,
            status=HandoffStatus.created,
            staffing_unlocked=False,
        ),
        http_status=201,
    )
