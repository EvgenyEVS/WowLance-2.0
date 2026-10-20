"""C18 StaffingUnlocked outbox: первый unlock -> 1 строка, replay -> без дубля, 404/409 -> без строки."""

from __future__ import annotations

import copy
import uuid

from sqlalchemy import select

from app.db.models import OutboxMessage, Room


def _grant(client, room_id: str, entitlement_id: str | None = None) -> dict:
    return client.post(
        "/internal/v1/entitlements",
        json={
            "entitlement_id": entitlement_id or str(uuid.uuid4()),
            "room_id": room_id,
            "source": "stub",
        },
    )


def _staffing_unlocked_rows(db_session):
    return db_session.scalars(
        select(OutboxMessage).where(OutboxMessage.event_type == "StaffingUnlocked")
    ).all()


def test_first_unlock_writes_one_staffing_unlocked_outbox(
    client, db_session, sale_payload
):
    created = client.post("/internal/v1/handoffs", json=sale_payload)
    assert created.status_code == 201, created.text
    room_id = created.json()["room_id"]

    r = _grant(client, room_id)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "granted"
    assert r.json()["staffing_unlocked"] is True

    room = db_session.get(Room, uuid.UUID(room_id))
    assert room is not None
    assert room.staffing_unlocked is True

    rows = _staffing_unlocked_rows(db_session)
    assert len(rows) == 1, rows
    msg = rows[0]
    assert msg.event_type == "StaffingUnlocked"
    assert msg.status == "sent"
    assert msg.sent_at is not None
    assert msg.idempotency_key == f"room:{room_id}:StaffingUnlocked"
    assert msg.payload["room_id"] == room_id
    assert msg.payload["staffing_unlocked"] is True
    assert msg.payload["entitlement_id"] is not None
    assert msg.payload["founder_sub"] == sale_payload["founder_sub"]
    assert "unlocked_at" in msg.payload


def test_replay_entitlement_does_not_duplicate_outbox(client, db_session, sale_payload):
    room_id = client.post("/internal/v1/handoffs", json=sale_payload).json()["room_id"]
    entitlement_id = str(uuid.uuid4())

    r1 = _grant(client, room_id, entitlement_id)
    assert r1.status_code == 200
    assert r1.json()["status"] == "granted"

    r2 = _grant(client, room_id, entitlement_id)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_granted"

    rows = _staffing_unlocked_rows(db_session)
    assert len(rows) == 1
    assert rows[0].event_type == "StaffingUnlocked"


def test_room_created_regression_still_one_row(client, db_session, sale_payload):
    created = client.post("/internal/v1/handoffs", json=sale_payload)
    assert created.status_code == 201
    room_id = created.json()["room_id"]

    _grant(client, room_id)

    room_created = db_session.scalars(
        select(OutboxMessage).where(OutboxMessage.event_type == "RoomCreated")
    ).all()
    assert len(room_created) == 1, room_created

    staffing = _staffing_unlocked_rows(db_session)
    assert len(staffing) == 1


def test_unknown_room_404_no_outbox(client, db_session):
    r = _grant(client, str(uuid.uuid4()))
    assert r.status_code == 404

    rows = _staffing_unlocked_rows(db_session)
    assert rows == []


def test_entitlement_conflict_409_no_outbox(client, db_session, sale_payload):
    room_a = client.post("/internal/v1/handoffs", json=sale_payload).json()["room_id"]
    other = copy.deepcopy(sale_payload)
    other["handoff_id"] = str(uuid.uuid4())
    other["project"]["name"] = "Second Room"
    room_b = client.post("/internal/v1/handoffs", json=other).json()["room_id"]

    entitlement_id = str(uuid.uuid4())
    first = _grant(client, room_a, entitlement_id)
    assert first.status_code == 200

    conflict = _grant(client, room_b, entitlement_id)
    assert conflict.status_code == 409

    rows = _staffing_unlocked_rows(db_session)
    assert len(rows) == 1
    assert rows[0].payload["room_id"] == room_a
