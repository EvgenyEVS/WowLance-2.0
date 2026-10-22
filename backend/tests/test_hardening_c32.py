"""C32 stub hardening: idempotent internal POSTs + canonical 4xx detail shape."""

from __future__ import annotations

import copy
import uuid

from sqlalchemy import func, select

from app.db.models import Room


def test_health_echoes_request_id(client):
    r = client.get("/health", headers={"X-Request-Id": "demo-req-1"})
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.headers.get("x-request-id") == "demo-req-1"


def test_handoff_replay_same_room(client, db_session, sale_payload):
    r1 = client.post("/internal/v1/handoffs", json=sale_payload)
    assert r1.status_code == 201
    room_id = r1.json()["room_id"]
    r2 = client.post("/internal/v1/handoffs", json=sale_payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_exists"
    assert r2.json()["room_id"] == room_id
    assert db_session.scalar(select(func.count()).select_from(Room)) == 1


def test_handoff_conflict_detail_is_string(client, sale_payload):
    assert client.post("/internal/v1/handoffs", json=sale_payload).status_code == 201
    other = copy.deepcopy(sale_payload)
    other["strategy_version"] = "conflict.1"
    r = client.post("/internal/v1/handoffs", json=other)
    assert r.status_code == 409
    assert isinstance(r.json()["detail"], str)


def test_entitlement_replay_already_granted(client, sale_payload):
    room_id = client.post("/internal/v1/handoffs", json=sale_payload).json()["room_id"]
    body = {
        "entitlement_id": str(uuid.uuid4()),
        "room_id": room_id,
        "source": "stub",
    }
    r1 = client.post("/internal/v1/entitlements", json=body)
    assert r1.status_code == 200
    assert r1.json()["status"] == "granted"
    r2 = client.post("/internal/v1/entitlements", json=body)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_granted"
    assert r2.json()["room_id"] == room_id


def test_crm_deal_status_replay(client, sale_payload):
    room_id = client.post("/internal/v1/handoffs", json=sale_payload).json()["room_id"]
    headers = {"X-Actor-Sub": "founder-demo-sub"}
    lead = client.post(
        f"/api/v1/rooms/{room_id}/leads",
        json={"title": "acct"},
        headers=headers,
    )
    assert lead.status_code == 201, lead.text
    lead_id = lead.json()["id"]
    assert client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/mark-hot", headers=headers
    ).status_code == 200
    handed = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead_id}/handoff-crm", headers=headers
    )
    assert handed.status_code == 200, handed.text
    crm_ref = handed.json()["lead"]["crm_ref"]
    payload = {
        "crm_ref": crm_ref,
        "deal_status": "won",
        "amount": 10,
        "currency": "USD",
    }
    r1 = client.post("/internal/v1/crm/deal-status", json=payload)
    assert r1.status_code == 200, r1.text
    r2 = client.post("/internal/v1/crm/deal-status", json=payload)
    assert r2.status_code == 200
    assert r2.json()["deal_status"] == "won"
    assert r2.json()["deal_amount"] == r1.json()["deal_amount"]


def test_validation_error_detail_is_list(client):
    r = client.post("/internal/v1/handoffs", json={})
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], list)
