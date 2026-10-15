"""C4 staffing slots: gated by entitlement, materialized from snapshot intent."""

from __future__ import annotations

import copy
import uuid

from sqlalchemy import func, select

from app.db.models import RoomFunctionSlot


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
    assert r.json()["staffing_unlocked"] is True


def test_materialize_sale_example_two_seller_seats(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)

    r = client.post(f"/api/v1/rooms/{room_id}/slots/materialize")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "materialized"
    slots = body["slots"]
    assert len(slots) == 2
    assert [s["role_key"] for s in slots] == ["seller", "seller"]
    assert [s["seat_index"] for s in slots] == [1, 2]
    assert all(s["status"] == "open" for s in slots)
    assert all(s["freelancer_sub"] is None for s in slots)
    assert all(s["level_min"] == "B" for s in slots)

    listed = client.get(f"/api/v1/rooms/{room_id}/slots")
    assert listed.status_code == 200
    assert listed.json()["staffing_unlocked"] is True
    assert len(listed.json()["slots"]) == 2

    count = db_session.scalar(select(func.count()).select_from(RoomFunctionSlot))
    assert count == 2


def test_materialize_replay_is_idempotent(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    first = client.post(f"/api/v1/rooms/{room_id}/slots/materialize")
    assert first.json()["status"] == "materialized"

    second = client.post(f"/api/v1/rooms/{room_id}/slots/materialize")
    assert second.status_code == 200
    assert second.json()["status"] == "already_materialized"
    assert len(second.json()["slots"]) == 2

    count = db_session.scalar(select(func.count()).select_from(RoomFunctionSlot))
    assert count == 2


def test_locked_room_returns_403(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    materialize = client.post(f"/api/v1/rooms/{room_id}/slots/materialize")
    assert materialize.status_code == 403
    assert materialize.json()["detail"] == "staffing_locked"

    listed = client.get(f"/api/v1/rooms/{room_id}/slots")
    assert listed.status_code == 403
    assert listed.json()["detail"] == "staffing_locked"


def test_unknown_room_404(client):
    missing = uuid.uuid4()
    assert client.post(f"/api/v1/rooms/{missing}/slots/materialize").status_code == 404
    assert client.get(f"/api/v1/rooms/{missing}/slots").status_code == 404


def test_empty_staffing_intent_materializes_empty_list(client, sale_payload):
    payload = copy.deepcopy(sale_payload)
    payload["handoff_id"] = str(uuid.uuid4())
    payload["staffing_intent"] = None
    room_id = _handoff(client, payload)
    _unlock(client, room_id)

    r = client.post(f"/api/v1/rooms/{room_id}/slots/materialize")
    assert r.status_code == 200, r.text
    assert r.json()["slots"] == []
