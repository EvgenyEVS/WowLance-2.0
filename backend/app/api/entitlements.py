"""Internal EntitlementGranted endpoint.

Auth: open in C2 (no Keycloak), same as C1 handoffs. Intended behind
API Gateway / service token later.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.entitlement import (
    EntitlementRoomConflictError,
    RoomNotFoundError,
    grant_entitlement,
)
from app.domain.schemas import EntitlementGrantedRequest, EntitlementGrantedResponse

router = APIRouter(prefix="/internal/v1", tags=["entitlements"])


@router.post(
    "/entitlements",
    response_model=EntitlementGrantedResponse,
    responses={
        200: {"description": "granted or already_granted"},
        404: {"description": "room_id does not exist"},
        409: {"description": "entitlement_id bound to a different room_id"},
        422: {"description": "Schema validation failed"},
    },
)
def create_entitlement(
    body: EntitlementGrantedRequest,
    db: Session = Depends(get_db),
) -> EntitlementGrantedResponse:
    """POST /internal/v1/entitlements — Order/Payments → WowLance (stub OK)."""
    try:
        result = grant_entitlement(db, body)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EntitlementRoomConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return result.response
