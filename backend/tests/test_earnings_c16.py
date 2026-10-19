"""C16 earnings stub: начисления за accept->done, список по комнате."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.config import settings

ACTOR = {"X-Actor-Sub": "teamlead-demo-sub"}
FREELANCER = {"X-Actor-Sub": "freelancer-demo-sub"}
PROOF = {"proof_uri": "https://example.com/proof.txt"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _upsert(client, sub: str, name: str = "Demo Freelancer") -> dict:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _create(client, room_id: str, title: str = "Call 20 leads", **extra) -> dict:
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


def _list_earnings(client, room_id: str):
    return client.get(f"/api/v1/rooms/{room_id}/earnings")


def test_accept_with_assignee_creates_earnings(client, sale_payload, db_session):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")
    task_id = _create(client, room_id, assignee_sub="freelancer-demo-sub")["id"]

    _start(client, room_id, task_id)
    _complete(client, room_id, task_id)
    _accept(client, room_id, task_id)

    r = _list_earnings(client, room_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["room_id"] == room_id
    assert body["currency"] == settings.earnings_currency
    assert body["total_amount"] == str(settings.earnings_task_amount)
    assert len(body["entries"]) == 1
    entry = body["entries"][0]
    assert entry["task_id"] == task_id
    assert entry["freelancer_sub"] == "freelancer-demo-sub"
    assert entry["amount"] == str(settings.earnings_task_amount)
    assert entry["source"] == "task_accepted"


def test_accept_without_explicit_assignee_still_earns(client, sale_payload):
    """Start заполняет assignee из актера → начисление есть."""
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")
    task_id = _create(client, room_id)["id"]  # no assignee_sub on create

    _start(client, room_id, task_id)  # fills assignee from actor
    _complete(client, room_id, task_id)
    _accept(client, room_id, task_id)

    r = _list_earnings(client, room_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_amount"] == str(settings.earnings_task_amount)
    assert len(body["entries"]) == 1
    assert body["entries"][0]["freelancer_sub"] == "freelancer-demo-sub"


def test_list_room_earnings_total_and_entries(client, sale_payload, db_session):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")

    # two accepted tasks
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

    r = _list_earnings(client, room_id)
    assert r.status_code == 200, r.text
    body = r.json()
    expected_total = str(settings.earnings_task_amount * 2)
    assert body["total_amount"] == expected_total
    assert len(body["entries"]) == 2
    task_ids = {e["task_id"] for e in body["entries"]}
    assert task_ids == {task1, task2}


def test_reject_does_not_create_earnings(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")
    task_id = _create(
        client, room_id, assignee_sub="freelancer-demo-sub"
    )["id"]

    _start(client, room_id, task_id)
    _complete(client, room_id, task_id)

    # reject -> back to in_progress, no earnings
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/reject", headers=ACTOR
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "in_progress"

    earnings = _list_earnings(client, room_id)
    assert earnings.status_code == 200
    assert earnings.json()["total_amount"] == "0.00"
    assert earnings.json()["entries"] == []


def test_earnings_unknown_room_404(client):
    r = _list_earnings(client, str(uuid.uuid4()))
    assert r.status_code == 404, r.text


def test_earnings_amount_matches_stub_setting(client, sale_payload):
    """Earnings amount equals EARNINGS_TASK_AMOUNT from settings."""
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")
    task_id = _create(
        client, room_id, assignee_sub="freelancer-demo-sub"
    )["id"]

    _start(client, room_id, task_id)
    _complete(client, room_id, task_id)
    _accept(client, room_id, task_id)

    earnings = _list_earnings(client, room_id)
    assert earnings.status_code == 200
    entry = earnings.json()["entries"][0]
    assert entry["amount"] == str(settings.earnings_task_amount)
    assert Decimal(entry["amount"]) == settings.earnings_task_amount
