"""Accept/Reject a pending strategy proposal. Actor: JWT sub, X-Actor-Sub only when AUTH_DISABLED=true."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_actor_sub
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


@router.post(
    "/{room_id}/strategy-proposals/{proposal_id}/accept",
    response_model=StrategyDecideResponse,
)
def post_accept_proposal(
    room_id: uuid.UUID,
    proposal_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor_sub),
) -> StrategyDecideResponse:
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
    actor: str = Depends(get_actor_sub),
) -> StrategyDecideResponse:
    try:
        return reject_proposal(db, room_id, proposal_id, actor)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProposalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StrategyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
