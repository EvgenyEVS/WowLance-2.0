"""C21 internal service-token guard: X-Service-Token on /internal/v1/*."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings


def test_default_disabled_handoff_ok(client, sale_payload):
    """Регрессия C1: по умолчанию internal открыт, handoff без заголовка — 201."""
    r = client.post("/internal/v1/handoffs", json=sale_payload)
    assert r.status_code == 201, r.text
    assert settings.internal_auth_disabled is True


def test_strict_without_token_401(client, sale_payload):
    """Строгий режим: запрос к /internal/v1/* без X-Service-Token → 401."""
    settings.internal_auth_disabled = False
    settings.internal_service_token = "test-secret"
    try:
        r = client.post(
            "/internal/v1/handoffs",
            json=sale_payload,
            headers={"X-Service-Token": ""},
        )
        assert r.status_code == 401, r.text

        r = client.post("/internal/v1/handoffs", json=sale_payload)
        assert r.status_code == 401, r.text
    finally:
        settings.internal_auth_disabled = True
        settings.internal_service_token = ""


def test_strict_with_valid_token_200(client, sale_payload):
    """Строгий режим: с верным X-Service-Token — как раньше (201)."""
    settings.internal_auth_disabled = False
    settings.internal_service_token = "test-secret"
    try:
        r = client.post(
            "/internal/v1/handoffs",
            json=sale_payload,
            headers={"X-Service-Token": "test-secret"},
        )
        assert r.status_code == 201, r.text
    finally:
        settings.internal_auth_disabled = True
        settings.internal_service_token = ""


def test_strict_wrong_token_401(client, sale_payload):
    """Неверный токен → 401 (не 403)."""
    settings.internal_auth_disabled = False
    settings.internal_service_token = "test-secret"
    try:
        r = client.post(
            "/internal/v1/handoffs",
            json=sale_payload,
            headers={"X-Service-Token": "wrong-secret"},
        )
        assert r.status_code == 401, r.text
    finally:
        settings.internal_auth_disabled = True
        settings.internal_service_token = ""


def test_api_v1_and_health_not_require_service_token(client, sale_payload):
    """C21: /api/v1/* и /health не требуют service token (C8 JWT отдельно)."""
    settings.internal_auth_disabled = False
    settings.internal_service_token = "test-secret"
    try:
        room = client.post(
            "/internal/v1/handoffs",
            json=sale_payload,
            headers={"X-Service-Token": "test-secret"},
        )
        assert room.status_code == 201, room.text
        room_id = room.json()["room_id"]

        # /api/v1/* — без X-Service-Token (C8 JWT отдельно; AUTH_DISABLED=true в тестах)
        r = client.get(f"/api/v1/rooms/{room_id}")
        assert r.status_code == 200, r.text

        # /health — без сервисного токена
        r = client.get("/health")
        assert r.status_code == 200, r.text
    finally:
        settings.internal_auth_disabled = True
        settings.internal_service_token = ""


def test_internal_covers_c18_entitlement_path(client, sale_payload):
    """C18 internal endpoint под тем же префикс-guard."""
    settings.internal_auth_disabled = False
    settings.internal_service_token = "test-secret"
    try:
        room = client.post(
            "/internal/v1/handoffs",
            json=sale_payload,
            headers={"X-Service-Token": "test-secret"},
        )
        assert room.status_code == 201, room.text
        room_id = room.json()["room_id"]

        # C18: entitlement — без токена 401, с токеном 200
        r = client.post(
            "/internal/v1/entitlements",
            json={
                "entitlement_id": "11111111-1111-1111-1111-111111111111",
                "room_id": room_id,
                "source": "stub",
            },
            headers={"X-Service-Token": "wrong"},
        )
        assert r.status_code == 401

        r = client.post(
            "/internal/v1/entitlements",
            json={
                "entitlement_id": "11111111-1111-1111-1111-111111111111",
                "room_id": room_id,
                "source": "stub",
            },
            headers={"X-Service-Token": "test-secret"},
        )
        assert r.status_code == 200, r.text
    finally:
        settings.internal_auth_disabled = True
        settings.internal_service_token = ""
