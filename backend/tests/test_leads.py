"""C9 hot leads: open -> hot -> handed_to_crm + local outbox row (crm-stub)."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.models import OutboxMessage

ACTOR = {"X-Actor-Sub": "founder-demo-sub"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _create(client, room_id: str, title: str = "Warm intro", **extra) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/leads",
        json={"title": title, **extra},
        headers=ACTOR,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_create_and_list_contains_open(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    created = _create(client, room_id, contact_name="Jane", contact_email="j@a.io")
    assert created["status"] == "open"
    assert created["crm_ref"] is None

    listed = client.get(f"/api/v1/rooms/{room_id}/leads")
    assert listed.status_code == 200
    body = listed.json()
    assert body["room_id"] == room_id
    assert [x["id"] for x in body["leads"]] == [created["id"]]
    assert body["leads"][0]["status"] == "open"


def test_mark_hot_then_handoff_creates_outbox(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)
    lead_id = _create(client, room_id)["id"]

    hot = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot", headers=ACTOR
    )
    assert hot.status_code == 200, hot.text
    assert hot.json()["status"] == "hot"

    hand = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm", headers=ACTOR
    )
    assert hand.status_code == 200, hand.text
    body = hand.json()
    assert body["status"] == "handed"
    assert body["crm_ref"] == f"crm-stub:{lead_id}"
    assert body["lead"]["status"] == "handed_to_crm"

    rows = db_session.scalars(
        select(OutboxMessage).where(OutboxMessage.event_type == "HotLeadToCrm")
    ).all()
    assert len(rows) == 1
    msg = rows[0]
    assert msg.event_type == "HotLeadToCrm"
    assert msg.idempotency_key == lead_id
    assert msg.status == "sent"
    assert msg.sent_at is not None
    assert msg.payload["lead_id"] == lead_id
    assert msg.payload["room_id"] == room_id
    assert msg.payload["founder_sub"] == sale_payload["founder_sub"]


def test_handoff_repeat_is_idempotent(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)
    lead_id = _create(client, room_id)["id"]
    client.post(f"/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot", headers=ACTOR)

    first = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm", headers=ACTOR
    )
    assert first.json()["status"] == "handed"

    second = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm", headers=ACTOR
    )
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "already_handed"
    assert second.json()["crm_ref"] == first.json()["crm_ref"]

    rows = db_session.scalars(
        select(OutboxMessage).where(OutboxMessage.event_type == "HotLeadToCrm")
    ).all()
    assert len(rows) == 1


def test_mark_hot_twice_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    lead_id = _create(client, room_id)["id"]
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot", headers=ACTOR
        ).status_code
        == 200
    )
    r = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot", headers=ACTOR
    )
    assert r.status_code == 409


def test_handoff_from_open_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    lead_id = _create(client, room_id)["id"]
    r = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm", headers=ACTOR
    )
    assert r.status_code == 409


def test_mutation_without_actor_header_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    create = client.post(
        f"/api/v1/rooms/{room_id}/leads", json={"title": "No actor"}
    )
    assert create.status_code == 422

    lead_id = _create(client, room_id)["id"]
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot"
        ).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm"
        ).status_code
        == 422
    )


def test_unknown_room_and_lead_404(client, sale_payload):
    missing = uuid.uuid4()
    assert client.get(f"/api/v1/rooms/{missing}/leads").status_code == 404
    assert (
        client.post(
            f"/api/v1/rooms/{missing}/leads",
            json={"title": "x"},
            headers=ACTOR,
        ).status_code
        == 404
    )

    room_id = _handoff(client, sale_payload)
    missing_lead = uuid.uuid4()
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/leads/{missing_lead}/mark-hot", headers=ACTOR
        ).status_code
        == 404
    )


def test_regression_handoff_and_room_read(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    room = client.get(f"/api/v1/rooms/{room_id}")
    assert room.status_code == 200
    assert room.json()["id"] == room_id
