"""C27 room RBAC lite: membership + 403 matrix. Default env keeps RBAC off."""

from __future__ import annotations

import uuid

from app.config import settings

FOUNDER = {"X-Actor-Sub": "founder-demo-sub"}
TEAMLEAD = {"X-Actor-Sub": "teamlead-demo-sub"}
MEMBER = {"X-Actor-Sub": "freelancer-demo-sub"}
STRANGER = {"X-Actor-Sub": "stranger-sub"}


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


def _materialize(client, room_id: str, headers=None) -> list[dict]:
    r = client.post(
        f"/api/v1/rooms/{room_id}/slots/materialize",
        headers=headers or {},
    )
    assert r.status_code == 200, r.text
    return r.json()["slots"]


def _upsert(client, sub: str, name: str) -> None:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name},
    )
    assert r.status_code == 200, r.text


def _assign(client, room_id: str, slot_id: str, sub: str, headers):
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/assign",
        json={"freelancer_sub": sub},
        headers=headers,
    )


def _ready(client, sale_payload, headers=None) -> tuple[str, list[dict]]:
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    return room_id, _materialize(client, room_id, headers=headers)


def test_rbac_off_non_member_can_assign(client, sale_payload):
    """Default ROOM_RBAC_DISABLED=true: G1–G10 / demo path unchanged."""
    assert settings.room_rbac_disabled is True
    room_id, slots = _ready(client, sale_payload)
    open_slot = next(s for s in slots if s["status"] == "open")
    _upsert(client, "freelancer-demo-sub", "Alice")
    r = _assign(
        client, room_id, open_slot["id"], "freelancer-demo-sub", TEAMLEAD
    )
    assert r.status_code == 200, r.text


def test_handoff_seeds_founder_membership(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    listed = client.get(f"/api/v1/rooms/{room_id}/members")
    assert listed.status_code == 200, listed.text
    members = listed.json()["members"]
    assert [m["user_sub"] for m in members] == ["founder-demo-sub"]
    assert members[0]["role"] == "founder"


def test_assign_upserts_member_role(client, sale_payload):
    room_id, slots = _ready(client, sale_payload)
    open_slot = next(s for s in slots if s["status"] == "open")
    _upsert(client, "freelancer-demo-sub", "Alice")
    assert _assign(
        client, room_id, open_slot["id"], "freelancer-demo-sub", FOUNDER
    ).status_code == 200
    roles = {
        m["user_sub"]: m["role"]
        for m in client.get(f"/api/v1/rooms/{room_id}/members").json()["members"]
    }
    assert roles["founder-demo-sub"] == "founder"
    assert roles["freelancer-demo-sub"] == "member"


def test_promote_teamlead_then_assign_when_rbac_on(client, sale_payload):
    settings.room_rbac_disabled = False
    try:
        room_id, slots = _ready(client, sale_payload, headers=FOUNDER)
        promo = client.post(
            f"/api/v1/rooms/{room_id}/members",
            json={"freelancer_sub": "teamlead-demo-sub", "role": "teamlead"},
            headers=FOUNDER,
        )
        assert promo.status_code == 200, promo.text
        assert promo.json()["role"] == "teamlead"

        open_slot = next(s for s in slots if s["status"] == "open")
        _upsert(client, "freelancer-demo-sub", "Alice")
        r = _assign(
            client, room_id, open_slot["id"], "freelancer-demo-sub", TEAMLEAD
        )
        assert r.status_code == 200, r.text
    finally:
        settings.room_rbac_disabled = True


def test_member_403_assign_when_rbac_on(client, sale_payload):
    settings.room_rbac_disabled = False
    try:
        room_id, slots = _ready(client, sale_payload, headers=FOUNDER)
        _upsert(client, "freelancer-demo-sub", "Alice")
        _upsert(client, "other-demo-sub", "Bob")
        first, second = [s for s in slots if s["status"] == "open"][:2]
        assert _assign(
            client, room_id, first["id"], "freelancer-demo-sub", FOUNDER
        ).status_code == 200
        r = _assign(
            client, room_id, second["id"], "other-demo-sub", MEMBER
        )
        assert r.status_code == 403, r.text
        assert r.json()["detail"] == "forbidden_role"
    finally:
        settings.room_rbac_disabled = True


def test_member_can_start_own_task_not_create(client, sale_payload):
    settings.room_rbac_disabled = False
    try:
        room_id, slots = _ready(client, sale_payload, headers=FOUNDER)
        _upsert(client, "freelancer-demo-sub", "Alice")
        open_slot = next(s for s in slots if s["status"] == "open")
        _assign(client, room_id, open_slot["id"], "freelancer-demo-sub", FOUNDER)

        denied = client.post(
            f"/api/v1/rooms/{room_id}/tasks",
            json={"title": "nope", "assignee_sub": "freelancer-demo-sub"},
            headers=MEMBER,
        )
        assert denied.status_code == 403
        assert denied.json()["detail"] == "forbidden_role"

        created = client.post(
            f"/api/v1/rooms/{room_id}/tasks",
            json={"title": "own work", "assignee_sub": "freelancer-demo-sub"},
            headers=FOUNDER,
        )
        assert created.status_code == 201, created.text
        task_id = created.json()["id"]

        started = client.post(
            f"/api/v1/rooms/{room_id}/tasks/{task_id}/start",
            headers=MEMBER,
        )
        assert started.status_code == 200, started.text

        other = client.post(
            f"/api/v1/rooms/{room_id}/tasks",
            json={"title": "staff task"},
            headers=FOUNDER,
        )
        assert other.status_code == 201
        blocked = client.post(
            f"/api/v1/rooms/{room_id}/tasks/{other.json()['id']}/start",
            headers=MEMBER,
        )
        assert blocked.status_code == 403
        assert blocked.json()["detail"] == "forbidden_role"
    finally:
        settings.room_rbac_disabled = True


def test_viewer_role_on_room_read(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    as_founder = client.get(f"/api/v1/rooms/{room_id}", headers=FOUNDER)
    assert as_founder.status_code == 200
    body = as_founder.json()
    assert body["viewer_role"] == "founder"
    assert body["rbac_enforced"] is False

    settings.room_rbac_disabled = False
    try:
        strict = client.get(f"/api/v1/rooms/{room_id}", headers=FOUNDER)
        assert strict.json()["rbac_enforced"] is True
        assert strict.json()["viewer_role"] == "founder"
        stranger = client.get(f"/api/v1/rooms/{room_id}", headers=STRANGER)
        assert stranger.json()["viewer_role"] is None
    finally:
        settings.room_rbac_disabled = True


def test_stranger_403_chat_when_rbac_on(client, sale_payload):
    settings.room_rbac_disabled = False
    try:
        room_id = _handoff(client, sale_payload)
        r = client.post(
            f"/api/v1/rooms/{room_id}/messages",
            json={"body": "hello"},
            headers=STRANGER,
        )
        assert r.status_code == 403
        assert r.json()["detail"] == "forbidden_role"
        ok = client.post(
            f"/api/v1/rooms/{room_id}/messages",
            json={"body": "from founder"},
            headers=FOUNDER,
        )
        assert ok.status_code == 201, ok.text
    finally:
        settings.room_rbac_disabled = True
