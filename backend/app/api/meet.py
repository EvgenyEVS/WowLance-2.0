"""C14 meet API: POST /api/v1/rooms/{room_id}/meet/ensure (stub Jitsi).

Client route under /api/v1 — guarded by require_user in main.py (C8).
Idempotent: repeat ensure returns the same url, status=already_exists.
Unknown room -> 404. Does not touch handoff/outbox (C11).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.rbac_deps import require_member
from app.db.session import get_db
from app.domain.meet import RoomNotFoundError, ensure_meeting
from app.domain.schemas import MeetEnsureResponse

router = APIRouter(prefix="/api/v1", tags=["meet"])


@router.post(
    "/rooms/{room_id}/meet/ensure",
    response_model=MeetEnsureResponse,
    responses={
        200: {"description": "meeting_url ensured (created / already_exists)"},
        404: {"description": "room_id does not exist"},
    },
)
def ensure_meet(
    room_id: uuid.UUID,
    actor_sub: str = Depends(require_member),
    db: Session = Depends(get_db),
) -> MeetEnsureResponse:
    """POST /api/v1/rooms/{room_id}/meet/ensure — stub Jitsi ensure."""
    try:
        meeting_url, status = ensure_meeting(db, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MeetEnsureResponse(meeting_url=meeting_url, status=status)
