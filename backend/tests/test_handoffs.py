"""C1 FounderHandoff acceptance tests (PostgreSQL)."""

from __future__ import annotations

import copy
import uuid

from sqlalchemy import func, select

from app.db.models import Room, StrategySnapshot


def test_happy_path_sale_example(client, db_session, sale_payload):
    r = client.post("/internal/v1/handoffs", json=sale_payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "created"
    assert body["staffing_unlocked"] is False
    room_id = uuid.UUID(body["room_id"])

    room = db_session.get(Room, room_id)
    assert room is not None
    assert room.handoff_id == uuid.UUID(sale_payload["handoff_id"])
    assert room.staffing_unlocked is False
    assert room.room_type == "sale"
    assert room.name == sale_payload["project"]["name"]

    snap = db_session.scalar(
        select(StrategySnapshot).where(StrategySnapshot.room_id == room_id)
    )
    assert snap is not None
    assert snap.strategy_version == sale_payload["strategy_version"]
    assert snap.strategy_payload["offer"] == sale_payload["strategy"]["offer"]
    assert snap.documents[0]["uri"].startswith("s3://")


def test_idempotent_replay(client, db_session, sale_payload):
    r1 = client.post("/internal/v1/handoffs", json=sale_payload)
    assert r1.status_code == 201
    room_id = r1.json()["room_id"]

    r2 = client.post("/internal/v1/handoffs", json=sale_payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_exists"
    assert r2.json()["room_id"] == room_id
    assert r2.json()["staffing_unlocked"] is False

    count = db_session.scalar(select(func.count()).select_from(Room))
    assert count == 1

    # Snapshot must not be rewritten (still one row).
    snaps = db_session.scalar(select(func.count()).select_from(StrategySnapshot))
    assert snaps == 1


def test_conflict_different_payload(client, sale_payload):
    assert client.post("/internal/v1/handoffs", json=sale_payload).status_code == 201

    other = copy.deepcopy(sale_payload)
    other["strategy_version"] = "2026-10-10.DIFFERENT"
    r = client.post("/internal/v1/handoffs", json=other)
    assert r.status_code == 409


def test_validation_missing_offer(client, sale_payload):
    bad = copy.deepcopy(sale_payload)
    del bad["strategy"]["offer"]
    r = client.post("/internal/v1/handoffs", json=bad)
    assert r.status_code == 422


def test_develop_room_type(client, db_session, sale_payload):
    payload = copy.deepcopy(sale_payload)
    payload["handoff_id"] = str(uuid.uuid4())
    payload["room_type"] = "develop"
    payload["project"]["name"] = "Demo Develop Room"

    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code == 201, r.text
    assert r.json()["staffing_unlocked"] is False

    room = db_session.get(Room, uuid.UUID(r.json()["room_id"]))
    assert room is not None
    assert room.room_type == "develop"
