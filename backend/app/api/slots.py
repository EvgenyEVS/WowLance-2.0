"""Staffing slots API (C4) + assign (C6). Open until Gateway/JWT; locked = 403."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.schemas import (
    SlotAssignRequest,
    SlotAssignResponse,
    StaffingMaterializeResponse,
    StaffingSlotsListResponse,
)
from app.domain.staffing import (
    AlreadySeatedError,
    FreelancerNotInRosterError,
    RoomNotFoundError,
    SlotAlreadyFilledError,
    SlotNotFoundError,
    StaffingLockedError,
    assign_slot,
    list_slots,
    materialize_slots,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["slots"])


def _actor_sub(x_actor_sub: str | None) -> str:
    if x_actor_sub is None or not x_actor_sub.strip():
        raise HTTPException(status_code=422, detail="X-Actor-Sub header is required")
    return x_actor_sub.strip()


def _map_errors(exc: Exception) -> None:
    if isinstance(exc, (RoomNotFoundError, SlotNotFoundError, FreelancerNotInRosterError)):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, StaffingLockedError):
        raise HTTPException(status_code=403, detail="staffing_locked") from exc
    if isinstance(exc, (SlotAlreadyFilledError, AlreadySeatedError)):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise exc


@router.get(
    "/{room_id}/slots",
    response_model=StaffingSlotsListResponse,
    responses={
        200: {"description": "Slots for an unlocked room"},
        403: {"description": "staffing_locked"},
        404: {"description": "room_id does not exist"},
    },
)
def get_room_slots(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> StaffingSlotsListResponse:
    try:
        return list_slots(db, room_id)
    except (RoomNotFoundError, StaffingLockedError) as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/slots/materialize",
    response_model=StaffingMaterializeResponse,
    responses={
        200: {"description": "materialized or already_materialized"},
        403: {"description": "staffing_locked"},
        404: {"description": "room_id does not exist"},
    },
)
def post_materialize_slots(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> StaffingMaterializeResponse:
    try:
        return materialize_slots(db, room_id)
    except (RoomNotFoundError, StaffingLockedError) as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/slots/{slot_id}/assign",
    response_model=SlotAssignResponse,
    responses={
        200: {"description": "assigned or already_assigned (idempotent)"},
        403: {"description": "staffing_locked"},
        404: {"description": "room/slot missing or freelancer_not_in_roster"},
        409: {"description": "slot_already_filled or already_seated"},
        422: {"description": "validation or missing X-Actor-Sub"},
    },
)
def post_assign_slot(
    room_id: uuid.UUID,
    slot_id: uuid.UUID,
    payload: SlotAssignRequest,
    db: Session = Depends(get_db),
    x_actor_sub: str | None = Header(default=None, alias="X-Actor-Sub"),
) -> SlotAssignResponse:
    _actor_sub(x_actor_sub)
    try:
        return assign_slot(db, room_id, slot_id, payload.freelancer_sub)
    except (
        RoomNotFoundError,
        StaffingLockedError,
        SlotNotFoundError,
        FreelancerNotInRosterError,
        SlotAlreadyFilledError,
        AlreadySeatedError,
    ) as exc:
        _map_errors(exc)
        raise
