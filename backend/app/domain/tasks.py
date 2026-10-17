"""C7 room tasks: minimal execution tracker. No roster/assign (C6)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Room, RoomTask
from app.domain.schemas import (
    RoomTaskCompleteRequest,
    RoomTaskCreateRequest,
    RoomTaskListResponse,
    RoomTaskOut,
    TaskStatus,
)

LIST_LIMIT = 100


class RoomNotFoundError(Exception):
    """No room for the given id."""


class TaskNotFoundError(Exception):
    """No task for the given (room_id, task_id)."""


class InvalidTransitionError(Exception):
    """Requested status transition is not allowed."""


def _require_room(db: Session, room_id: uuid.UUID) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    return room


def _task_out(row: RoomTask) -> RoomTaskOut:
    return RoomTaskOut(
        id=row.id,
        room_id=row.room_id,
        title=row.title,
        status=TaskStatus(row.status),
        assignee_sub=row.assignee_sub,
        proof_uri=row.proof_uri,
        proof_note=row.proof_note,
        reviewed_by_sub=row.reviewed_by_sub,
        review_note=row.review_note,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _require_task(db: Session, room_id: uuid.UUID, task_id: uuid.UUID) -> RoomTask:
    row = db.get(RoomTask, task_id)
    if row is None or row.room_id != room_id:
        raise TaskNotFoundError("task_id does not exist in this room")
    return row


def list_tasks(db: Session, room_id: uuid.UUID) -> RoomTaskListResponse:
    room = _require_room(db, room_id)
    rows = list(
        db.scalars(
            select(RoomTask)
            .where(RoomTask.room_id == room.id)
            .order_by(RoomTask.created_at, RoomTask.id)
            .limit(LIST_LIMIT)
        ).all()
    )
    return RoomTaskListResponse(
        room_id=room.id,
        tasks=[_task_out(row) for row in rows],
    )


def create_task(
    db: Session, room_id: uuid.UUID, payload: RoomTaskCreateRequest
) -> RoomTaskOut:
    room = _require_room(db, room_id)
    row = RoomTask(
        id=uuid.uuid4(),
        room_id=room.id,
        title=payload.title,
        status=TaskStatus.todo.value,
        assignee_sub=payload.assignee_sub,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _task_out(row)


def start_task(
    db: Session, room_id: uuid.UUID, task_id: uuid.UUID, actor_sub: str
) -> RoomTaskOut:
    row = _require_task(db, room_id, task_id)
    if row.status != TaskStatus.todo.value:
        raise InvalidTransitionError("only a todo task can be started")
    row.status = TaskStatus.in_progress.value
    if not row.assignee_sub:
        row.assignee_sub = actor_sub
    db.commit()
    db.refresh(row)
    return _task_out(row)


def complete_task(
    db: Session,
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    actor_sub: str,
    payload: RoomTaskCompleteRequest,
) -> RoomTaskOut:
    """in_progress -> submitted with proof (Quality Gate lite, C10)."""
    row = _require_task(db, room_id, task_id)
    if row.status != TaskStatus.in_progress.value:
        raise InvalidTransitionError("only an in_progress task can be completed")
    row.status = TaskStatus.submitted.value
    if not row.assignee_sub:
        row.assignee_sub = actor_sub
    row.proof_uri = payload.proof_uri
    row.proof_note = payload.proof_note
    row.reviewed_by_sub = None
    row.review_note = None
    db.commit()
    db.refresh(row)
    return _task_out(row)


def accept_task(
    db: Session, room_id: uuid.UUID, task_id: uuid.UUID, actor_sub: str
) -> RoomTaskOut:
    """submitted -> done (teamlead accept)."""
    row = _require_task(db, room_id, task_id)
    if row.status != TaskStatus.submitted.value:
        raise InvalidTransitionError("only a submitted task can be accepted")
    row.status = TaskStatus.done.value
    row.reviewed_by_sub = actor_sub
    row.review_note = None
    db.commit()
    db.refresh(row)
    return _task_out(row)


def reject_task(
    db: Session,
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    actor_sub: str,
    review_note: str | None,
) -> RoomTaskOut:
    """submitted -> in_progress (teamlead reject). Proof is kept."""
    row = _require_task(db, room_id, task_id)
    if row.status != TaskStatus.submitted.value:
        raise InvalidTransitionError("only a submitted task can be rejected")
    row.status = TaskStatus.in_progress.value
    row.reviewed_by_sub = actor_sub
    row.review_note = review_note
    db.commit()
    db.refresh(row)
    return _task_out(row)
