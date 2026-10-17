"""C13 room health: aggregates, publish outbox, error codes, regression."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.models import OutboxMessage

ACTOR = {"X-Actor-Sub": "founder-demo-sub"}
ACTOR_TASK = {"X-Actor-Sub": "freelancer-demo-sub"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _unlock(client, room_id: str) -> None:
    r = client.post(
        "/internal/v1/entitlements",
        json={
            "entitlement_id": str(uuid.uuid4()),
            "room_id": room_id,
            "source": "stub",
        },
    )
    assert r.status_code == 200, r.text


def _materialize(client, room_id: str) -> list[dict]:
    r = client.post(f"/api/v1/rooms/{room_id}/slots/materialize")
    assert r.status_code == 200, r.text
    return r.json()["slots"]


def _upsert(client, sub: str, name: str = "Demo Freelancer") -> dict:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _assign(client, room_id: str, slot_id: str, sub: str) -> object:
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/assign",
        json={"freelancer_sub": sub},
        headers={"X-Actor-Sub": "teamlead-demo-sub"},
    )


def _get_health(client, room_id: str):
    return client.get(f"/api/v1/rooms/{room_id}/health")


def _publish(client, room_id: str):
    return client.post(f"/internal/v1/rooms/{room_id}/health/publish")


def test_empty_room_health_is_all_zeros(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    r = _get_health(client, room_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["room_id"] == room_id
    assert body["room"]["room_type"] == "sale"
    assert body["room"]["staffing_unlocked"] is False
    assert body["room"]["strategy_id"]
    assert body["room"]["strategy_version"]
    assert body["slots"] == {"total": 0, "open": 0, "filled": 0, "cancelled": 0}
    assert body["tasks"] == {"todo": 0, "in_progress": 0, "submitted": 0, "done": 0}
    assert body["leads"] == {"total": 0, "hot": 0, "handed_to_crm": 0}
    assert body["captured_at"]


def test_health_reflects_slots_after_materialize_and_assign(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    slots = _materialize(client, room_id)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    body = _get_health(client, room_id).json()
    assert body["room"]["staffing_unlocked"] is True
    assert body["slots"]["total"] == 2
    assert body["slots"]["filled"] == 1
    assert body["slots"]["open"] == 1


def test_health_counts_tasks_by_status(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    created = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": "Draft offer"},
        headers=ACTOR_TASK,
    )
    assert created.status_code in (200, 201), created.text
    task_id = created.json()["id"]

    started = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=ACTOR_TASK
    )
    assert started.status_code == 200, started.text

    body = _get_health(client, room_id).json()
    assert body["tasks"]["in_progress"] == 1
    assert body["tasks"]["submitted"] == 0

    completed = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json={"proof_uri": "s3://proof/1", "proof_note": "draft"},
        headers=ACTOR_TASK,
    )
    assert completed.status_code == 200, completed.text

    body = _get_health(client, room_id).json()
    assert body["tasks"]["submitted"] == 1
    assert body["tasks"]["in_progress"] == 0


def test_health_counts_leads(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    created = client.post(
        f"/api/v1/rooms/{room_id}/leads",
        json={"title": "Warm intro", "contact_name": "Jane"},
        headers=ACTOR,
    )
    assert created.status_code in (200, 201), created.text
    lead_id = created.json()["id"]

    hot = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot", headers=ACTOR
    )
    assert hot.status_code == 200, hot.text

    body = _get_health(client, room_id).json()
    assert body["leads"] == {"total": 1, "hot": 1, "handed_to_crm": 0}

    handed = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm", headers=ACTOR
    )
    assert handed.status_code == 200, handed.text

    body = _get_health(client, room_id).json()
    assert body["leads"] == {"total": 1, "hot": 0, "handed_to_crm": 1}


def test_publish_writes_outbox_row_and_history(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)

    first = _publish(client, room_id)
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "published"
    assert body["event_type"] == "RoomHealthSnapshot"
    assert body["snapshot"]["room_id"] == room_id
    assert body["snapshot"]["slots"]["total"] == 0

    rows = db_session.scalars(
        select(OutboxMessage).where(
            OutboxMessage.event_type == "RoomHealthSnapshot"
        )
    ).all()
    assert len(rows) == 1
    assert rows[0].status == "sent"
    assert rows[0].sent_at is not None
    assert rows[0].payload["room_id"] == room_id
    assert rows[0].payload["leads"]["total"] == 0

    second = _publish(client, room_id)
    assert second.status_code == 200, second.text
    assert second.json()["outbox_id"] != body["outbox_id"]

    rows = db_session.scalars(
        select(OutboxMessage).where(
            OutboxMessage.event_type == "RoomHealthSnapshot"
        )
    ).all()
    assert len(rows) == 2

    assert _get_health(client, room_id).status_code == 200


def test_health_unknown_room_404(client):
    unknown = str(uuid.uuid4())
    assert _get_health(client, unknown).status_code == 404
    assert _publish(client, unknown).status_code == 404


def test_regression_hot_lead_outbox_untouched(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)
    created = client.post(
        f"/api/v1/rooms/{room_id}/leads",
        json={"title": "Acme", "contact_name": "Jane"},
        headers=ACTOR,
    )
    lead_id = created.json()["id"]
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot", headers=ACTOR
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm", headers=ACTOR
        ).status_code
        == 200
    )

    assert _get_health(client, room_id).status_code == 200

    hot_rows = db_session.scalars(
        select(OutboxMessage).where(OutboxMessage.event_type == "HotLeadToCrm")
    ).all()
    assert len(hot_rows) == 1
    health_rows = db_session.scalars(
        select(OutboxMessage).where(
            OutboxMessage.event_type == "RoomHealthSnapshot"
        )
    ).all()
    assert health_rows == []
