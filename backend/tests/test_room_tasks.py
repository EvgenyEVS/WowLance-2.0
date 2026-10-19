"""C7 room tasks: tracker todo -> in_progress -> submitted -> done (C10 gate)."""

from __future__ import annotations

import uuid

ACTOR = {"X-Actor-Sub": "teamlead-demo-sub"}
FREELANCER = {"X-Actor-Sub": "freelancer-demo-sub"}
PROOF = {"proof_uri": "https://example.com/proof.txt"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _create(client, room_id: str, title: str = "Call 20 leads", **extra) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": title, **extra},
        headers=ACTOR,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_create_and_list_contains_todo(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    created = _create(client, room_id)
    assert created["status"] == "todo"
    assert created["assignee_sub"] is None

    listed = client.get(f"/api/v1/rooms/{room_id}/tasks")
    assert listed.status_code == 200
    body = listed.json()
    assert body["room_id"] == room_id
    assert [t["id"] for t in body["tasks"]] == [created["id"]]
    assert body["tasks"][0]["status"] == "todo"


def _start(client, room_id: str, task_id: str, headers=FREELANCER) -> dict:
    # C15: actor must be in roster for start
    client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": headers.get("X-Actor-Sub", ""), "display_name": "Demo Freelancer"},
    )
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=headers
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_start_then_complete_submits_with_proof(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]

    started = _start(client, room_id, task_id)
    assert started["status"] == "in_progress"
    assert started["assignee_sub"] == "freelancer-demo-sub"

    submitted = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=PROOF,
        headers=FREELANCER,
    )
    assert submitted.status_code == 200, submitted.text
    body = submitted.json()
    assert body["status"] == "submitted"
    assert body["proof_uri"] == PROOF["proof_uri"]
    assert body["reviewed_by_sub"] is None


def test_create_keeps_explicit_assignee(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": "pre-assigned-sub", "display_name": "Pre Assigned"},
    )
    created = _create(client, room_id, assignee_sub="pre-assigned-sub")
    assert created["assignee_sub"] == "pre-assigned-sub"

    started = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{created['id']}/start", headers=FREELANCER
    )
    assert started.status_code == 200
    assert started.json()["assignee_sub"] == "pre-assigned-sub"


def test_complete_from_todo_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=PROOF,
        headers=ACTOR,
    )
    assert r.status_code == 409


def test_start_already_submitted_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
            json=PROOF,
            headers=ACTOR,
        ).status_code
        == 200
    )

    r = client.post(f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=ACTOR)
    assert r.status_code == 409


def test_mutation_without_actor_header_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    create = client.post(
        f"/api/v1/rooms/{room_id}/tasks", json={"title": "No actor"}
    )
    assert create.status_code == 422

    task_id = _create(client, room_id)["id"]
    assert (
        client.post(f"/api/v1/rooms/{room_id}/tasks/{task_id}/start").status_code == 422
    )
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
            json=PROOF,
        ).status_code
        == 422
    )


def test_unknown_room_404(client):
    missing = uuid.uuid4()
    assert client.get(f"/api/v1/rooms/{missing}/tasks").status_code == 404
    assert (
        client.post(
            f"/api/v1/rooms/{missing}/tasks",
            json={"title": "x"},
            headers=ACTOR,
        ).status_code
        == 404
    )


def test_unknown_task_404(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    missing_task = uuid.uuid4()
    assert (
        client.post(
            f"/api/v1/rooms/{room_id}/tasks/{missing_task}/start", headers=ACTOR
        ).status_code
        == 404
    )


def test_tasks_available_before_staffing_unlock(client, sale_payload):
    """Tasks do not depend on entitlement (parallel with C6)."""
    room_id = _handoff(client, sale_payload)
    room = client.get(f"/api/v1/rooms/{room_id}").json()
    assert room["staffing_unlocked"] is False

    assert client.get(f"/api/v1/rooms/{room_id}/tasks").status_code == 200
    assert _create(client, room_id)["status"] == "todo"


def test_regression_handoff_and_room_read(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    room = client.get(f"/api/v1/rooms/{room_id}")
    assert room.status_code == 200
    assert room.json()["id"] == room_id
