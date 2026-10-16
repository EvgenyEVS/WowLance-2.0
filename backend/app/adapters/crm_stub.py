"""C9 stub CRM adapter: build the HotLeadToCrm payload and a fake crm_ref.

No live CRM HTTP, no OAuth, no Keycloak — see
`contracts/wowlance/HotLeadToCrm.v1.yaml`. Outbox persistence is done by
`app.domain.leads`; this module only shapes the outgoing event.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from app.db.models import Room, RoomLead

CRM_REF_PREFIX = "crm-stub"


def crm_ref_for(lead_id: uuid.UUID) -> str:
    """Fake CRM reference: `crm-stub:<lead_id>` (contract §4.6)."""
    return f"{CRM_REF_PREFIX}:{lead_id}"


def build_hot_lead_payload(
    lead: RoomLead, room: Room, handed_at: datetime
) -> dict:
    """HotLeadToCrm payload exactly as declared in the contract."""
    return {
        "lead_id": str(lead.id),
        "room_id": str(room.id),
        "title": lead.title,
        "contact_name": lead.contact_name,
        "contact_email": lead.contact_email,
        "notes": lead.notes,
        "founder_sub": room.founder_sub,
        "room_name": room.name,
        "handed_at": handed_at.isoformat(),
    }
