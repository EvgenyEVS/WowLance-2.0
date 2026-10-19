"""C15 task assignee из roster: create/start/assign валидируют sub в freelancer_roster."""

from __future__ import annotations

import uuid

ACTOR = {"X-Actor-Sub": "teamlead-demo-sub"}
FREELANCER = {"X-Actor-Sub": "freelancer-demo-sub"}
PROOF = {"proof_uri": "https://example.com/proof.txt"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _upsert(client, sub: str, name: str = "Demo Freelancer") -> dict:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _create(client, room_id: str, title: str = "Call 20 leads", **extra) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": title, **extra},
        headers=ACTOR,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _assign(client, room_id: str, task_id: str, sub: str) -> object:
    return client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/assign",
        json={"assignee_sub": sub},
        headers=ACTOR,
    )


def test_create_with_roster_sub_ok(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")

    created = _create(client, room_id, assignee_sub="f-1")
    assert created["assignee_sub"] == "f-1"
    assert created["status"] == "todo"


def test_create_without_roster_sub_404(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": "Ghost task", "assignee_sub": "ghost-sub"},
        headers=ACTOR,
    )
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "freelancer_not_in_roster"


def test_create_without_assignee_ok(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    created = _create(client, room_id)
    assert created["assignee_sub"] is None


def test_start_actor_in_roster_fills_assignee(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")
    task_id = _create(client, room_id)["id"]

    started = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=FREELANCER
    )
    assert started.status_code == 200, started.text
    assert started.json()["status"] == "in_progress"
    assert started.json()["assignee_sub"] == "freelancer-demo-sub"


def test_start_actor_not_in_roster_404(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    # roster is empty — no freelancers upserted
    task_id = _create(client, room_id)["id"]

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start",
        headers={"X-Actor-Sub": "ghost-sub"},
    )
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "freelancer_not_in_roster"


def test_start_keeps_explicit_assignee(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    created = _create(client, room_id, assignee_sub="f-1")
    task_id = created["id"]

    started = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=FREELANCER
    )
    assert started.status_code == 200
    assert started.json()["assignee_sub"] == "f-1"


def test_assign_on_todo_ok(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    task_id = _create(client, room_id)["id"]

    r = _assign(client, room_id, task_id, "f-1")
    assert r.status_code == 200, r.text
    assert r.json()["assignee_sub"] == "f-1"
    assert r.json()["status"] == "todo"


def test_assign_on_in_progress_ok(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")
    _upsert(client, "f-1", "Bob")
    task_id = _create(client, room_id)["id"]

    client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=FREELANCER
    )
    r = _assign(client, room_id, task_id, "f-1")
    assert r.status_code == 200, r.text
    assert r.json()["assignee_sub"] == "f-1"
    assert r.json()["status"] == "in_progress"


def test_assign_on_submitted_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")
    _upsert(client, "f-1", "Bob")
    task_id = _create(client, room_id)["id"]

    client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=FREELANCER
    )
    client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=PROOF,
        headers=FREELANCER,
    )

    r = _assign(client, room_id, task_id, "f-1")
    assert r.status_code == 409, r.text


def test_assign_on_done_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "freelancer-demo-sub", "Alice")
    _upsert(client, "f-1", "Bob")
    task_id = _create(client, room_id)["id"]

    client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=FREELANCER
    )
    client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=PROOF,
        headers=FREELANCER,
    )
    client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/accept", headers=ACTOR
    )

    r = _assign(client, room_id, task_id, "f-1")
    assert r.status_code == 409, r.text


def test_assign_without_roster_404(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]

    r = _assign(client, room_id, task_id, "ghost-sub")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "freelancer_not_in_roster"


def test_assign_unknown_task_404(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")

    r = _assign(client, room_id, str(uuid.uuid4()), "f-1")
    assert r.status_code == 404, r.text


def test_regression_qg_complete_accept_reject(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    task_id = _create(client, room_id, assignee_sub="f-1")["id"]

    started = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=FREELANCER
    )
    assert started.status_code == 200

    submitted = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=PROOF,
        headers=FREELANCER,
    )
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "submitted"

    accepted = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/accept", headers=ACTOR
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "done"

    # reject on done → 409
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/reject", headers=ACTOR
    )
    assert r.status_code == 409


def test_regression_roster_and_slot_assign_untouched(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    _upsert(client, "f-1", "Alice")

    roster = client.get("/api/v1/roster")
    assert roster.status_code == 200
    assert len(roster.json()["members"]) == 1
    assert roster.json()["members"][0]["freelancer_sub"] == "f-1"
