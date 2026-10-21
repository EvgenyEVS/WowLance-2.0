"""C19 CRM deal-status inbound: POST /internal/v1/crm/deal-status updates deal_* on a handed_to_crm lead."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.models import RoomLead

ACTOR = {"X-Actor-Sub": "founder-demo-sub"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _create(client, room_id: str, title: str = "Warm intro") -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/leads",
        json={"title": title},
        headers=ACTOR,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _handed_lead(client, db_session, sale_payload):
    """Handoff → create lead → mark hot → handoff-crm. Returns (room_id, lead, crm_ref)."""
    room_id = _handoff(client, sale_payload)
    lead = _create(client, room_id)
    client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead['id']}/mark-hot", headers=ACTOR
    )
    hand = client.post(
        f"/api/v1/rooms/{room_id}/leads/{lead['id']}/handoff-crm", headers=ACTOR
    )
    assert hand.status_code == 200, hand.text
    assert hand.json()["status"] == "handed"
    crm_ref = hand.json()["crm_ref"]
    assert crm_ref == f"crm-stub:{lead['id']}"
    return room_id, lead, crm_ref


def _deal_status(client, crm_ref: str, payload: dict):
    body = {"crm_ref": crm_ref, "deal_status": "won", **payload}
    return client.post("/internal/v1/crm/deal-status", json=body)


def test_deal_status_won_sets_fields(client, db_session, sale_payload):
    room_id, lead, crm_ref = _handed_lead(client, db_session, sale_payload)

    r = _deal_status(client, crm_ref, {"amount": 15000, "currency": "USD"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["room_id"] == room_id
    assert body["lead_id"] == lead["id"]
    assert body["crm_ref"] == crm_ref
    assert body["deal_status"] == "won"
    assert body["deal_amount"] == "15000.00"
    assert body["deal_currency"] == "USD"
    assert body["deal_updated_at"] is not None

    row = db_session.get(RoomLead, uuid.UUID(lead["id"]))
    assert row is not None
    assert row.deal_status == "won"
    assert row.deal_currency == "USD"
    assert row.deal_updated_at is not None


def test_deal_status_idempotent_repeat(client, db_session, sale_payload):
    room_id, lead, crm_ref = _handed_lead(client, db_session, sale_payload)

    r1 = _deal_status(client, crm_ref, {"amount": 15000, "currency": "USD"})
    assert r1.status_code == 200

    r2 = _deal_status(client, crm_ref, {"amount": 15000, "currency": "USD"})
    assert r2.status_code == 200
    assert r2.json()["deal_updated_at"] == r1.json()["deal_updated_at"]


def test_unknown_crm_ref_404(client):
    r = _deal_status(
        client, "crm-stub:" + str(uuid.uuid4()), {"amount": 100, "currency": "USD"}
    )
    assert r.status_code == 404, r.text


def test_deal_status_on_non_handed_lead_409(client, db_session, sale_payload):
    """crm_ref set but lead not in handed_to_crm → 409 lead_not_handed."""
    for status in ("open", "hot"):
        room_id = _handoff(client, sale_payload)
        lead = _create(client, room_id)
        if status == "hot":
            client.post(
                f"/api/v1/rooms/{room_id}/leads/{lead['id']}/mark-hot",
                headers=ACTOR,
            )
        crm_ref = f"crm-stub:{lead['id']}"
        # simulate a lead that has crm_ref but is not handed (defensive branch)
        row = db_session.get(RoomLead, uuid.UUID(lead["id"]))
        row.crm_ref = crm_ref
        db_session.commit()

        r = _deal_status(client, crm_ref, {"amount": 100, "currency": "USD"})
        assert r.status_code == 409, r.text


def test_list_leads_returns_deal_fields(client, db_session, sale_payload):
    room_id, lead, crm_ref = _handed_lead(client, db_session, sale_payload)
    _deal_status(client, crm_ref, {"amount": 15000, "currency": "USD"})

    listed = client.get(f"/api/v1/rooms/{room_id}/leads")
    assert listed.status_code == 200
    body = listed.json()
    item = body["leads"][0]
    assert item["id"] == lead["id"]
    assert item["deal_status"] == "won"
    assert item["deal_amount"] == "15000.00"
    assert item["deal_currency"] == "USD"
    assert item["deal_updated_at"] is not None


def test_c9_handoff_outbox_regression(client, db_session, sale_payload):
    """C9 outbox still exactly one row after deal-status applied."""
    room_id, lead, crm_ref = _handed_lead(client, db_session, sale_payload)
    _deal_status(client, crm_ref, {"amount": 15000, "currency": "USD"})

    from app.db.models import OutboxMessage

    rows = db_session.scalars(
        select(OutboxMessage).where(OutboxMessage.event_type == "HotLeadToCrm")
    ).all()
    assert len(rows) == 1, rows
