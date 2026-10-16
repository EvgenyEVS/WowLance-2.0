"""Access token verification (C8): RS256 via Keycloak JWKS or dev stub key.

No RBAC here — «valid JWT -> has sub -> let in». Internal /internal/v1/*
routes intentionally do not use this module (service token later).
"""

from __future__ import annotations

import threading

import jwt as pyjwt
from jwt import PyJWKClient

from app.config import settings

ALGORITHM = "RS256"


class TokenError(Exception):
    """Token missing, malformed, expired, bad signature, issuer or audience."""


_jwks_client: PyJWKClient | None = None
_jwks_lock = threading.Lock()


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    with _jwks_lock:
        if _jwks_client is None or getattr(_jwks_client, "uri", None) != settings.jwks_url:
            _jwks_client = PyJWKClient(settings.jwks_url, cache_keys=True)
        return _jwks_client


def _signing_key(token: str):
    if settings.auth_stub_jwks:
        # Dev only: verify against the in-process stub key (no HTTP self-fetch).
        from app.auth.stub import stub_public_key

        return stub_public_key()
    try:
        return _get_jwks_client().get_signing_key_from_jwt(token).key
    except Exception as exc:  # noqa: BLE001 — network/JWKS errors are all 401-worthy
        raise TokenError(f"JWKS unavailable: {exc}") from exc


def verify_token(token: str) -> dict:
    """Decode and validate an access token; returns claims. Raises TokenError."""
    try:
        claims = pyjwt.decode(
            token,
            _signing_key(token),
            algorithms=[ALGORITHM],
            issuer=settings.keycloak_issuer,
            audience=settings.verify_audience,
            options={"require": ["exp", "iat"]},
        )
    except TokenError:
        raise
    except pyjwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    if not claims.get("sub"):
        raise TokenError("token has no sub claim")
    return claims
