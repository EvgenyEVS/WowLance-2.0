"""Staffing slots API (C4). Open until Gateway/JWT; locked rooms return 403."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.schemas import StaffingMaterializeResponse, StaffingSlotsListResponse
from app.domain.staffing import (
    RoomNotFoundError,
    StaffingLockedError,
    list_slots,
    materialize_slots,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["slots"])


def _map_errors(exc: Exception) -> None:
    if isinstance(exc, RoomNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, StaffingLockedError):
        raise HTTPException(status_code=403, detail="staffing_locked") from exc
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
