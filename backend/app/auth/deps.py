"""FastAPI dependencies (C8): Bearer JWT -> CurrentUser + shadow User upsert.

require_user  — router-level guard for /api/v1/* (401 when AUTH_DISABLED=false).
get_actor_sub — actor of a mutation: JWT sub when auth is on,
                X-Actor-Sub header only when AUTH_DISABLED=true (legacy/tests).
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt import TokenError, verify_token
from app.config import settings
from app.db.models import User
from app.db.session import get_db

_401_HEADERS = {"WWW-Authenticate": "Bearer"}


@dataclass(frozen=True)
class CurrentUser:
    sub: str
    display_name: str | None = None
    email: str | None = None


def _bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401, detail="Bearer token required", headers=_401_HEADERS
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=401, detail="Bearer token required", headers=_401_HEADERS
        )
    return token.strip()


def upsert_shadow_user(db: Session, user: CurrentUser) -> User:
    """Find or create `users` row by Keycloak sub (first authenticated request)."""
    row = db.get(User, user.sub)
    if row is None:
        row = User(sub=user.sub, display_name=user.display_name)
        db.add(row)
    elif user.display_name and row.display_name != user.display_name:
        row.display_name = user.display_name
    db.commit()
    return row


def require_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> CurrentUser | None:
    """Guard for client routes /api/v1/*: valid JWT -> shadow user upserted.

    AUTH_DISABLED=true (dev/tests) -> no-op, C1–C7 behavior unchanged.
    /health and /internal/v1/* must NOT depend on this.
    """
    if settings.auth_disabled:
        return None
    try:
        claims = verify_token(_bearer_token(authorization))
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc), headers=_401_HEADERS) from exc
    current = CurrentUser(
        sub=str(claims["sub"]),
        display_name=claims.get("name") or claims.get("preferred_username"),
        email=claims.get("email"),
    )
    upsert_shadow_user(db, current)
    return current


def get_actor_sub(
    x_actor_sub: str | None = Header(default=None, alias="X-Actor-Sub"),
    user: CurrentUser | None = Depends(require_user),
) -> str:
    """Actor of a mutating request.

    Auth on  -> sub from JWT (X-Actor-Sub ignored, no header required).
    Auth off -> X-Actor-Sub header stays mandatory (422), as in C1–C7.
    """
    if settings.auth_disabled:
        if x_actor_sub is None or not x_actor_sub.strip():
            raise HTTPException(status_code=422, detail="X-Actor-Sub header is required")
        return x_actor_sub.strip()
    if user is None:  # pragma: no cover — require_user already answered 401
        raise HTTPException(status_code=401, detail="Bearer token required", headers=_401_HEADERS)
    return user.sub


def get_optional_actor_sub(
    x_actor_sub: str | None = Header(default=None, alias="X-Actor-Sub"),
    user: CurrentUser | None = Depends(require_user),
) -> str | None:
    """Actor when present; never 422. Used for GET room viewer_role and C27 optional guards."""
    if settings.auth_disabled:
        if x_actor_sub is None or not x_actor_sub.strip():
            return None
        return x_actor_sub.strip()
    if user is None:
        return None
    return user.sub
