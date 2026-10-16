"""C8 auth: Bearer JWT verification (JWKS / dev stub) + shadow User upsert."""

from app.auth.deps import CurrentUser, get_actor_sub, require_user, upsert_shadow_user
from app.auth.jwt import TokenError, verify_token

__all__ = [
    "CurrentUser",
    "TokenError",
    "get_actor_sub",
    "require_user",
    "upsert_shadow_user",
    "verify_token",
]
