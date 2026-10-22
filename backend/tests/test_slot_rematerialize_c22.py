"""C22 Slot rematerialize: sync seats к активному staffing_intent после Accept."""

from __future__ import annotations

import copy
import json
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISH_EXAMPLE = (
    REPO_ROOT / "contracts" / "strategy" / "examples" / "StrategyPublished.sale.json"
)
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


def _rematerialize(client, room_id: str):
    return client.post(f"/api/v1/rooms/{room_id}/slots/rematerialize")


def _upsert(client, sub: str, name: str = "Demo Freelancer") -> dict:
    r = client.post(
        "/internal/v1/roster",
        json={"freelancer_sub": sub, "display_name": name},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _assign(client, room_id: str, slot_id: str, sub: str):
    return client.post(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}/assign",
        json={"freelancer_sub": sub},
        headers=ACTOR,
    )


def _publish(
    client,
    room_id: str,
    staffing_intent: dict,
    publication_id: str | None = None,
    strategy_version: str | None = None,
) -> str:
    body = json.loads(PUBLISH_EXAMPLE.read_text(encoding="utf-8"))
    body["room_id"] = room_id
    body["publication_id"] = publication_id or str(uuid.uuid4())
    if strategy_version is not None:
        body["strategy_version"] = strategy_version
    body["staffing_intent"] = staffing_intent
    r = client.post("/internal/v1/strategy-publications", json=body)
    assert r.status_code == 200, r.text
    return r.json()["proposal_id"]


def _accept(client, room_id: str, proposal_id: str):
    r = client.post(
        f"/api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/accept",
        headers=ACTOR,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _ready_room(client, sale_payload) -> tuple[str, list[dict]]:
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)
    return room_id, _materialize(client, room_id)


def test_rematerialize_bigger_intent_adds_open_seats(client, sale_payload):
    """DoD #1: intent A (2) → Accept с большим count (3) → rematerialize → 3 open."""
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)

    slots = _materialize(client, room_id)
    assert len(slots) == 2
    assert all(s["status"] == "open" for s in slots)

    proposal_id = _publish(
        client,
        room_id,
        {"package_code": "cold_calling_base", "slots": [{"role_key": "seller", "count": 3, "level_min": "B"}]},
    )
    _accept(client, room_id, proposal_id)

    r = _rematerialize(client, room_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "rematerialized"
    assert len(body["slots"]) == 3
    assert [s["seat_index"] for s in body["slots"]] == [1, 2, 3]
    assert all(s["status"] == "open" for s in body["slots"])
    assert body["orphaned_filled"] == []


def test_rematerialize_smaller_intent_cancel_open_orphan_filled(client, sale_payload):
    """DoD #2: уменьшение intent — лишние open → cancelled, filled → orphaned_filled."""
    room_id = _handoff(client, sale_payload)
    _unlock(client, room_id)

    proposal_id = _publish(
        client,
        room_id,
        {"package_code": "cold_calling_base", "slots": [{"role_key": "seller", "count": 3, "level_min": "B"}]},
    )
    _accept(client, room_id, proposal_id)
    slots = _materialize(client, room_id)
    assert len(slots) == 3

    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[1]["id"], "f-1").status_code == 200  # seat #2 filled

    proposal_id = _publish(
        client,
        room_id,
        {"package_code": "cold_calling_base", "slots": [{"role_key": "seller", "count": 1, "level_min": "B"}]},
        strategy_version="2026-10-20.1",
    )
    _accept(client, room_id, proposal_id)

    r = _rematerialize(client, room_id)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "rematerialized"
    by_id = {s["id"]: s for s in body["slots"]}
    assert by_id[slots[0]["id"]]["status"] == "open"  # seat #1 в intent — остался open
    assert by_id[slots[2]["id"]]["status"] == "cancelled"  # seat #3 лишний open → cancelled
    assert by_id[slots[1]["id"]]["status"] == "filled"  # seat #2 filled — не тронут
    assert len(body["orphaned_filled"]) == 1
    assert body["orphaned_filled"][0]["id"] == slots[1]["id"]
    assert body["orphaned_filled"][0]["freelancer_sub"] == "f-1"


def test_rematerialize_locked_room_403(client, sale_payload):
    """DoD #3: без entitlement → 403 staffing_locked."""
    room_id = _handoff(client, sale_payload)
    r = _rematerialize(client, room_id)
    assert r.status_code == 403, r.text
    assert r.json()["detail"] == "staffing_locked"


def test_rematerialize_unknown_room_404(client):
    r = _rematerialize(client, str(uuid.uuid4()))
    assert r.status_code == 404, r.text


def test_rematerialize_no_changes_already_synced(client, sale_payload):
    """DoD #4: повтор rematerialize без изменений → already_synced."""
    room_id, slots = _ready_room(client, sale_payload)

    r1 = _rematerialize(client, room_id)
    assert r1.status_code == 200
    assert r1.json()["status"] == "already_synced"
    assert len(r1.json()["slots"]) == len(slots)

    r2 = _rematerialize(client, room_id)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_synced"


def test_rematerialize_regression_unassign_still_works(client, sale_payload):
    """DoD #4: C12 unassign регрессия после rematerialize."""
    room_id, slots = _ready_room(client, sale_payload)
    _upsert(client, "f-1", "Alice")
    assert _assign(client, room_id, slots[0]["id"], "f-1").status_code == 200

    r = _rematerialize(client, room_id)
    assert r.status_code == 200

    un = client.post(
        f"/api/v1/rooms/{room_id}/slots/{slots[0]['id']}/unassign",
        headers=ACTOR,
    )
    assert un.status_code == 200, un.text
    assert un.json()["slot"]["status"] == "open"
    assert un.json()["slot"]["freelancer_sub"] is None
