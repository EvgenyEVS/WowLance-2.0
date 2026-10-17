"""Dev-only RS256 stub: in-memory key, JWKS document, token minting.

Active only when AUTH_DISABLED=false and AUTH_STUB_JWKS=true — «not for prod».
The key lives in process memory; /auth/stub-jwks and /auth/stub-token serve it.
"""

from __future__ import annotations

import base64
import threading
import time

import jwt as pyjwt
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings

KID = "wowlance-stub"
ALGORITHM = "RS256"

_lock = threading.Lock()
_private_key: rsa.RSAPrivateKey | None = None


def _key() -> rsa.RSAPrivateKey:
    global _private_key
    with _lock:
        if _private_key is None:
            _private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        return _private_key


def stub_public_key() -> rsa.RSAPublicKey:
    return _key().public_key()


def _b64url(value: int) -> str:
    length = (value.bit_length() + 7) // 8
    raw = value.to_bytes(length, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def stub_jwks() -> dict:
    numbers = stub_public_key().public_numbers()
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": KID,
                "use": "sig",
                "alg": ALGORITHM,
                "n": _b64url(numbers.n),
                "e": _b64url(numbers.e),
            }
        ]
    }


def mint_token(
    sub: str,
    preferred_username: str | None = None,
    email: str | None = None,
    name: str | None = None,
    ttl_seconds: int = 3600,
) -> str:
    now = int(time.time())
    claims: dict = {
        "sub": sub,
        "iss": settings.keycloak_issuer,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    if settings.keycloak_audience:
        claims["aud"] = settings.keycloak_audience
    for claim_name, value in (
        ("preferred_username", preferred_username),
        ("email", email),
        ("name", name),
    ):
        if value:
            claims[claim_name] = value
    return pyjwt.encode(claims, _key(), algorithm=ALGORITHM, headers={"kid": KID})
