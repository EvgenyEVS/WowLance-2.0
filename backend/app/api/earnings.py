"""C16 earnings API: GET /api/v1/rooms/{room_id}/earnings (stub ledger)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Room
from app.db.session import get_db
from app.domain.earnings import list_room_earnings
from app.domain.schemas import EarningsEntryOut, EarningsListResponse

router = APIRouter(prefix="/api/v1", tags=["earnings"])


@router.get(
    "/rooms/{room_id}/earnings",
    response_model=EarningsListResponse,
    responses={
        200: {"description": "Earnings entries for the room + total"},
        404: {"description": "room_id does not exist"},
    },
)
def list_room_earnings_api(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> EarningsListResponse:
    """GET /api/v1/rooms/{room_id}/earnings — stub ledger list."""
    room = db.get(Room, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="room_id does not exist")

    entries, total, currency = list_room_earnings(db, room_id)
    return EarningsListResponse(
        room_id=room_id,
        total_amount=str(total),
        currency=currency,
        entries=[
            EarningsEntryOut(
                id=e.id,
                room_id=e.room_id,
                task_id=e.task_id,
                freelancer_sub=e.freelancer_sub,
                amount=str(e.amount),
                currency=e.currency,
                source=e.source,
                created_at=e.created_at,
            )
            for e in entries
        ],
    )
