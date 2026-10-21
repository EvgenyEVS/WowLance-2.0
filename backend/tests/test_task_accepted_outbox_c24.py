"""C24 Outbox TaskAccepted при accept задачи (submitted -> done)."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.models import EarningsEntry, OutboxMessage

ACTOR = {"X-Actor-Sub": "teamlead-demo-sub"}
FREELANCER = {"X-Actor-Sub": "freelancer-demo-sub"}
PROOF = {"proof_uri": "https://example.com/proof.txt"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _upsert(client, sub: str, name: str = "Demo Freelancer") -> None:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name},
    )
    assert r.status_code == 200, r.text


def _create(client, room_id: str, title: str = "Call 20 leads", **extra) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": title, **extra},
        headers=ACTOR,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _start(client, room_id: str, task_id: str, headers=FREELANCER) -> dict:
    _upsert(client, headers.get("X-Actor-Sub", ""))
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=headers
    )
    assert r.status_code == 200, r.text
    return r.json()


def _complete(client, room_id: str, task_id: str, headers=FREELANCER) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=PROOF,
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _accept(client, room_id: str, task_id: str):
    return client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/accept", headers=ACTOR
    )


def _outbox_rows(db_session, event_type: str):
    return list(
        db_session.scalars(
            select(OutboxMessage).where(OutboxMessage.event_type == event_type)
        ).all()
    )


def _earnings_rows(db_session, task_id):
    return list(
        db_session.scalars(
            select(EarningsEntry).where(EarningsEntry.task_id == task_id)
        ).all()
    )


def test_accept_creates_task_accepted_outbox(client, sale_payload, db_session):
    """DoD #1: Accept → 1 outbox TaskAccepted, payload.task_id совпадает."""
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    _complete(client, room_id, task_id)

    r = _accept(client, room_id, task_id)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "done"
    assert r.json()["reviewed_by_sub"] == ACTOR["X-Actor-Sub"]

    rows = _outbox_rows(db_session, "TaskAccepted")
    assert len(rows) == 1
    assert rows[0].status == "sent"
    assert rows[0].idempotency_key == f"task:{task_id}:TaskAccepted"
    assert rows[0].payload["task_id"] == str(task_id)
    assert rows[0].payload["room_id"] == room_id
    assert rows[0].payload["reviewed_by_sub"] == ACTOR["X-Actor-Sub"]
    assert rows[0].payload["proof_uri"] == PROOF["proof_uri"]
    assert rows[0].sent_at is not None


def test_reject_no_task_accepted_outbox(client, sale_payload, db_session):
    """DoD #2: Reject → 0 TaskAccepted (нет outbox на reject)."""
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    _complete(client, room_id, task_id)

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/reject",
        headers=ACTOR,
        json={"review_note": "needs rework"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "in_progress"

    rows = _outbox_rows(db_session, "TaskAccepted")
    assert len(rows) == 0


def test_accept_with_assignee_earnings_and_outbox_one_transaction(
    client, sale_payload, db_session
):
    """DoD #3: Earnings + TaskAccepted в одной транзакции (оба есть после accept с assignee)."""
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    task_id = _create(client, room_id, assignee_sub="f-1")["id"]
    _start(client, room_id, task_id, headers={"X-Actor-Sub": "f-1"})
    _complete(client, room_id, task_id, headers={"X-Actor-Sub": "f-1"})

    r = _accept(client, room_id, task_id)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "done"

    earnings = _earnings_rows(db_session, task_id)
    assert len(earnings) == 1
    assert earnings[0].freelancer_sub == "f-1"
    assert earnings[0].source == "task_accepted"

    rows = _outbox_rows(db_session, "TaskAccepted")
    assert len(rows) == 1
    assert rows[0].payload["assignee_sub"] == "f-1"
    assert rows[0].payload["amount"] is not None
    assert rows[0].payload["currency"] is not None


def test_accept_regression_status_transition(client, sale_payload, db_session):
    """DoD #4: accept не ломает существующие переходы (QG регрессия)."""
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    _complete(client, room_id, task_id)

    r = _accept(client, room_id, task_id)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "done"

    # Повторный accept невозможен (уже done) → 409.
    r2 = _accept(client, room_id, task_id)
    assert r2.status_code == 409, r2.text

    # Outbox не дублируется.
    rows = _outbox_rows(db_session, "TaskAccepted")
    assert len(rows) == 1
