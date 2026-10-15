"""StrategyPublished inbox and Accept/Reject (C5). Does not rematerialize slots."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.models import Room, StrategyProposal, StrategySnapshot
from app.domain.schemas import (
    PublicationStatus,
    StrategyDecideResponse,
    StrategyDecision,
    StrategyPublishedRequest,
    StrategyPublishedResponse,
)

SNAPSHOT_ACTIVE = "active"
SNAPSHOT_SUPERSEDED = "superseded"
PROPOSAL_PENDING = "pending"
PROPOSAL_ACCEPTED = "accepted"
PROPOSAL_REJECTED = "rejected"


class RoomNotFoundError(Exception):
    """No room for the given id."""


class ProposalNotFoundError(Exception):
    """No proposal for this room."""


class StrategyConflictError(Exception):
    """409: pending exists, version==active, not pending, or publication bound elsewhere."""


@dataclass
class PublishResult:
    response: StrategyPublishedResponse
    http_status: int


def _now() -> datetime:
    return datetime.now(timezone.utc)


def active_snapshot(room: Room) -> StrategySnapshot | None:
    active = [s for s in room.strategy_snapshots if s.status == SNAPSHOT_ACTIVE]
    if not active:
        return None
    active.sort(key=lambda s: s.created_at, reverse=True)
    return active[0]


def pending_proposal(db: Session, room_id: uuid.UUID) -> StrategyProposal | None:
    return db.scalar(
        select(StrategyProposal).where(
            StrategyProposal.room_id == room_id,
            StrategyProposal.status == PROPOSAL_PENDING,
        )
    )


def _load_room(db: Session, room_id: uuid.UUID) -> Room | None:
    return db.scalar(
        select(Room)
        .where(Room.id == room_id)
        .options(selectinload(Room.strategy_snapshots))
    )


def publish_strategy(
    db: Session, body: StrategyPublishedRequest
) -> PublishResult:
    existing = db.scalar(
        select(StrategyProposal).where(
            StrategyProposal.publication_id == body.publication_id
        )
    )
    if existing is not None:
        if existing.room_id != body.room_id:
            raise StrategyConflictError(
                "publication_id already bound to a different room"
            )
        return PublishResult(
            response=StrategyPublishedResponse(
                proposal_id=existing.id,
                room_id=existing.room_id,
                status=PublicationStatus.already_exists,
            ),
            http_status=200,
        )

    room = _load_room(db, body.room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")

    if pending_proposal(db, room.id) is not None:
        raise StrategyConflictError("a pending strategy proposal already exists")

    current = active_snapshot(room)
    if current is not None and current.strategy_version == body.strategy_version:
        raise StrategyConflictError("strategy_version already active")

    proposal = StrategyProposal(
        id=uuid.uuid4(),
        publication_id=body.publication_id,
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
        status=PROPOSAL_PENDING,
    )
    db.add(proposal)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raced = db.scalar(
            select(StrategyProposal).where(
                StrategyProposal.publication_id == body.publication_id
            )
        )
        if raced is not None and raced.room_id == body.room_id:
            return PublishResult(
                response=StrategyPublishedResponse(
                    proposal_id=raced.id,
                    room_id=raced.room_id,
                    status=PublicationStatus.already_exists,
                ),
                http_status=200,
            )
        raise StrategyConflictError("a pending strategy proposal already exists") from exc

    db.refresh(proposal)
    return PublishResult(
        response=StrategyPublishedResponse(
            proposal_id=proposal.id,
            room_id=proposal.room_id,
            status=PublicationStatus.pending,
        ),
        http_status=200,
    )


def _get_pending_proposal(
    db: Session, room_id: uuid.UUID, proposal_id: uuid.UUID
) -> tuple[Room, StrategyProposal]:
    room = _load_room(db, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    proposal = db.get(StrategyProposal, proposal_id)
    if proposal is None or proposal.room_id != room_id:
        raise ProposalNotFoundError("proposal_id does not exist")
    if proposal.status != PROPOSAL_PENDING:
        raise StrategyConflictError("proposal is not pending")
    return room, proposal


def accept_proposal(
    db: Session,
    room_id: uuid.UUID,
    proposal_id: uuid.UUID,
    actor_sub: str,
) -> StrategyDecideResponse:
    room, proposal = _get_pending_proposal(db, room_id, proposal_id)
    current = active_snapshot(room)
    if current is not None:
        current.status = SNAPSHOT_SUPERSEDED
    new_snap = StrategySnapshot(
        id=uuid.uuid4(),
        room_id=room.id,
        strategy_id=proposal.strategy_id,
        strategy_version=proposal.strategy_version,
        strategy_payload=proposal.strategy_payload,
        documents=proposal.documents,
        staffing_intent=proposal.staffing_intent,
        commercial=None,
        status=SNAPSHOT_ACTIVE,
    )
    db.add(new_snap)
    proposal.status = PROPOSAL_ACCEPTED
    proposal.decided_at = _now()
    proposal.decided_by_sub = actor_sub
    db.commit()
    return StrategyDecideResponse(
        proposal_id=proposal.id,
        room_id=room.id,
        decision=StrategyDecision.accepted,
        active_strategy_version=proposal.strategy_version,
    )


def reject_proposal(
    db: Session,
    room_id: uuid.UUID,
    proposal_id: uuid.UUID,
    actor_sub: str,
) -> StrategyDecideResponse:
    room, proposal = _get_pending_proposal(db, room_id, proposal_id)
    current = active_snapshot(room)
    proposal.status = PROPOSAL_REJECTED
    proposal.decided_at = _now()
    proposal.decided_by_sub = actor_sub
    db.commit()
    version = current.strategy_version if current is not None else proposal.strategy_version
    return StrategyDecideResponse(
        proposal_id=proposal.id,
        room_id=room.id,
        decision=StrategyDecision.rejected,
        active_strategy_version=version,
    )
