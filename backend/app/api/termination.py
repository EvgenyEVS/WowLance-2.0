"""C17 termination API: POST …/terminate + GET …/terminations."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.rbac_deps import require_staff
from app.db.session import get_db
from app.domain.schemas import (
    RoomTerminationListResponse,
    RoomTerminationOut,
    TerminateMemberRequest,
    TerminateMemberResponse,
)
from app.domain.termination import (
    NotSeatedError,
    RoomNotFoundError,
    SlotNotFilledError,
    list_terminations,
    terminate_member,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["termination"])


def _map_errors(exc: Exception) -> None:
    if isinstance(exc, (RoomNotFoundError, NotSeatedError)):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, SlotNotFilledError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise exc


@router.post(
    "/{room_id}/members/{freelancer_sub}/terminate",
    response_model=TerminateMemberResponse,
    responses={
        200: {"description": "member terminated, slot freed, outbox written"},
        404: {"description": "room missing or freelancer not seated (not_seated)"},
        409: {"description": "explicit slot_id not filled (slot_not_filled)"},
        422: {"description": "validation or missing reason / missing X-Actor-Sub"},
    },
)
def post_terminate_member(
    room_id: uuid.UUID,
    freelancer_sub: str,
    payload: TerminateMemberRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_staff),
) -> TerminateMemberResponse:
    """C17: POST /api/v1/rooms/{room_id}/members/{freelancer_sub}/terminate."""
    try:
        result = terminate_member(
            db=db,
            room_id=room_id,
            freelancer_sub=freelancer_sub,
            reason=payload.reason,
            terminated_by_sub=actor,
            slot_id=payload.slot_id,
        )
    except (RoomNotFoundError, NotSeatedError, SlotNotFilledError) as exc:
        _map_errors(exc)
        raise
    return TerminateMemberResponse(
        status=result["status"],
        freelancer_sub=result["freelancer_sub"],
        slot_ids=result["slot_ids"],
    )


@router.get(
    "/{room_id}/terminations",
    response_model=RoomTerminationListResponse,
    responses={
        200: {"description": "termination journal for the room"},
        404: {"description": "room_id does not exist"},
    },
)
def get_room_terminations(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RoomTerminationListResponse:
    """GET /api/v1/rooms/{room_id}/terminations — termination journal list."""
    try:
        rows = list_terminations(db, room_id)
    except RoomNotFoundError as exc:
        _map_errors(exc)
        raise
    return RoomTerminationListResponse(
        room_id=room_id,
        terminations=[
            RoomTerminationOut(
                id=r.id,
                room_id=r.room_id,
                freelancer_sub=r.freelancer_sub,
                reason=r.reason,
                terminated_by_sub=r.terminated_by_sub,
                slot_ids=[uuid.UUID(s) if isinstance(s, str) else s for s in r.slot_ids],
                created_at=r.created_at,
            )
            for r in rows
        ],
    )
