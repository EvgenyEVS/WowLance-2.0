"""C14 meet / Jitsi stub: ensure idempotency, GET room reflects meeting_url, 404, regression."""

from __future__ import annotations

import uuid

from app.db.models import Room


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


ACTOR = {"X-Actor-Sub": "founder-demo-sub"}


def test_meet_ensure_creates_url(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    first = client.post(
        f"/api/v1/rooms/{room_id}/meet/ensure", headers=ACTOR
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["status"] == "created"
    assert body["meeting_url"] == f"https://meet.jit.si/wowlance-{room_id}"

    # Idempotent repeat: same url, status already_exists
    second = client.post(
        f"/api/v1/rooms/{room_id}/meet/ensure", headers=ACTOR
    )
    assert second.status_code == 200, second.text
    body2 = second.json()
    assert body2["status"] == "already_exists"
    assert body2["meeting_url"] == body["meeting_url"]


def test_meet_persisted_on_room_row(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)
    client.post(f"/api/v1/rooms/{room_id}/meet/ensure", headers=ACTOR)

    room = db_session.get(Room, uuid.UUID(room_id))
    assert room is not None
    assert room.meeting_url == f"https://meet.jit.si/wowlance-{room_id}"


def test_get_room_reflects_meeting_url(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    client.post(f"/api/v1/rooms/{room_id}/meet/ensure", headers=ACTOR)

    r = client.get(f"/api/v1/rooms/{room_id}")
    assert r.status_code == 200, r.text
    assert r.json()["meeting_url"] == f"https://meet.jit.si/wowlance-{room_id}"


def test_get_room_meeting_url_null_before_ensure(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    r = client.get(f"/api/v1/rooms/{room_id}")
    assert r.status_code == 200, r.text
    assert r.json()["meeting_url"] is None


def test_meet_ensure_unknown_room_404(client):
    r = client.post(
        f"/api/v1/rooms/{uuid.uuid4()}/meet/ensure", headers=ACTOR
    )
    assert r.status_code == 404, r.text


def test_meet_missing_actor_sub_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    r = client.post(f"/api/v1/rooms/{room_id}/meet/ensure")
    assert r.status_code == 422, r.text


def test_regression_handoff_and_room_read_without_meet(client, sale_payload):
    created = client.post("/internal/v1/handoffs", json=sale_payload)
    assert created.status_code in (200, 201), created.text
    room_id = created.json()["room_id"]

    r = client.get(f"/api/v1/rooms/{room_id}")
    assert r.status_code == 200, r.text
    assert r.json()["meeting_url"] is None
    assert r.json()["staffing_unlocked"] is False
