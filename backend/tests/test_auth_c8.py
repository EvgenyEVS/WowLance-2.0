"""C8 auth: strict mode (AUTH_DISABLED=false + stub JWKS) vs open dev mode.

Regression C1–C7 with AUTH_DISABLED=true lives in the other test modules
(conftest forces it). Here: 401/200 cases, shadow upsert, open /health + internal.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.auth.stub import mint_token
from app.config import settings
from app.db.models import User

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISH_EXAMPLE = (
    REPO_ROOT / "contracts" / "wowlance" / "examples" / "StrategyPublished.sale.json"
)


@pytest.fixture()
def strict_auth(monkeypatch):
    """Auth enabled: strict Bearer + dev stub JWKS/token minting (no real Keycloak)."""
    monkeypatch.setattr(settings, "auth_disabled", False)
    monkeypatch.setattr(settings, "auth_stub_jwks", True)
    return settings


def _handoff(client, payload: dict) -> str:
    r = client.post("/internal/v1/handoffs", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["room_id"]


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _publish_body(room_id: str) -> dict:
    body = json.loads(PUBLISH_EXAMPLE.read_text(encoding="utf-8"))
    body["room_id"] = room_id
    return body


# --- 401 cases ---------------------------------------------------------------


def test_get_room_401_without_token(client, sale_payload, strict_auth):
    room_id = _handoff(client, sale_payload)

    r = client.get(f"/api/v1/rooms/{room_id}")
    assert r.status_code == 401, r.text
    assert r.headers.get("WWW-Authenticate") == "Bearer"


def test_get_room_401_malformed_token(client, sale_payload, strict_auth):
    room_id = _handoff(client, sale_payload)

    assert client.get(f"/api/v1/rooms/{room_id}", headers=_bearer("not-a-jwt")).status_code == 401
    # wrong scheme is not Bearer
    assert client.get(f"/api/v1/rooms/{room_id}", headers={"Authorization": "Token abc"}).status_code == 401


def test_get_room_401_expired_token(client, sale_payload, strict_auth):
    room_id = _handoff(client, sale_payload)
    expired = mint_token(sub="demo", ttl_seconds=-10)

    r = client.get(f"/api/v1/rooms/{room_id}", headers=_bearer(expired))
    assert r.status_code == 401, r.text


def test_get_room_401_wrong_audience(client, sale_payload, strict_auth, monkeypatch):
    room_id = _handoff(client, sale_payload)
    token = mint_token(sub="demo")  # aud = wowlance-api
    monkeypatch.setattr(settings, "keycloak_audience", "another-api")

    r = client.get(f"/api/v1/rooms/{room_id}", headers=_bearer(token))
    assert r.status_code == 401, r.text


def test_mutation_401_without_token(client, sale_payload, strict_auth):
    room_id = _handoff(client, sale_payload)

    r = client.post(f"/api/v1/rooms/{room_id}/tasks", json={"title": "T1"})
    assert r.status_code == 401, r.text


# --- 200 with a valid token --------------------------------------------------


def test_get_room_200_with_stub_jwt(client, sale_payload, strict_auth):
    room_id = _handoff(client, sale_payload)
    token = mint_token(sub="jwt-founder-sub", name="Demo Founder")

    r = client.get(f"/api/v1/rooms/{room_id}", headers=_bearer(token))
    assert r.status_code == 200, r.text
    assert r.json()["id"] == room_id


def test_shadow_user_upserted_on_first_request(client, db_session, sale_payload, strict_auth):
    room_id = _handoff(client, sale_payload)
    token = mint_token(sub="shadow-sub-1", name="First Name")

    assert client.get(f"/api/v1/rooms/{room_id}", headers=_bearer(token)).status_code == 200
    db_session.expire_all()
    user = db_session.get(User, "shadow-sub-1")
    assert user is not None
    assert user.display_name == "First Name"

    renamed = mint_token(sub="shadow-sub-1", name="Second Name")
    assert client.get(f"/api/v1/rooms/{room_id}", headers=_bearer(renamed)).status_code == 200
    db_session.expire_all()
    users = [u for u in db_session.query(User).all() if u.sub == "shadow-sub-1"]
    assert len(users) == 1
    assert users[0].display_name == "Second Name"


def test_mutation_actor_is_jwt_sub_not_header(client, db_session, sale_payload, strict_auth):
    """X-Actor-Sub is ignored when auth is on: decided_by_sub comes from JWT."""
    import uuid as uuid_mod

    from app.db.models import StrategyProposal

    room_id = _handoff(client, sale_payload)
    pub = client.post("/internal/v1/strategy-publications", json=_publish_body(room_id))
    assert pub.status_code == 200, pub.text
    proposal_id = pub.json()["proposal_id"]

    r = client.post(
        f"/api/v1/rooms/{room_id}/strategy-proposals/{proposal_id}/accept",
        headers={
            **_bearer(mint_token(sub="jwt-actor-sub")),
            "X-Actor-Sub": "header-should-lose",
        },
    )
    assert r.status_code == 200, r.text

    db_session.expire_all()
    proposal = db_session.get(StrategyProposal, uuid_mod.UUID(proposal_id))
    assert proposal is not None
    assert proposal.decided_by_sub == "jwt-actor-sub"


# --- open surfaces -----------------------------------------------------------


def test_health_and_internal_open_when_strict(client, sale_payload, strict_auth):
    assert client.get("/health").status_code == 200

    room_id = _handoff(client, sale_payload)  # no token on /internal/v1/handoffs
    assert client.post(
        "/internal/v1/strategy-publications", json=_publish_body(room_id)
    ).status_code == 200


# --- dev stub endpoints ------------------------------------------------------


def test_stub_endpoints_404_when_auth_disabled(client):
    assert client.get("/auth/stub-jwks").status_code == 404
    assert client.post("/auth/stub-token", json={"sub": "demo"}).status_code == 404


def test_stub_token_flow(client, sale_payload, strict_auth):
    """«Token in 2 minutes»: mint at /auth/stub-token, call API with it."""
    room_id = _handoff(client, sale_payload)

    mint = client.post("/auth/stub-token", json={"sub": "demo", "name": "Demo"})
    assert mint.status_code == 200, mint.text
    token = mint.json()["access_token"]

    r = client.get(f"/api/v1/rooms/{room_id}", headers=_bearer(token))
    assert r.status_code == 200, r.text

    jwks = client.get("/auth/stub-jwks")
    assert jwks.status_code == 200
    assert jwks.json()["keys"][0]["kty"] == "RSA"
