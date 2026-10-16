"""Dev-only auth endpoints (C8): stub JWKS + test token minting.

404 unless AUTH_DISABLED=false and AUTH_STUB_JWKS=true — «not for prod».
Real deployments use Keycloak JWKS (KEYCLOAK_JWKS_URL / issuer).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.auth.stub import mint_token, stub_jwks
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth-stub"])


class StubTokenRequest(BaseModel):
    sub: str = Field(min_length=1, examples=["demo-user"])
    preferred_username: str | None = Field(default=None, examples=["demo"])
    email: str | None = Field(default=None, examples=["demo@example.com"])
    name: str | None = Field(default=None, examples=["Demo User"])


class StubTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    sub: str


def _ensure_stub_enabled() -> None:
    if settings.auth_disabled or not settings.auth_stub_jwks:
        raise HTTPException(status_code=404, detail="stub auth disabled")


@router.get("/stub-jwks", summary="Dev-only JWKS for the in-process stub key")
def get_stub_jwks() -> dict:
    _ensure_stub_enabled()
    return stub_jwks()


@router.post(
    "/stub-token",
    response_model=StubTokenResponse,
    summary="Dev-only: mint an RS256 test access token («token in 2 minutes»)",
)
def post_stub_token(payload: StubTokenRequest) -> StubTokenResponse:
    _ensure_stub_enabled()
    token = mint_token(
        sub=payload.sub,
        preferred_username=payload.preferred_username,
        email=payload.email,
        name=payload.name,
    )
    return StubTokenResponse(access_token=token, sub=payload.sub)
