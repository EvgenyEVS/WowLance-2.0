"""C5 StrategyPublished → Accept/Reject."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from sqlalchemy import select

from app.db.models import StrategySnapshot

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISH_EXAMPLE = (
    REPO_ROOT / "contracts" / "wowlance" / "examples" / "StrategyPublished.sale.json"
)
ACTOR = {"X-Actor-Sub": "teamlead-demo-sub"}
OLD_OFFER = "Outbound cold calling for B2B SaaS"
NEW_OFFER = "Outbound cold calling plus LinkedIn follow-up"
NEW_VERSION = "2026-10-15.2"


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["room_id"]


def _publish_body(room_id: str, **overrides) -> dict:
    body = json.loads(PUBLISH_EXAMPLE.read_text(encoding="utf-8"))
    body["room_id"] = room_id
    body.update(overrides)
    return body


def test_publish_keeps_active_snapshot_until_accept(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    pub = client.post("/internal/v1/strategy-publications", json=_publish_body(room_id))
    assert pub.status_code == 200, pub.text
    assert pub.json()["status"] == "pending"
    proposal_id = pub.json()["proposal_id"]

    room = client.get(f"/api/v1/rooms/{room_id}")
    assert room.status_code == 200
    body = room.json()
    assert body["strategy"]["offer"] == OLD_OFFER
    assert body["strategy"]["strategy_version"] == sale_payload["strategy_version"]
    assert body["pending_strategy"] is not None
    assert body["pending_strategy"]["proposal_id"] == proposal_id
    assert body["pending_strategy"]["offer"] == NEW_OFFER
    assert body["pending_strategy"]["status"] == "pending"


def test_accept_promotes_snapshot(client, db_session, sale_payload):
    room_id = _handoff(client, sale_payload)
    pub = client.post("/internal/v1/strategy-publications", json=_publish_body(room_id))
    proposal_id = pub.json()["proposal_id"]

    acc = client.post(
        f"/api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/accept",
        headers=ACTOR,
    )
    assert acc.status_code == 200, acc.text
    assert acc.json()["decision"] == "accepted"
    assert acc.json()["active_strategy_version"] == NEW_VERSION

    room = client.get(f"/api/v1/rooms/{room_id}").json()
    assert room["strategy"]["offer"] == NEW_OFFER
    assert room["pending_strategy"] is None

    snaps = list(
        db_session.scalars(
            select(StrategySnapshot).where(StrategySnapshot.room_id == uuid.UUID(room_id))
        )
    )
    statuses = {s.status for s in snaps}
    assert statuses == {"active", "superseded"}
    active = next(s for s in snaps if s.status == "active")
    superseded = next(s for s in snaps if s.status == "superseded")
    assert active.strategy_payload["offer"] == NEW_OFFER
    assert superseded.strategy_payload["offer"] == OLD_OFFER


def test_reject_keeps_old_active(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    pub = client.post("/internal/v1/strategy-publications", json=_publish_body(room_id))
    proposal_id = pub.json()["proposal_id"]

    rej = client.post(
        f"/api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/reject",
        headers=ACTOR,
    )
    assert rej.status_code == 200, rej.text
    assert rej.json()["decision"] == "rejected"
    assert rej.json()["active_strategy_version"] == sale_payload["strategy_version"]

    room = client.get(f"/api/v1/rooms/{room_id}").json()
    assert room["strategy"]["offer"] == OLD_OFFER
    assert room["pending_strategy"] is None


def test_second_publish_while_pending_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    first = _publish_body(room_id)
    assert client.post("/internal/v1/strategy-publications", json=first).status_code == 200
    second = _publish_body(room_id, publication_id=str(uuid.uuid4()), strategy_version="other")
    assert client.post("/internal/v1/strategy-publications", json=second).status_code == 409


def test_replay_publication_id_already_exists(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    body = _publish_body(room_id)
    r1 = client.post("/internal/v1/strategy-publications", json=body)
    r2 = client.post("/internal/v1/strategy-publications", json=body)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_exists"
    assert r2.json()["proposal_id"] == r1.json()["proposal_id"]


def test_publish_same_version_as_active_409(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    body = _publish_body(room_id, strategy_version=sale_payload["strategy_version"])
    assert client.post("/internal/v1/strategy-publications", json=body).status_code == 409


def test_accept_without_actor_header_422(client, sale_payload):
    room_id = _handoff(client, sale_payload)
    pub = client.post("/internal/v1/strategy-publications", json=_publish_body(room_id))
    proposal_id = pub.json()["proposal_id"]
    r = client.post(
        f"/api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/accept"
    )
    assert r.status_code == 422
