"""Room tasks API (C7). Actor: JWT sub when auth on, X-Actor-Sub stub when AUTH_DISABLED=true."""

from __future__ import annotations

import uuid

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.rbac_deps import require_staff, require_task_worker
from app.db.session import get_db
from app.domain.schemas import (
    RoomTaskAssignRequest,
    RoomTaskCompleteRequest,
    RoomTaskCreateRequest,
    RoomTaskListResponse,
    RoomTaskOut,
    RoomTaskRejectRequest,
)
from app.domain.staffing import FreelancerNotInRosterError
from app.domain.tasks import (
    InvalidTransitionError,
    RoomNotFoundError,
    TaskNotFoundError,
    accept_task,
    assign_task,
    complete_task,
    create_task,
    list_tasks,
    reject_task,
    start_task,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["tasks"])


def _map_errors(exc: Exception) -> None:
    if isinstance(exc, (RoomNotFoundError, TaskNotFoundError, FreelancerNotInRosterError)):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, InvalidTransitionError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise exc


@router.get(
    "/{room_id}/tasks",
    response_model=RoomTaskListResponse,
    responses={
        200: {"description": "Tasks of the room"},
        404: {"description": "room_id does not exist"},
    },
)
def get_room_tasks(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
    status: Literal[
        "todo", "in_progress", "submitted", "done", "rejected"
    ]
    | None = Query(default=None),
) -> RoomTaskListResponse:
    try:
        return list_tasks(db, room_id, status=status)
    except RoomNotFoundError as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/tasks",
    response_model=RoomTaskOut,
    status_code=201,
    responses={
        201: {"description": "Task created in todo"},
        404: {"description": "room_id does not exist"},
        422: {"description": "validation or missing X-Actor-Sub"},
    },
)
def post_room_task(
    room_id: uuid.UUID,
    payload: RoomTaskCreateRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_staff),
) -> RoomTaskOut:
    try:
        return create_task(db, room_id, payload)
    except (RoomNotFoundError, FreelancerNotInRosterError) as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/tasks/{task_id}/start",
    response_model=RoomTaskOut,
    responses={
        200: {"description": "todo -> in_progress"},
        404: {"description": "room or task does not exist"},
        409: {"description": "illegal transition"},
        422: {"description": "missing X-Actor-Sub"},
    },
)
def post_start_task(
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(require_task_worker),
) -> RoomTaskOut:
    try:
        return start_task(db, room_id, task_id, actor)
    except (
        RoomNotFoundError,
        TaskNotFoundError,
        FreelancerNotInRosterError,
        InvalidTransitionError,
    ) as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/tasks/{task_id}/assign",
    response_model=RoomTaskOut,
    responses={
        200: {"description": "assignee set on todo/in_progress task"},
        404: {"description": "room/task missing or freelancer_not_in_roster"},
        409: {"description": "illegal status (submitted/done)"},
        422: {"description": "missing X-Actor-Sub"},
    },
)
def post_assign_task(
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: RoomTaskAssignRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_staff),
) -> RoomTaskOut:
    """C15: POST /api/v1/rooms/{room_id}/tasks/{task_id}/assign."""
    try:
        return assign_task(db, room_id, task_id, payload.assignee_sub)
    except (RoomNotFoundError, TaskNotFoundError, FreelancerNotInRosterError) as exc:
        _map_errors(exc)
        raise
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/{room_id}/tasks/{task_id}/complete",
    response_model=RoomTaskOut,
    responses={
        200: {"description": "in_progress -> submitted (proof required)"},
        404: {"description": "room or task does not exist"},
        409: {"description": "illegal transition"},
        422: {"description": "missing proof_uri or missing X-Actor-Sub"},
    },
)
def post_complete_task(
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: RoomTaskCompleteRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_task_worker),
) -> RoomTaskOut:
    try:
        return complete_task(db, room_id, task_id, actor, payload)
    except (RoomNotFoundError, TaskNotFoundError, InvalidTransitionError) as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/tasks/{task_id}/accept",
    response_model=RoomTaskOut,
    responses={
        200: {"description": "submitted -> done"},
        404: {"description": "room or task does not exist"},
        409: {"description": "illegal transition"},
        422: {"description": "missing X-Actor-Sub"},
    },
)
def post_accept_task(
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(require_staff),
) -> RoomTaskOut:
    try:
        return accept_task(db, room_id, task_id, actor)
    except (RoomNotFoundError, TaskNotFoundError, InvalidTransitionError) as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/tasks/{task_id}/reject",
    response_model=RoomTaskOut,
    responses={
        200: {"description": "submitted -> in_progress (proof kept)"},
        404: {"description": "room or task does not exist"},
        409: {"description": "illegal transition"},
        422: {"description": "missing X-Actor-Sub"},
    },
)
def post_reject_task(
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(require_staff),
    payload: RoomTaskRejectRequest | None = None,
) -> RoomTaskOut:
    review_note = payload.review_note if payload is not None else None
    try:
        return reject_task(db, room_id, task_id, actor, review_note)
    except (RoomNotFoundError, TaskNotFoundError, InvalidTransitionError) as exc:
        _map_errors(exc)
        raise
