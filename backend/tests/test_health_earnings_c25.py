"""C25: earnings блок в Room Health snapshot (GET + publish)."""

from __future__ import annotations

from decimal import Decimal

from app.config import settings
from app.db.models import OutboxMessage
from sqlalchemy import select

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


def _create(client, room_id: str, title: str, **extra) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": title, **extra},
        headers=ACTOR,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _start(client, room_id: str, task_id: str) -> dict:
    _upsert(client, "freelancer-demo-sub", "Alice")
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=FREELANCER
    )
    assert r.status_code == 200, r.text
    return r.json()


def _complete(client, room_id: str, task_id: str) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=PROOF,
        headers=FREELANCER,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _accept(client, room_id: str, task_id: str) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/accept", headers=ACTOR
    )
    assert r.status_code == 200, r.text
    return r.json()


def _get_health(client, room_id: str):
    return client.get(f"/api/v1/rooms/{room_id}/health")


def _publish(client, room_id: str):
    return client.post(f"/internal/v1/rooms/{room_id}/health/publish")


def _outbox_health_rows(db_session):
    return list(
        db_session.scalars(
            select(OutboxMessage).where(
                OutboxMessage.event_type == "RoomHealthSnapshot"
            )
        ).all()
    )


def test_empty_room_health_earnings_zeros(client, sale_payload):
    """DoD #1: пустая комната → earnings zeros (не 404)."""
    room_id = _handoff(client, sale_payload)
    r = _get_health(client, room_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["earnings"] == {
        "total_amount": "0.00",
        "currency": settings.earnings_currency,
        "entries_count": 0,
    }


def test_accept_twice_earnings_total(client, sale_payload, db_session):
    """DoD #2: accept×2 с assignee → total 20.00, count 2 (при default 10)."""
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")

    task1 = _create(client, room_id, "Task 1", assignee_sub="freelancer-demo-sub")[
        "id"
    ]
    _start(client, room_id, task1)
    _complete(client, room_id, task1)
    _accept(client, room_id, task1)

    task2 = _create(client, room_id, "Task 2", assignee_sub="freelancer-demo-sub")[
        "id"
    ]
    _start(client, room_id, task2)
    _complete(client, room_id, task2)
    _accept(client, room_id, task2)

    body = _get_health(client, room_id).json()
    expected_total = str(settings.earnings_task_amount * 2)
    assert body["earnings"]["total_amount"] == expected_total
    assert body["earnings"]["currency"] == settings.earnings_currency
    assert body["earnings"]["entries_count"] == 2


def test_publish_payload_contains_earnings(client, sale_payload, db_session):
    """DoD #3: publish payload содержит earnings."""
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")

    task = _create(client, room_id, "Task 1", assignee_sub="freelancer-demo-sub")[
        "id"
    ]
    _start(client, room_id, task)
    _complete(client, room_id, task)
    _accept(client, room_id, task)

    r = _publish(client, room_id)
    assert r.status_code == 200, r.text
    payload = r.json()["snapshot"]["earnings"]
    assert payload["entries_count"] == 1
    assert payload["total_amount"] == str(settings.earnings_task_amount)
    assert payload["currency"] == settings.earnings_currency

    rows = _outbox_health_rows(db_session)
    assert len(rows) == 1
    assert rows[0].payload["earnings"]["entries_count"] == 1


def test_health_regression_counts_slots_tasks_leads(client, sale_payload):
    """DoD #4: регрессия C13 — slots/tasks/leads подсчёты не сломались."""
    room_id = _handoff(client, sale_payload)
    body = _get_health(client, room_id).json()
    assert body["slots"] == {"total": 0, "open": 0, "filled": 0, "cancelled": 0}
    assert body["tasks"] == {"todo": 0, "in_progress": 0, "submitted": 0, "done": 0}
    assert body["leads"] == {"total": 0, "hot": 0, "handed_to_crm": 0}
    assert body["earnings"]["entries_count"] == 0
    assert Decimal(body["earnings"]["total_amount"]) == Decimal("0.00")


def test_earnings_list_matches_health(client, sale_payload):
    """C36 must-fix #2: Earned list total/count совпадает с health earnings."""
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")

    for title in ("Task 1", "Task 2"):
        task = _create(
            client, room_id, title, assignee_sub="freelancer-demo-sub"
        )["id"]
        _start(client, room_id, task)
        _complete(client, room_id, task)
        _accept(client, room_id, task)

    earned = client.get(f"/api/v1/rooms/{room_id}/earnings")
    assert earned.status_code == 200, earned.text
    earned_body = earned.json()
    health_body = _get_health(client, room_id).json()

    assert earned_body["total_amount"] == health_body["earnings"]["total_amount"]
    assert earned_body["currency"] == health_body["earnings"]["currency"]
    assert len(earned_body["entries"]) == health_body["earnings"]["entries_count"]
