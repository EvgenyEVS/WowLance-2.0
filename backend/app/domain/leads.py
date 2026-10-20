"""C9 leads: create -> open -> hot -> handed_to_crm + local outbox row.

No live CRM: `app.adapters.crm_stub` builds the payload, we persist an
`outbox_messages` row (event_type=HotLeadToCrm, status=sent) and return a
fake `crm_ref`. Idempotency key = lead_id.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.crm_stub import build_hot_lead_payload, crm_ref_for
from app.db.models import OutboxMessage, Room, RoomLead
from app.domain.schemas import (
    LeadHandoffResponse,
    LeadHandoffStatus,
    LeadStatus,
    RoomLeadCreateRequest,
    RoomLeadListResponse,
    RoomLeadOut,
)

LIST_LIMIT = 100
HOT_LEAD_EVENT = "HotLeadToCrm"


class RoomNotFoundError(Exception):
    """No room for the given id."""


class LeadNotFoundError(Exception):
    """No lead for the given (room_id, lead_id)."""


class LeadNotHandledError(Exception):
    """Lid not in handed_to_crm; deal-status cannot be applied (lead_not_handed)."""


class InvalidTransitionError(Exception):
    """Requested lead status transition is not allowed."""


def _require_room(db: Session, room_id: uuid.UUID) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    return room


def _require_lead(db: Session, room_id: uuid.UUID, lead_id: uuid.UUID) -> RoomLead:
    row = db.get(RoomLead, lead_id)
    if row is None or row.room_id != room_id:
        raise LeadNotFoundError("lead_id does not exist in this room")
    return row


def _lead_out(row: RoomLead) -> RoomLeadOut:
    return RoomLeadOut(
        id=row.id,
        room_id=row.room_id,
        title=row.title,
        contact_name=row.contact_name,
        contact_email=row.contact_email,
        notes=row.notes,
        status=LeadStatus(row.status),
        crm_ref=row.crm_ref,
        deal_status=row.deal_status,
        deal_amount=str(row.deal_amount) if row.deal_amount is not None else None,
        deal_currency=row.deal_currency,
        deal_updated_at=row.deal_updated_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def list_leads(db: Session, room_id: uuid.UUID) -> RoomLeadListResponse:
    room = _require_room(db, room_id)
    rows = list(
        db.scalars(
            select(RoomLead)
            .where(RoomLead.room_id == room.id)
            .order_by(RoomLead.created_at, RoomLead.id)
            .limit(LIST_LIMIT)
        ).all()
    )
    return RoomLeadListResponse(room_id=room.id, leads=[_lead_out(r) for r in rows])


def create_lead(
    db: Session, room_id: uuid.UUID, payload: RoomLeadCreateRequest
) -> RoomLeadOut:
    room = _require_room(db, room_id)
    row = RoomLead(
        id=uuid.uuid4(),
        room_id=room.id,
        title=payload.title,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        notes=payload.notes,
        status=LeadStatus.open.value,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _lead_out(row)


def mark_hot(
    db: Session, room_id: uuid.UUID, lead_id: uuid.UUID, actor_sub: str
) -> RoomLeadOut:
    row = _require_lead(db, room_id, lead_id)
    if row.status != LeadStatus.open.value:
        raise InvalidTransitionError("only an open lead can be marked hot")
    row.status = LeadStatus.hot.value
    db.commit()
    db.refresh(row)
    return _lead_out(row)


def handoff_to_crm(
    db: Session, room_id: uuid.UUID, lead_id: uuid.UUID, actor_sub: str
) -> LeadHandoffResponse:
    room = _require_room(db, room_id)
    lead = _require_lead(db, room_id, lead_id)

    if lead.status == LeadStatus.handed_to_crm.value:
        # Idempotent repeat: same crm_ref, no second outbox row.
        return LeadHandoffResponse(
            lead=_lead_out(lead),
            crm_ref=lead.crm_ref or crm_ref_for(lead.id),
            status=LeadHandoffStatus.already_handed,
        )
    if lead.status != LeadStatus.hot.value:
        raise InvalidTransitionError("only a hot lead can be handed off to CRM")

    handed_at = datetime.now(timezone.utc)
    payload = build_hot_lead_payload(lead, room, handed_at)
    key = str(lead.id)
    existing = db.scalar(
        select(OutboxMessage).where(OutboxMessage.idempotency_key == key)
    )
    if existing is None:
        db.add(
            OutboxMessage(
                id=uuid.uuid4(),
                event_type=HOT_LEAD_EVENT,
                idempotency_key=key,
                payload=payload,
                status="sent",
                sent_at=handed_at,
            )
        )

    lead.status = LeadStatus.handed_to_crm.value
    lead.crm_ref = crm_ref_for(lead.id)
    db.commit()
    db.refresh(lead)
    return LeadHandoffResponse(
        lead=_lead_out(lead),
        crm_ref=lead.crm_ref,
        status=LeadHandoffStatus.handed,
    )


def apply_deal_status(
    db: Session,
    crm_ref: str,
    deal_status: str,
    amount,
    currency: str | None,
) -> RoomLeadOut:
    """C19: apply CRM deal-status to a handed_to_crm lead by crm_ref.

    Idempotent: repeat with the same status → 200, no write.
    Raises LeadNotFoundError (404) / LeadNotHandledError (409).
    """
    lead = db.scalar(
        select(RoomLead).where(RoomLead.crm_ref == crm_ref)
    )
    if lead is None:
        raise LeadNotFoundError("crm_ref does not match any lead")
    if lead.status != LeadStatus.handed_to_crm.value:
        raise LeadNotHandledError("lead_not_handed")

    already = (
        lead.deal_status == deal_status
        and lead.deal_currency == currency
        and (
            lead.deal_amount is None
            if amount is None
            else lead.deal_amount == Decimal(str(amount))
        )
    )
    if already:
        return _lead_out(lead)

    updated_at = datetime.now(timezone.utc)
    lead.deal_status = deal_status
    if amount is not None:
        lead.deal_amount = Decimal(str(amount))
    lead.deal_currency = currency
    lead.deal_updated_at = updated_at
    db.commit()
    db.refresh(lead)
    return _lead_out(lead)
