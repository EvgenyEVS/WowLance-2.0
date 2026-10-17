"""C10 Quality Gate lite: proof on submit, teamlead accept/reject."""

from __future__ import annotations

import uuid

ACTOR = {"X-Actor-Sub": "teamlead-demo-sub"}
FREELANCER = {"X-Actor-Sub": "freelancer-demo-sub"}
PROOF = {"proof_uri": "https://drive.example.com/report.pdf", "proof_note": "see p.3"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _create(client, room_id: str, title: str = "Prepare report") -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": title},
        headers=ACTOR,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _start(client, room_id: str, task_id: str, headers=FREELANCER) -> dict:
    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=headers
    )
    assert r.status_code == 200, r.text
    return r.json()


def _complete(client, room_id: str, task_id: str, body: dict, headers=FREELANCER):
    return client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=body,
        headers=headers,
    )


def test_submit_stores_proof(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)

    r = _complete(client, room_id, task_id, PROOF)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "submitted"
    assert body["proof_uri"] == PROOF["proof_uri"]
    assert body["proof_note"] == PROOF["proof_note"]
    assert body["reviewed_by_sub"] is None
    assert body["review_note"] is None


def test_complete_without_proof_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)

    assert _complete(client, room_id, task_id, {}).status_code == 422
    assert _complete(client, room_id, task_id, {"proof_note": "no uri"}).status_code == 422
    assert _complete(client, room_id, task_id, {"proof_uri": ""}).status_code == 422

    current = client.get(f"/api/v1/rooms/{room_id}/tasks").json()["tasks"][0]
    assert current["status"] == "in_progress"


def test_accept_submitted_done(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    assert _complete(client, room_id, task_id, PROOF).status_code == 200

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/accept", headers=ACTOR
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "done"
    assert body["reviewed_by_sub"] == "teamlead-demo-sub"
    assert body["proof_uri"] == PROOF["proof_uri"]


def test_reject_keeps_proof_and_allows_resubmit(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    assert _complete(client, room_id, task_id, PROOF).status_code == 200

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/reject",
        json={"review_note": "missing pages"},
        headers=ACTOR,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "in_progress"
    assert body["review_note"] == "missing pages"
    assert body["reviewed_by_sub"] == "teamlead-demo-sub"
    assert body["proof_uri"] == PROOF["proof_uri"]

    again = _complete(
        client,
        room_id,
        task_id,
        {"proof_uri": "https://drive.example.com/report-v2.pdf"},
    )
    assert again.status_code == 200
    assert again.json()["status"] == "submitted"


def test_reject_without_body_ok(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    assert _complete(client, room_id, task_id, PROOF).status_code == 200

    r = client.post(f"/api/v1/rooms/{room_id}/tasks/{task_id}/reject", headers=ACTOR)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "in_progress"
    assert r.json()["review_note"] is None


def test_accept_from_in_progress_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/accept", headers=ACTOR
    )
    assert r.status_code == 409


def test_accept_from_todo_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/accept", headers=ACTOR
    )
    assert r.status_code == 409


def test_reject_from_in_progress_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)

    r = client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/reject", headers=ACTOR
    )
    assert r.status_code == 409


def test_direct_in_progress_to_done_forbidden(client, sale_payload):
    """No shortcut: complete -> submitted, never done directly (C10)."""
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    _complete(client, room_id, task_id, PROOF)

    current = client.get(f"/api/v1/rooms/{room_id}/tasks").json()["tasks"][0]
    assert current["status"] == "submitted"


def test_list_returns_proof_fields(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _create(client, room_id)["id"]
    _start(client, room_id, task_id)
    _complete(client, room_id, task_id, PROOF)

    task = client.get(f"/api/v1/rooms/{room_id}/tasks").json()["tasks"][0]
    for field in (
        "proof_uri",
        "proof_note",
        "reviewed_by_sub",
        "review_note",
    ):
        assert field in task


def test_accept_unknown_room_404(client):
    missing_room = uuid.uuid4()
    missing_task = uuid.uuid4()
    r = client.post(
        f"/api/v1/rooms/{missing_room}/tasks/{missing_task}/accept", headers=ACTOR
    )
    assert r.status_code == 404
