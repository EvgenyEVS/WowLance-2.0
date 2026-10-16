"""C6 roster + assign: upsert roster, seat an open slot, error codes, regression."""

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


def _upsert(client, sub: str, name: str = "Demo Freelancer", **extra) -> dict:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name, **extra},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _assign(client, room_id: str, slot_id: str, sub: str, headers=ACTOR) -> object:
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/assign",
        json={"freelancer_sub": sub},
        headers=headers,
    )


def _ready_room(client, sale_payload) -> tuple[str, list[dict]]:
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    return room_id, _materialize(client, room_id)


def test_roster_upsert_then_list_contains(client):
    first = _upsert(client, "f-1", "Alice", skills=["writing"], level="B")
    assert first == {"freelancer_sub": "f-1", "status": "upserted"}

    listed = client.get("/api/v1/roster")
    assert listed.status_code == 200
    members = listed.json()["members"]
    assert [m["freelancer_sub"] for m in members] == ["f-1"]
    assert members[0]["display_name"] == "Alice"
    assert members[0]["skills"] == ["writing"]
    assert members[0]["level"] == "B"

    replay = _upsert(client, "f-1", "Alice", skills=["writing"], level="B")
    assert replay["status"] == "already_exists"

    updated = _upsert(client, "f-1", "Alice Cooper", level="C")
    assert updated["status"] == "upserted"
    members = client.get("/api/v1/roster").json()["members"]
    assert members[0]["display_name"] == "Alice Cooper"
    assert members[0]["level"] == "C"


def test_flow_handoff_entitlement_materialize_assign_fills(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    assert len(slots) == 2
    _upsert(client, "f-1", "Alice")

    r = _assign(client, room_id, slots[0]["id"], "f-1")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "assigned"
    assert body["slot"]["status"] == "filled"
    assert body["slot"]["freelancer_sub"] == "f-1"

    listed = client.get(f"/api/v1/rooms/{room_id}/slots").json()["slots"]
    filled = [s for s in listed if s["id"] == slots[0]["id"]][0]
    assert filled["status"] == "filled"
    assert filled["freelancer_sub"] == "f-1"


def test_repeat_assign_same_freelancer_is_idempotent(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    again = _assign(client, room_id, slots[0]["id"], "f-1")
    assert again.status_code == 200, again.text
    assert again.json()["status"] == "already_assigned"


def test_assign_without_roster_404(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    r = _assign(client, room_id, slots[0]["id"], "ghost-sub")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "freelancer_not_in_roster"


def test_assign_locked_room_403(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")

    r = _assign(client, room_id, str(uuid.uuid4()), "f-1")
    assert r.status_code == 403, r.text
    assert r.json()["detail"] == "staffing_locked"


def test_assign_unknown_slot_404(client, sale_payload):
    room_id, _ = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    r = _assign(client, room_id, str(uuid.uuid4()), "f-1")
    assert r.status_code == 404, r.text


def test_assign_filled_by_other_409(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    _upsert(client, "f-2", "Bob")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    r = _assign(client, room_id, slots[0]["id"], "f-2")
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "slot_already_filled"


def test_one_freelancer_two_slots_409(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    r = _assign(client, room_id, slots[1]["id"], "f-1")
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "already_seated"


def test_assign_without_actor_header_422(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    r = _assign(client, room_id, slots[0]["id"], "f-1", headers={})
    assert r.status_code == 422, r.text


def test_regression_materialize_without_assign(client, sale_payload):
    room_id, slots = _ready_room(client, sale_payload)
    assert all(s["status"] == "open" for s in slots)
    assert all(s["freelancer_sub"] is None for s in slots)
