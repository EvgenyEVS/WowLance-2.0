"""Staffing slots API (C4) + assign (C6) + unassign/reassign (C12). Locked = 403."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_actor_sub
from app.db.session import get_db
from app.domain.schemas import (
    SlotAssignRequest,
    SlotAssignResponse,
    SlotMatchResponse,
    SlotReassignResponse,
    SlotUnassignResponse,
    StaffingMaterializeResponse,
    StaffingSlotsListResponse,
)
from app.domain.staffing import (
    AlreadySeatedError,
    FreelancerNotInRosterError,
    RoomNotFoundError,
    SlotAlreadyFilledError,
    SlotNotFilledError,
    SlotNotFoundError,
    StaffingLockedError,
    assign_slot,
    list_slots,
    materialize_slots,
    reassign_slot,
    unassign_slot,
)
from app.domain.matching import DEFAULT_LIMIT, SlotNotOpenError, match_candidates

router = APIRouter(prefix="/api/v1/rooms", tags=["slots"])


def _map_errors(exc: Exception) -> None:
    if isinstance(exc, (RoomNotFoundError, SlotNotFoundError, FreelancerNotInRosterError)):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, StaffingLockedError):
        raise HTTPException(status_code=403, detail="staffing_locked") from exc
    if isinstance(exc, (SlotAlreadyFilledError, AlreadySeatedError)):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, SlotNotFilledError):
        raise HTTPException(status_code=409, detail="slot_not_filled") from exc
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


@router.get(
    "/{room_id}/slots/{slot_id}/match",
    response_model=SlotMatchResponse,
    responses={
        200: {"description": "shortlist of candidates for the open slot"},
        403: {"description": "staffing_locked"},
        404: {"description": "room_id does not exist or slot not in this room"},
        409: {"description": "slot_not_open"},
        422: {"description": "validation failed (limit out of range)"},
    },
)
def get_slot_match(
    room_id: uuid.UUID,
    slot_id: uuid.UUID,
    limit: int = DEFAULT_LIMIT,
    db: Session = Depends(get_db),
) -> SlotMatchResponse:
    try:
        return match_candidates(db, room_id, slot_id, limit)
    except (RoomNotFoundError, SlotNotFoundError) as exc:
        _map_errors(exc)
        raise
    except StaffingLockedError as exc:
        _map_errors(exc)
        raise
    except SlotNotOpenError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


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
    actor: str = Depends(get_actor_sub),
) -> SlotAssignResponse:
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


@router.post(
    "/{room_id}/slots/{slot_id}/unassign",
    response_model=SlotUnassignResponse,
    responses={
        200: {"description": "slot freed: filled -> open"},
        403: {"description": "staffing_locked"},
        404: {"description": "room/slot missing"},
        409: {"description": "slot_not_filled"},
        422: {"description": "validation or missing X-Actor-Sub"},
    },
)
def post_unassign_slot(
    room_id: uuid.UUID,
    slot_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor_sub),
) -> SlotUnassignResponse:
    try:
        return unassign_slot(db, room_id, slot_id)
    except (
        RoomNotFoundError,
        StaffingLockedError,
        SlotNotFoundError,
        SlotNotFilledError,
    ) as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/slots/{slot_id}/reassign",
    response_model=SlotReassignResponse,
    responses={
        200: {"description": "reassigned or already_assigned (idempotent)"},
        403: {"description": "staffing_locked"},
        404: {"description": "room/slot missing or freelancer_not_in_roster"},
        409: {"description": "slot_not_filled or already_seated"},
        422: {"description": "validation or missing X-Actor-Sub"},
    },
)
def post_reassign_slot(
    room_id: uuid.UUID,
    slot_id: uuid.UUID,
    payload: SlotAssignRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor_sub),
) -> SlotReassignResponse:
    try:
        return reassign_slot(db, room_id, slot_id, payload.freelancer_sub)
    except (
        RoomNotFoundError,
        StaffingLockedError,
        SlotNotFoundError,
        FreelancerNotInRosterError,
        SlotNotFilledError,
        AlreadySeatedError,
    ) as exc:
        _map_errors(exc)
        raise
