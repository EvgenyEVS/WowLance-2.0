"""C16 stub earnings ledger: начисления за принятые задачи (accept -> done).

Вызывается из `accept_task` в той же транзакции, что и переход в `done`.
Живой Billing / выплаты / налоги — не в C16.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import EarningsEntry, RoomTask


class TaskNotFoundError(Exception):
    """No task for the given (room_id, task_id)."""


def _require_task(
    db: Session, room_id: uuid.UUID, task_id: uuid.UUID
) -> RoomTask:
    row = db.get(RoomTask, task_id)
    if row is None or row.room_id != room_id:
        raise TaskNotFoundError("task_id does not exist in this room")
    return row


def record_for_accepted_task(
    db: Session,
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    freelancer_sub: str,
) -> EarningsEntry | None:
    """C16: create earnings entry for an accepted task.

    Idempotent by UNIQUE task_id: repeat call returns the existing entry
    (accept of an already-done task is impossible, but UNIQUE guards anyway).
    Returns None if assignee_sub is empty (no earnings without a freelancer).
    """
    if not freelancer_sub:
        return None

    _require_task(db, room_id, task_id)

    existing = db.scalar(
        select(EarningsEntry).where(EarningsEntry.task_id == task_id)
    )
    if existing is not None:
        return existing

    entry = EarningsEntry(
        id=uuid.uuid4(),
        room_id=room_id,
        task_id=task_id,
        freelancer_sub=freelancer_sub,
        amount=settings.earnings_task_amount,
        currency=settings.earnings_currency,
        source="task_accepted",
    )
    db.add(entry)
    db.flush()
    return entry


def list_room_earnings(
    db: Session, room_id: uuid.UUID
) -> tuple[list[EarningsEntry], Decimal, str]:
    """Return (entries, total_amount, currency) for a room."""
    rows = list(
        db.scalars(
            select(EarningsEntry)
            .where(EarningsEntry.room_id == room_id)
            .order_by(EarningsEntry.created_at, EarningsEntry.id)
        ).all()
    )
    total = sum((e.amount for e in rows), Decimal("0")).quantize(
        Decimal("0.01")
    )
    currency = settings.earnings_currency
    return rows, total, currency
