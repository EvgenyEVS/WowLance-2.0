"""C7 room tasks: minimal execution tracker + C15 assignee из roster."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import FreelancerRoster, OutboxMessage, Room, RoomTask
from app.domain.earnings import record_for_accepted_task
from app.domain.schemas import (
    RoomTaskAssignRequest,
    RoomTaskCompleteRequest,
    RoomTaskCreateRequest,
    RoomTaskListResponse,
    RoomTaskOut,
    TaskStatus,
)
from app.domain.staffing import FreelancerNotInRosterError

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


def _require_roster(db: Session, sub: str) -> None:
    """404 freelancer_not_in_roster when sub is not in the local roster."""
    if db.get(FreelancerRoster, sub) is None:
        raise FreelancerNotInRosterError("freelancer_not_in_roster")


TASK_ACCEPTED_EVENT = "TaskAccepted"


def _task_accepted_outbox(
    db: Session,
    task_id: uuid.UUID,
    room_id: uuid.UUID,
    reviewed_by_sub: str,
    assignee_sub: str | None,
    proof_uri: str | None,
    accepted_at: datetime,
    earnings_amount=None,
    earnings_currency: str | None = None,
) -> None:
    """C24: outbox TaskAccepted для принятой задачи (submitted -> done).

    Идемпотентно по task_id: повторный accept невозможен (уже done),
    но UNIQUE idempotency_key страхует от дублей. Создаётся в той же
    транзакции, что и статус done + earnings row.
    """
    key = f"task:{task_id}:TaskAccepted"
    existing = db.scalar(
        select(OutboxMessage).where(OutboxMessage.idempotency_key == key)
    )
    if existing is not None:
        return
    payload = {
        "room_id": str(room_id),
        "task_id": str(task_id),
        "assignee_sub": assignee_sub,
        "reviewed_by_sub": reviewed_by_sub,
        "proof_uri": proof_uri,
        "accepted_at": accepted_at.isoformat(),
    }
    if earnings_amount is not None:
        payload["amount"] = str(earnings_amount)
        payload["currency"] = earnings_currency
    db.add(
        OutboxMessage(
            id=uuid.uuid4(),
            event_type=TASK_ACCEPTED_EVENT,
            idempotency_key=key,
            payload=payload,
            status="sent",
            sent_at=accepted_at,
        )
    )


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


def list_tasks(
    db: Session, room_id: uuid.UUID, status: str | None = None
) -> RoomTaskListResponse:
    room = _require_room(db, room_id)
    query = select(RoomTask).where(RoomTask.room_id == room.id)
    if status == "rejected":
        query = query.where(
            RoomTask.status == TaskStatus.in_progress.value,
            RoomTask.review_note.is_not(None),
        )
    elif status:
        query = query.where(RoomTask.status == status)
    query = (
        query.order_by(
            case((RoomTask.status == TaskStatus.submitted.value, 0), else_=1),
            RoomTask.created_at,
            RoomTask.id,
        ).limit(LIST_LIMIT)
    )
    rows = list(db.scalars(query).all())
    return RoomTaskListResponse(
        room_id=room.id,
        tasks=[_task_out(row) for row in rows],
    )


def create_task(
    db: Session, room_id: uuid.UUID, payload: RoomTaskCreateRequest
) -> RoomTaskOut:
    room = _require_room(db, room_id)
    if payload.assignee_sub:
        _require_roster(db, payload.assignee_sub)
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
        _require_roster(db, actor_sub)
    db.commit()
    db.refresh(row)
    return _task_out(row)


def assign_task(
    db: Session, room_id: uuid.UUID, task_id: uuid.UUID, assignee_sub: str
) -> RoomTaskOut:
    """C15: set assignee on a todo/in_progress task; sub must be in roster."""
    row = _require_task(db, room_id, task_id)
    if row.status not in (TaskStatus.todo.value, TaskStatus.in_progress.value):
        raise InvalidTransitionError(
            "assignment only on todo or in_progress tasks"
        )
    _require_roster(db, assignee_sub)
    row.assignee_sub = assignee_sub
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
    """submitted -> done (teamlead accept). C16: record earnings for assignee.
    C24: outbox TaskAccepted в той же транзакции, что и done + earnings."""
    row = _require_task(db, room_id, task_id)
    if row.status != TaskStatus.submitted.value:
        raise InvalidTransitionError("only a submitted task can be accepted")
    row.status = TaskStatus.done.value
    row.reviewed_by_sub = actor_sub
    row.review_note = None
    accepted_at = datetime.now(timezone.utc)
    earnings_entry = None
    if row.assignee_sub:
        earnings_entry = record_for_accepted_task(
            db, room_id, task_id, row.assignee_sub
        )
    _task_accepted_outbox(
        db,
        task_id=task_id,
        room_id=room_id,
        reviewed_by_sub=actor_sub,
        assignee_sub=row.assignee_sub,
        proof_uri=row.proof_uri,
        accepted_at=accepted_at,
        earnings_amount=earnings_entry.amount if earnings_entry else None,
        earnings_currency=earnings_entry.currency if earnings_entry else None,
    )
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
