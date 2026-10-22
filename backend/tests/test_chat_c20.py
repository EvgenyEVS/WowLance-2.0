"""C20 room chat: GET/POST messages in a room."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.db.models import RoomMessage

ACTOR = {"X-Actor-Sub": "freelancer-demo-sub"}


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code in (200, 201), r.text
    return r.json()["room_id"]


def _post_message(client, room_id: str, body: str, headers=None) -> dict:
    h = dict(ACTOR)
    if headers is not None:
        h.update(headers)
    r = client.post(
        f"/api/v1/rooms/{room_id}/messages",
        json={"body": body},
        headers=h,
    )
    return r


def _list_messages(client, room_id: str, limit: int | None = None):
    params = {}
    if limit is not None:
        params["limit"] = limit
    return client.get(
        f"/api/v1/rooms/{room_id}/messages", params=params or None
    )


def test_post_then_list_contains_message(client, sale_payload):
    room_id = _handoff(client, sale_payload)

    r = _post_message(client, room_id, "Hello, team!")
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["body"] == "Hello, team!"
    assert created["author_sub"] == "freelancer-demo-sub"
    assert created["room_id"] == room_id
    assert created["id"] is not None
    assert created["created_at"] is not None

    listed = _list_messages(client, room_id)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["room_id"] == room_id
    assert [m["id"] for m in body["messages"]] == [created["id"]]
    assert body["messages"][0]["body"] == "Hello, team!"
    assert body["messages"][0]["author_sub"] == "freelancer-demo-sub"


def test_multiple_messages_ordered_oldest_first(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    bodies = ["first", "second", "third"]
    for b in bodies:
        _post_message(client, room_id, b)

    listed = _list_messages(client, room_id)
    assert listed.status_code == 200
    msgs = listed.json()["messages"]
    assert [m["body"] for m in msgs] == bodies


def test_limit_respected(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    for i in range(5):
        _post_message(client, room_id, f"msg {i}")

    listed = _list_messages(client, room_id, limit=3)
    assert listed.status_code == 200
    bodies = [m["body"] for m in listed.json()["messages"]]
    assert bodies == ["msg 2", "msg 3", "msg 4"]


def test_unknown_room_404(client, sale_payload):
    r = _post_message(client, str(uuid.uuid4()), "body")
    assert r.status_code == 404, r.text

    listed = _list_messages(client, str(uuid.uuid4()))
    assert listed.status_code == 404


def test_empty_body_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    r = _post_message(client, room_id, "")
    assert r.status_code == 422, r.text


def test_body_over_max_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    r = _post_message(client, room_id, "x" * 2001)
    assert r.status_code == 422, r.text


def test_missing_actor_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    r = client.post(
        f"/api/v1/rooms/{room_id}/messages",
        json={"body": "body"},
        headers={},  # no X-Actor-Sub -> 422 when AUTH_DISABLED=true
    )
    assert r.status_code == 422, r.text


def test_room_read_regression(client, sale_payload):
    """Room read still works after adding messages table."""
    room_id = _handoff(client, sale_payload)
    _post_message(client, room_id, "hello")

    room = client.get(f"/api/v1/rooms/{room_id}")
    assert room.status_code == 200
    assert room.json()["id"] == room_id


def test_messages_persist_in_db(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)
    _post_message(client, room_id, "persist me")

    rows = db_session.scalars(select(RoomMessage)).all()
    assert len(rows) == 1
    assert rows[0].body == "persist me"
    assert rows[0].author_sub == "freelancer-demo-sub"
    assert rows[0].room_id == uuid.UUID(room_id)
