"""Room leads API (C9). Mutations require the X-Actor-Sub stub -> 422 without it."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.rbac_deps import require_staff
from app.db.session import get_db
from app.domain.leads import (
    InvalidTransitionError,
    LeadNotFoundError,
    LeadNotEligibleError,
    RoomNotFoundError,
    apply_deal_status,
    create_lead,
    handoff_to_crm,
    list_leads,
    mark_hot,
)
from app.stub_log import log_stub
from app.domain.schemas import (
    CrmDealStatusRequest,
    CrmDealStatusResponse,
    LeadHandoffResponse,
    RoomLeadCreateRequest,
    RoomLeadListResponse,
    RoomLeadOut,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["leads"])
crm_router = APIRouter(prefix="/internal/v1/crm", tags=["crm"])


def _map_errors(exc: Exception) -> None:
    if isinstance(exc, (RoomNotFoundError, LeadNotFoundError)):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, InvalidTransitionError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    raise exc


@router.get(
    "/{room_id}/leads",
    response_model=RoomLeadListResponse,
    responses={
        200: {"description": "Leads of the room"},
        404: {"description": "room_id does not exist"},
    },
)
def get_room_leads(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RoomLeadListResponse:
    try:
        return list_leads(db, room_id)
    except RoomNotFoundError as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/leads",
    response_model=RoomLeadOut,
    status_code=201,
    responses={
        201: {"description": "Lead created in open"},
        404: {"description": "room_id does not exist"},
        422: {"description": "validation or missing X-Actor-Sub"},
    },
)
def post_room_lead(
    room_id: uuid.UUID,
    payload: RoomLeadCreateRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(require_staff),
) -> RoomLeadOut:
    try:
        return create_lead(db, room_id, payload)
    except RoomNotFoundError as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/leads/{lead_id}/mark-hot",
    response_model=RoomLeadOut,
    responses={
        200: {"description": "open -> hot"},
        404: {"description": "room or lead does not exist"},
        409: {"description": "lead is not open"},
        422: {"description": "missing X-Actor-Sub"},
    },
)
def post_mark_hot(
    room_id: uuid.UUID,
    lead_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(require_staff),
) -> RoomLeadOut:
    try:
        return mark_hot(db, room_id, lead_id, actor)
    except (RoomNotFoundError, LeadNotFoundError, InvalidTransitionError) as exc:
        _map_errors(exc)
        raise


@router.post(
    "/{room_id}/leads/{lead_id}/handoff-crm",
    response_model=LeadHandoffResponse,
    responses={
        200: {"description": "hot -> handed_to_crm (+ outbox); repeat -> already_handed"},
        404: {"description": "room or lead does not exist"},
        409: {"description": "lead is not hot yet"},
        422: {"description": "missing X-Actor-Sub"},
    },
)
def post_handoff_crm(
    room_id: uuid.UUID,
    lead_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(require_staff),
) -> LeadHandoffResponse:
    try:
        return handoff_to_crm(db, room_id, lead_id, actor)
    except (RoomNotFoundError, LeadNotFoundError, InvalidTransitionError) as exc:
        _map_errors(exc)
        raise


@crm_router.post(
    "/deal-status",
    response_model=CrmDealStatusResponse,
    responses={
        200: {"description": "deal-status applied (idempotent)"},
        404: {"description": "crm_ref does not match any lead"},
        409: {"description": "lead is not in handed_to_crm (lead_not_handed)"},
        422: {"description": "validation failed"},
    },
)
def post_crm_deal_status(
    payload: CrmDealStatusRequest,
    db: Session = Depends(get_db),
) -> CrmDealStatusResponse:
    """POST /internal/v1/crm/deal-status — inbound CRM deal-status stub."""
    try:
        lead = apply_deal_status(
            db,
            crm_ref=payload.crm_ref,
            deal_status=payload.deal_status.value,
            amount=payload.amount,
            currency=payload.currency,
        )
    except LeadNotFoundError as exc:
        log_stub("crm_deal_status", "not_found", crm_ref=payload.crm_ref)
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LeadNotEligibleError as exc:
        log_stub("crm_deal_status", "conflict", crm_ref=payload.crm_ref)
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    log_stub(
        "crm_deal_status",
        "applied",
        room_id=lead.room_id,
        crm_ref=lead.crm_ref,
    )

    return CrmDealStatusResponse(
        room_id=lead.room_id,
        lead_id=lead.id,
        crm_ref=lead.crm_ref or "",
        deal_status=lead.deal_status,
        deal_amount=str(lead.deal_amount) if lead.deal_amount is not None else None,
        deal_currency=lead.deal_currency,
        deal_updated_at=lead.deal_updated_at,
    )
