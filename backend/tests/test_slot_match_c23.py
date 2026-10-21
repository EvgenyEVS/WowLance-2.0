"""C23 Matching lite: GET …/slots/{slot_id}/match shortlist из локального roster."""

from __future__ import annotations

import copy
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


def _upsert(client, sub: str, skills: list[str] | None = None, level: str | None = None, name: str = "Freelancer") -> dict:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name, "skills": skills, "level": level},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _assign(client, room_id: str, slot_id: str, sub: str):
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/assign",
        json={"freelancer_sub": sub},
        headers=ACTOR,
    )


def _match(client, room_id: str, slot_id: str, limit: int | None = None):
    params = f"?limit={limit}" if limit is not None else ""
    return client.get(f"/api/v1/rooms/{room_id}/slots/{slot_id}/match{params}")


def _ready_room(client, sale_payload) -> tuple[str, list[dict]]:
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    return room_id, _materialize(client, room_id)


def test_match_returns_ordered_shortlist(client, sale_payload):
    """DoD #1: roster с skills → match отдаёт упорядоченный shortlist."""
    room_id, slots = _ready_room(client, sale_payload)
    open_slot = slots[0]

    _upsert(client, "f-a", skills=["seller", "cold"], level="B", name="Alpha")
    _upsert(client, "f-b", skills=["seller"], level="A", name="Beta")
    _upsert(client, "f-c", skills=["designer"], level="B", name="Gamma")

    r = _match(client, room_id, open_slot["id"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["slot_id"] == open_slot["id"]
    subs = [c["freelancer_sub"] for c in body["candidates"]]
    assert "f-a" in subs and "f-b" in subs and "f-c" in subs

    # Сортировка: score desc, затем freelancer_sub asc.
    scores = [c["score"] for c in body["candidates"]]
    assert scores == sorted(scores, reverse=True)
    for i in range(len(scores) - 1):
        if scores[i] == scores[i + 1]:
            assert body["candidates"][i]["freelancer_sub"] < body["candidates"][i + 1]["freelancer_sub"]

    # Каждый кандидат имеет все обязательные поля.
    for c in body["candidates"]:
        assert set(["freelancer_sub", "display_name", "skills", "level", "score"]).issubset(c.keys())
        assert isinstance(c["score"], int)


def test_match_excludes_seated_freelancer(client, sale_payload):
    """DoD #2: Seated freelancer отсутствует в candidates."""
    room_id, slots = _ready_room(client, sale_payload)
    open_slot = slots[0]
    other_slot = slots[1]

    _upsert(client, "f-1", skills=["seller"], level="B", name="Seated One")
    _upsert(client, "f-2", skills=["seller"], level="B", name="Free One")
    # f-1 седим на другой слот — seated в комнате, но не на целевом слоте.
    assert _assign(client, room_id, other_slot["id"], "f-1").status_code == 200

    r = _match(client, room_id, open_slot["id"])
    assert r.status_code == 200, r.text
    subs = [c["freelancer_sub"] for c in r.json()["candidates"]]
    assert "f-1" not in subs
    assert "f-2" in subs


def test_match_filled_slot_409(client, sale_payload):
    """DoD #3: Filled slot → 409 slot_not_open."""
    room_id, slots = _ready_room(client, sale_payload)
    open_slot = slots[0]

    _upsert(client, "f-1", skills=["seller"], level="B", name="One")
    assert _assign(client, room_id, open_slot["id"], "f-1").status_code == 200

    r = _match(client, room_id, open_slot["id"])
    assert r.status_code == 409, r.text
    assert r.json()["detail"] == "slot_not_open"


def test_match_locked_room_403(client, sale_payload):
    """DoD #4: Locked → 403 staffing_locked."""
    room_id = _handoff(client, sale_payload)
    r = _match(client, room_id, str(uuid.uuid4()))
    assert r.status_code == 403, r.text
    assert r.json()["detail"] == "staffing_locked"


def test_match_unknown_room_404(client):
    r = _match(client, str(uuid.uuid4()), str(uuid.uuid4()))
    assert r.status_code == 404, r.text


def test_match_unknown_slot_404(client, sale_payload):
    room_id, _ = _ready_room(client, sale_payload)
    r = _match(client, room_id, str(uuid.uuid4()))
    assert r.status_code == 404, r.text


def test_match_limit_truncation(client, sale_payload):
    """Limit truncates (default 5, max 20)."""
    room_id, slots = _ready_room(client, sale_payload)
    open_slot = slots[0]

    for i in range(7):
        _upsert(client, f"f-{i:02d}", skills=["seller"], level="B", name=f"Filler {i:02d}")

    r = _match(client, room_id, open_slot["id"], limit=3)
    assert r.status_code == 200, r.text
    assert len(r.json()["candidates"]) == 3

    r = _match(client, room_id, open_slot["id"])
    assert r.status_code == 200
    assert len(r.json()["candidates"]) <= 5


def test_match_regression_assign_after_suggest(client, sale_payload):
    """DoD #5: Регрессия assign после выбора из shortlist."""
    room_id, slots = _ready_room(client, sale_payload)
    open_slot = slots[0]

    _upsert(client, "f-pick", skills=["seller"], level="B", name="Pick Me")
    r = _match(client, room_id, open_slot["id"])
    assert r.status_code == 200
    assert any(c["freelancer_sub"] == "f-pick" for c in r.json()["candidates"])

    # Assign выбранного — существующий эндпоинт.
    ar = _assign(client, room_id, open_slot["id"], "f-pick")
    assert ar.status_code == 200, ar.text
    assert ar.json()["slot"]["status"] == "filled"
    assert ar.json()["slot"]["freelancer_sub"] == "f-pick"

    # Match на том же (теперь filled) слоте → 409.
    mr = _match(client, room_id, open_slot["id"])
    assert mr.status_code == 409
