"""C11 RoomCreated outbox: create → 1 row, replay → без дубля, 409 → без второй строки."""

from __future__ import annotations

import copy
import uuid

from sqlalchemy import select

from app.db.models import OutboxMessage, Room


def _handoff(client, payload: dict) -> dict:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()


def _outbox_rows(db_session):
    return db_session.scalars(select(OutboxMessage)).all()


def test_create_writes_one_room_created_outbox(client, db_session, sale_payload):
    result = _handoff(client, sale_payload)
    assert result["status"] == "created"
    room_id = uuid.UUID(result["room_id"])

    room = db_session.get(Room, room_id)
    assert room is not None

    rows = _outbox_rows(db_session)
    assert len(rows) == 1, rows
    msg = rows[0]
    assert msg.event_type == "RoomCreated"
    assert msg.idempotency_key == str(room_id)
    assert msg.status == "sent"
    assert msg.sent_at is not None
    assert msg.payload["room_id"] == str(room_id)
    assert msg.payload["handoff_id"] == sale_payload["handoff_id"]
    assert msg.payload["room_type"] == "sale"
    assert msg.payload["name"] == sale_payload["project"]["name"]
    assert msg.payload["founder_sub"] == sale_payload["founder_sub"]
    assert msg.payload["strategy_id"] == sale_payload["strategy_id"]
    assert msg.payload["strategy_version"] == sale_payload["strategy_version"]
    assert msg.payload["staffing_unlocked"] is False


def test_replay_does_not_duplicate_outbox(client, db_session, sale_payload):
    _handoff(client, sale_payload)
    r2 = client.post("/internal/v1/handoffs", json=sale_payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_exists"

    rows = _outbox_rows(db_session)
    assert len(rows) == 1
    assert rows[0].event_type == "RoomCreated"


def test_conflict_409_no_second_outbox(client, db_session, sale_payload):
    assert client.post("/internal/v1/handoffs", json=sale_payload).status_code == 201

    other = copy.deepcopy(sale_payload)
    other["strategy_version"] = "2026-10-10.DIFFERENT"
    r = client.post("/internal/v1/handoffs", json=other)
    assert r.status_code == 409

    rows = _outbox_rows(db_session)
    assert len(rows) == 1
    assert rows[0].event_type == "RoomCreated"


def test_develop_room_type_writes_outbox(client, db_session, sale_payload):
    payload = copy.deepcopy(sale_payload)
    payload["handoff_id"] = str(uuid.uuid4())
    payload["room_type"] = "develop"
    payload["project"]["name"] = "Demo Develop Room"

    result = _handoff(client, payload)
    assert result["status"] == "created"
    room_id = uuid.UUID(result["room_id"])

    rows = db_session.scalars(
        select(OutboxMessage).where(OutboxMessage.event_type == "RoomCreated")
    ).all()
    assert len(rows) == 1
    assert rows[0].payload["room_type"] == "develop"
    assert rows[0].payload["name"] == "Demo Develop Room"
    assert rows[0].payload["room_id"] == str(room_id)
