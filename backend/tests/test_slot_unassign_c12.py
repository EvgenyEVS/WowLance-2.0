"""C12 slot unassign/reassign: filled->open, swap person, error codes, regression."""

from __future__ import annotations

import uuid

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


def _assign(client, room_id: str, slot_id: str, sub: str, headers=ACTOR) -> object:
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/assign",
        json={"freelancer_sub": sub},
        headers=headers,
    )


def _unassign(client, room_id: str, slot_id: str, headers=ACTOR) -> object:
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/unassign",
        headers=headers,
    )


def _reassign(client, room_id: str, slot_id: str, sub: str, headers=ACTOR) -> object:
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/reassign",
        json={"freelancer_sub": sub},
        headers=headers,
    )


def _ready_room(client, sale_payload) -> tuple[str, list[dict]]:
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    return room_id, _materialize(client, room_id)


def test_assign_unassign_then_reassign_same_slot(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    r = _unassign(client, room_id, slots[0]["id"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "unassigned"
    assert body["slot"]["status"] == "open"
    assert body["slot"]["freelancer_sub"] is None

    listed = client.get(f"/api/v1/rooms/{room_id}/slots").json()["slots"]
    opened = [s for s in listed if s["id"] == slots[0]["id"]][0]
    assert opened["status"] == "open"
    assert opened["freelancer_sub"] is None

    again = _assign(client, room_id, slots[0]["id"], "f-1")
    assert again.status_code == 200, again.text
    assert again.json()["status"] == "assigned"


def test_unassign_open_slot_409(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    r = _unassign(client, room_id, slots[0]["id"])
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "slot_not_filled"


def test_reassign_filled_swaps_person(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    _upsert(client, "f-2", "Bob")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    r = _reassign(client, room_id, slots[0]["id"], "f-2")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "reassigned"
    assert body["slot"]["status"] == "filled"
    assert body["slot"]["freelancer_sub"] == "f-2"


def test_reassign_same_sub_idempotent(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    r = _reassign(client, room_id, slots[0]["id"], "f-1")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "already_assigned"
    assert r.json()["slot"]["freelancer_sub"] == "f-1"


def test_reassign_to_seated_elsewhere_409(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    _upsert(client, "f-2", "Bob")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200
    assert _assign(client, room_id, slots[1]["id"], "f-2").status_code == 200

    r = _reassign(client, room_id, slots[0]["id"], "f-2")
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "already_seated"


def test_reassign_open_slot_409(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    r = _reassign(client, room_id, slots[0]["id"], "f-1")
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "slot_not_filled"


def test_reassign_not_in_roster_404(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    r = _reassign(client, room_id, slots[0]["id"], "ghost-sub")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "freelancer_not_in_roster"


def test_unassign_reassign_locked_room_403(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")

    r_un = _unassign(client, room_id, str(uuid.uuid4()))
    assert r_un.status_code == 403, r_un.text
    assert r_un.json()["detail"] == "staffing_locked"

    r_re = _reassign(client, room_id, str(uuid.uuid4()), "f-1")
    assert r_re.status_code == 403, r_re.text
    assert r_re.json()["detail"] == "staffing_locked"


def test_unassign_unknown_room_404(client):
    r = _unassign(client, str(uuid.uuid4()), str(uuid.uuid4()))
    assert r.status_code == 404, r.text


def test_unassign_unknown_slot_404(client, sale_payload):
    room_id, _ = _ready_room(client, sale_payload)
    r = _unassign(client, room_id, str(uuid.uuid4()))
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "slot_id does not exist in this room"


def test_unassign_reassign_without_actor_header_422(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    assert (
        _unassign(client, room_id, slots[0]["id"], headers={}).status_code == 422
    )
    assert (
        _reassign(client, room_id, slots[0]["id"], "f-1", headers={}).status_code
        == 422
    )


def test_regression_tasks_and_outbox_untouched(client, db_session, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200
    assert _unassign(client, room_id, slots[0]["id"]).status_code == 200

    tasks = client.get(f"/api/v1/rooms/{room_id}/tasks")
    assert tasks.status_code == 200, tasks.text
    assert tasks.json()["tasks"] == []

    from sqlalchemy import select

    from app.db.models import OutboxMessage

    events = db_session.scalars(select(OutboxMessage)).all()
    assert len(events) == 2
    assert {e.event_type for e in events} == {"RoomCreated", "StaffingUnlocked"}
