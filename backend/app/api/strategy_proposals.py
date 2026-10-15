"""Accept/Reject a pending strategy proposal. Requires X-Actor-Sub stub."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.schemas import StrategyDecideResponse
from app.domain.strategy_accept import (
    ProposalNotFoundError,
    RoomNotFoundError,
    StrategyConflictError,
    accept_proposal,
    reject_proposal,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["strategy-proposals"])


def _actor_sub(x_actor_sub: str | None) -> str:
    if x_actor_sub is None or not x_actor_sub.strip():
        raise HTTPException(status_code=422, detail="X-Actor-Sub header is required")
    return x_actor_sub.strip()


@router.post(
    "/{room_id}/strategy-proposals/{proposal_id}/accept",
    response_model=StrategyDecideResponse,
)
def post_accept_proposal(
    room_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    x_actor_sub: str | None = Header(default=None, alias="X-Actor-Sub"),
) -> StrategyDecideResponse:
    actor = _actor_sub(x_actor_sub)
    try:
        return accept_proposal(db, room_id, proposal_id, actor)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StrategyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{room_id}/strategy-proposals/{proposal_id}/reject",
    response_model=StrategyDecideResponse,
)
def post_reject_proposal(
    room_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    x_actor_sub: str | None = Header(default=None, alias="X-Actor-Sub"),
) -> StrategyDecideResponse:
    actor = _actor_sub(x_actor_sub)
    try:
        return reject_proposal(db, room_id, proposal_id, actor)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StrategyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
