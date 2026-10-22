"""C30: GET tasks ?status= filter + reject reason survives list refresh."""

from __future__ import annotations

ACTOR = {"X-Actor-Sub": "teamlead-demo-sub"}
FREELANCER = {"X-Actor-Sub": "freelancer-demo-sub"}
PROOF = {"proof_uri": "https://drive.example.com/report.pdf", "proof_note": "see p.3"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _seed_task(client, room_id: str, title: str) -> str:
    client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": "freelancer-demo-sub", "display_name": "Alice"},
    )
    created = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": title},
        headers=ACTOR,
    )
    assert created.status_code == 201, created.text
    task_id = created.json()["id"]
    assert client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/start", headers=FREELANCER
    ).status_code == 200
    return task_id


def test_status_filter_and_rejected_alias(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    todo_id = client.post(
        f"/api/v1/rooms/{room_id}/tasks",
        json={"title": "still todo"},
        headers=ACTOR,
    ).json()["id"]
    submitted_id = _seed_task(client, room_id, "needs review")
    assert client.post(
        f"/api/v1/rooms/{room_id}/tasks/{submitted_id}/complete",
        json=PROOF,
        headers=FREELANCER,
    ).status_code == 200
    rejected_id = _seed_task(client, room_id, "needs rework")
    assert client.post(
        f"/api/v1/rooms/{room_id}/tasks/{rejected_id}/complete",
        json=PROOF,
        headers=FREELANCER,
    ).status_code == 200
    assert client.post(
        f"/api/v1/rooms/{room_id}/tasks/{rejected_id}/reject",
        json={"review_note": "missing pages"},
        headers=ACTOR,
    ).status_code == 200

    todos = client.get(f"/api/v1/rooms/{room_id}/tasks", params={"status": "todo"})
    assert todos.status_code == 200
    assert [t["id"] for t in todos.json()["tasks"]] == [todo_id]

    submitted = client.get(
        f"/api/v1/rooms/{room_id}/tasks", params={"status": "submitted"}
    )
    assert [t["id"] for t in submitted.json()["tasks"]] == [submitted_id]

    rejected = client.get(
        f"/api/v1/rooms/{room_id}/tasks", params={"status": "rejected"}
    )
    assert rejected.status_code == 200
    rows = rejected.json()["tasks"]
    assert [t["id"] for t in rows] == [rejected_id]
    assert rows[0]["status"] == "in_progress"
    assert rows[0]["review_note"] == "missing pages"


def test_reject_reason_visible_on_list_get(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    task_id = _seed_task(client, room_id, "qg")
    assert client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/complete",
        json=PROOF,
        headers=FREELANCER,
    ).status_code == 200
    assert client.post(
        f"/api/v1/rooms/{room_id}/tasks/{task_id}/reject",
        json={"review_note": "need recording"},
        headers=ACTOR,
    ).status_code == 200

    listed = client.get(f"/api/v1/rooms/{room_id}/tasks")
    assert listed.status_code == 200
    row = next(t for t in listed.json()["tasks"] if t["id"] == task_id)
    assert row["status"] == "in_progress"
    assert row["review_note"] == "need recording"
    assert row["proof_uri"] == PROOF["proof_uri"]


def test_unknown_status_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    r = client.get(f"/api/v1/rooms/{room_id}/tasks", params={"status": "nope"})
    assert r.status_code == 422
