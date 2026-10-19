"""C17 member termination: terminate → free slot + journal + outbox MemberTerminated."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.models import OutboxMessage, RoomTermination

ACTOR = {"X-Actor-Sub": "teamlead-demo-sub"}


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


def _materialize(client, room_id: str) -> list[dict]:
    r = client.post(f"/api/v1/rooms/{room_id}/slots/materialize")
    assert r.status_code == 200, r.text
    return r.json()["slots"]


def _upsert(client, sub: str, name: str = "Demo Freelancer") -> dict:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _assign(client, room_id: str, slot_id: str, sub: str) -> object:
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/assign",
        json={"freelancer_sub": sub},
        headers=ACTOR,
    )


def _terminate(client, room_id: str, sub: str, reason: str, slot_id: str | None = None):
    body: dict = {"reason": reason}
    if slot_id is not None:
        body["slot_id"] = slot_id
    return client.post(
        f"/api/v1/rooms/{room_id}/members/{sub}/terminate",
        json=body,
        headers=ACTOR,
    )


def _list_terminations(client, room_id: str):
    return client.get(f"/api/v1/rooms/{room_id}/terminations")


def test_assign_then_terminate_frees_slot_and_writes_outbox(
    client, sale_payload, db_session
):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    slots = _materialize(client, room_id)
    assert len(slots) >= 1
    _upsert(client, "f-1", "Alice")

    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    # slot is filled
    listed = client.get(f"/api/v1/rooms/{room_id}/slots").json()["slots"]
    filled = [s for s in listed if s["id"] == slots[0]["id"]][0]
    assert filled["status"] == "filled"
    assert filled["freelancer_sub"] == "f-1"

    r = _terminate(client, room_id, "f-1", "Redundancy / end of contract")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "terminated"
    assert body["freelancer_sub"] == "f-1"
    assert slots[0]["id"] in [str(s) for s in body["slot_ids"]]

    # slot is open again
    listed = client.get(f"/api/v1/rooms/{room_id}/slots").json()["slots"]
    freed = [s for s in listed if s["id"] == slots[0]["id"]][0]
    assert freed["status"] == "open"
    assert freed["freelancer_sub"] is None

    # 1 termination row
    rows = db_session.scalars(select(RoomTermination)).all()
    assert len(rows) == 1
    assert rows[0].freelancer_sub == "f-1"
    assert rows[0].reason == "Redundancy / end of contract"
    assert rows[0].terminated_by_sub == "teamlead-demo-sub"
    assert str(slots[0]["id"]) in rows[0].slot_ids

    # 1 outbox MemberTerminated row
    outbox = db_session.scalars(
        select(OutboxMessage).where(
            OutboxMessage.event_type == "MemberTerminated"
        )
    ).all()
    assert len(outbox) == 1
    assert outbox[0].status == "sent"
    assert outbox[0].payload["freelancer_sub"] == "f-1"
    assert outbox[0].payload["reason"] == "Redundancy / end of contract"


def test_terminate_without_seat_404(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    r = _terminate(client, room_id, "ghost-sub", "No seat")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "not_seated"


def test_terminate_empty_reason_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    _materialize(client, room_id)
    _upsert(client, "f-1", "Alice")
    _assign(client, room_id, "00000000-0000-0000-0000-000000000000", "f-1")

    r = _terminate(client, room_id, "f-1", "")
    assert r.status_code == 422, r.text


def test_list_terminations_returns_record(client, sale_payload, db_session):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    slots = _materialize(client, room_id)
    _upsert(client, "f-1", "Alice")
    _assign(client, room_id, slots[0]["id"], "f-1")
    _terminate(client, room_id, "f-1", "Reason one")

    r = _list_terminations(client, room_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["room_id"] == room_id
    assert len(body["terminations"]) == 1
    t = body["terminations"][0]
    assert t["freelancer_sub"] == "f-1"
    assert t["reason"] == "Reason one"
    assert t["terminated_by_sub"] == "teamlead-demo-sub"
    assert t["created_at"]


def test_terminate_repeat_not_seated_404(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    slots = _materialize(client, room_id)
    _upsert(client, "f-1", "Alice")
    _assign(client, room_id, slots[0]["id"], "f-1")

    assert _terminate(client, room_id, "f-1", "First time").status_code == 200

    # repeat: sub no longer seated → 404 not_seated
    r = _terminate(client, room_id, "f-1", "Second time")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "not_seated"


def test_terminate_explicit_slot_not_filled_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    slots = _materialize(client, room_id)
    _upsert(client, "f-1", "Alice")

    # slot is open, explicit slot_id → 409 slot_not_filled
    r = _terminate(
        client, room_id, "f-1", "Nope", slot_id=str(slots[0]["id"])
    )
    assert r.status_code == 409, r.text


def test_regression_assign_and_list_slots_untouched(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    slots = _materialize(client, room_id)
    _upsert(client, "f-1", "Alice")

    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    listed = client.get(f"/api/v1/rooms/{room_id}/slots")
    assert listed.status_code == 200
    body = listed.json()
    assert len(body["slots"]) == len(slots)


def test_regression_outbox_event_types_unaffected(
    client, db_session, sale_payload
):
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    slots = _materialize(client, room_id)
    _upsert(client, "f-1", "Alice")
    _assign(client, room_id, slots[0]["id"], "f-1")
    _terminate(client, room_id, "f-1", "Reason")

    member_term = db_session.scalars(
        select(OutboxMessage).where(
            OutboxMessage.event_type == "MemberTerminated"
        )
    ).all()

    assert len(member_term) == 1
