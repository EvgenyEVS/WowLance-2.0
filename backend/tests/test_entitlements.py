"""C2 EntitlementGranted acceptance tests (PostgreSQL)."""

from __future__ import annotations

import copy
import uuid

from sqlalchemy import func, select

from app.db.models import Entitlement, Room


def _grant_body(room_id: str, entitlement_id: str | None = None) -> dict:
    return {
        "entitlement_id": entitlement_id or str(uuid.uuid4()),
        "room_id": room_id,
        "source": "stub",
    }


def test_grant_after_handoff_unlocks_staffing(client, db_session, sale_payload):
    created = client.post("/internal/v1/handoffs", json=sale_payload)
    assert created.status_code == 201, created.text
    assert created.json()["staffing_unlocked"] is False
    room_id = created.json()["room_id"]

    r = client.post("/internal/v1/entitlements", json=_grant_body(room_id))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "granted"
    assert body["staffing_unlocked"] is True
    assert body["room_id"] == room_id

    room = db_session.get(Room, uuid.UUID(room_id))
    assert room is not None
    assert room.staffing_unlocked is True


def test_idempotent_replay_same_entitlement(client, db_session, sale_payload):
    room_id = client.post("/internal/v1/handoffs", json=sale_payload).json()["room_id"]
    entitlement_id = str(uuid.uuid4())
    payload = _grant_body(room_id, entitlement_id)

    r1 = client.post("/internal/v1/entitlements", json=payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "granted"

    r2 = client.post("/internal/v1/entitlements", json=payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_granted"
    assert r2.json()["staffing_unlocked"] is True
    assert r2.json()["room_id"] == room_id

    count = db_session.scalar(select(func.count()).select_from(Entitlement))
    assert count == 1


def test_unknown_room_id_404(client):
    r = client.post(
        "/internal/v1/entitlements",
        json=_grant_body(str(uuid.uuid4())),
    )
    assert r.status_code == 404


def test_same_entitlement_other_room_409(client, sale_payload):
    room_a = client.post("/internal/v1/handoffs", json=sale_payload).json()["room_id"]
    other = copy.deepcopy(sale_payload)
    other["handoff_id"] = str(uuid.uuid4())
    other["project"]["name"] = "Second Room"
    room_b = client.post("/internal/v1/handoffs", json=other).json()["room_id"]

    entitlement_id = str(uuid.uuid4())
    first = client.post(
        "/internal/v1/entitlements",
        json=_grant_body(room_a, entitlement_id),
    )
    assert first.status_code == 200

    conflict = client.post(
        "/internal/v1/entitlements",
        json=_grant_body(room_b, entitlement_id),
    )
    assert conflict.status_code == 409


def test_c1_handoff_example_still_locked_until_grant(client, sale_payload):
    r = client.post("/internal/v1/handoffs", json=sale_payload)
    assert r.status_code == 201
    assert r.json()["status"] == "created"
    assert r.json()["staffing_unlocked"] is False


def test_handoff_replay_does_not_reset_unlocked(client, db_session, sale_payload):
    created = client.post("/internal/v1/handoffs", json=sale_payload)
    room_id = created.json()["room_id"]
    grant = client.post("/internal/v1/entitlements", json=_grant_body(room_id))
    assert grant.json()["status"] == "granted"

    replay = client.post("/internal/v1/handoffs", json=sale_payload)
    assert replay.status_code == 200
    assert replay.json()["status"] == "already_exists"
    assert replay.json()["staffing_unlocked"] is True
    assert replay.json()["room_id"] == room_id

    room = db_session.get(Room, uuid.UUID(room_id))
    assert room is not None
    assert room.staffing_unlocked is True
