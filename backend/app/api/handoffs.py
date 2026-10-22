"""Internal FounderHandoff endpoint.

Auth: open in C1 (no Keycloak). Intended behind API Gateway / service token later.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.handoff import HandoffConflictError, process_founder_handoff
from app.domain.schemas import FounderHandoffRequest, FounderHandoffResponse
from app.stub_log import log_stub

router = APIRouter(prefix="/internal/v1", tags=["handoffs"])


@router.post(
    "/handoffs",
    response_model=FounderHandoffResponse,
    responses={
        201: {"description": "Room created"},
        200: {"description": "Idempotent replay (already_exists)"},
        409: {"description": "handoff_id bound to different payload"},
        422: {"description": "Schema validation failed"},
    },
)
def create_founder_handoff(
    body: FounderHandoffRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> FounderHandoffResponse:
    """POST /internal/v1/handoffs — Strategy → WowLance (FounderHandoff v1)."""
    try:
        result = process_founder_handoff(db, body)
    except HandoffConflictError as exc:
        log_stub("handoff", "conflict", handoff_id=body.handoff_id)
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    log_stub(
        "handoff",
        result.response.status.value,
        room_id=result.response.room_id,
        handoff_id=body.handoff_id,
    )
    response.status_code = result.http_status
    return result.response
