"""Internal StrategyPublished endpoint (open until Gateway/JWT)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.schemas import StrategyPublishedRequest, StrategyPublishedResponse
from app.domain.strategy_accept import (
    RoomNotFoundError,
    StrategyConflictError,
    publish_strategy,
)
from app.stub_log import log_stub

router = APIRouter(prefix="/internal/v1", tags=["strategy-publications"])


@router.post(
    "/strategy-publications",
    response_model=StrategyPublishedResponse,
    responses={
        200: {"description": "pending or already_exists"},
        404: {"description": "room_id does not exist"},
        409: {"description": "conflict"},
        422: {"description": "validation failed"},
    },
)
def create_strategy_publication(
    body: StrategyPublishedRequest,
    db: Session = Depends(get_db),
) -> StrategyPublishedResponse:
    try:
        result = publish_strategy(db, body)
    except RoomNotFoundError as exc:
        log_stub(
            "strategy_published",
            "not_found",
            room_id=body.room_id,
            strategy_id=body.strategy_id,
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StrategyConflictError as exc:
        log_stub(
            "strategy_published",
            "conflict",
            room_id=body.room_id,
            strategy_id=body.strategy_id,
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    log_stub(
        "strategy_published",
        result.response.status.value,
        room_id=body.room_id,
        strategy_id=body.strategy_id,
        proposal_id=result.response.proposal_id,
    )
    return result.response
