"""C3 GET /api/v1/rooms/{room_id} (PostgreSQL)."""

from __future__ import annotations

import uuid

from app.db.models import Room


def test_get_room_matches_handoff_snapshot(client, db_session, sale_payload):
    created = client.post("/internal/v1/handoffs", json=sale_payload)
    assert created.status_code == 201, created.text
    room_id = created.json()["room_id"]

    r = client.get(f"/api/v1/rooms/{room_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    strategy = sale_payload["strategy"]
    assert body["id"] == room_id
    assert body["name"] == sale_payload["project"]["name"]
    assert body["room_type"] == "sale"
    assert body["timezone"] == sale_payload["project"]["timezone"]
    assert body["founder_sub"] == sale_payload["founder_sub"]
    assert body["handoff_id"] == sale_payload["handoff_id"]
    assert body["strategy"]["offer"] == strategy["offer"]
    assert body["strategy"]["audience"] == strategy["audience"]
    assert body["strategy"]["hot_criteria"] == strategy["hot_criteria"]
    assert body["strategy"]["utp"] == strategy["utp"]
    assert body["strategy"]["strategy_version"] == sale_payload["strategy_version"]
    assert body["strategy"]["documents"][0]["uri"].startswith("s3://")


def test_staffing_unlocked_matches_db_after_handoff(client, db_session, sale_payload):
    created = client.post("/internal/v1/handoffs", json=sale_payload)
    room_id = uuid.UUID(created.json()["room_id"])
    room = db_session.get(Room, room_id)
    assert room is not None
    assert room.staffing_unlocked is False

    r = client.get(f"/api/v1/rooms/{room_id}")
    assert r.status_code == 200
    assert r.json()["staffing_unlocked"] is False
    assert r.json()["staffing_unlocked"] == room.staffing_unlocked


def test_unknown_room_404(client):
    r = client.get(f"/api/v1/rooms/{uuid.uuid4()}")
    assert r.status_code == 404
