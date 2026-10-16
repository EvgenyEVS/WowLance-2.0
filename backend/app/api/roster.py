"""C6 local roster API: stub upsert (internal) + list for the assign UI.

Internal upsert is open (no Keycloak in C1–C6). Read list is open too.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.roster import list_roster, upsert_roster
from app.domain.schemas import (
    RosterListResponse,
    RosterUpsertRequest,
    RosterUpsertResponse,
)

internal_router = APIRouter(prefix="/internal/v1", tags=["roster"])
router = APIRouter(prefix="/api/v1", tags=["roster"])


@internal_router.post(
    "/roster",
    response_model=RosterUpsertResponse,
    responses={
        200: {"description": "upserted or already_exists (idempotent by sub)"},
        422: {"description": "Schema validation failed"},
    },
)
def post_roster(
    body: RosterUpsertRequest,
    db: Session = Depends(get_db),
) -> RosterUpsertResponse:
    """POST /internal/v1/roster — Talent -> WowLance (stub, TalentRosterUpsert v1)."""
    return upsert_roster(db, body)


@router.get(
    "/roster",
    response_model=RosterListResponse,
    responses={200: {"description": "Local roster snapshot"}},
)
def get_roster(db: Session = Depends(get_db)) -> RosterListResponse:
    """GET /api/v1/roster — list for the assign picker."""
    return list_roster(db)
