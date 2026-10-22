"""Pydantic models mirroring OpenSpec contracts under contracts/ (см. contracts/REGISTRY.md)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoomType(str, Enum):
    sale = "sale"
    develop = "develop"


class ProjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    timezone: str = "Europe/Moscow"


class StrategyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offer: str
    audience: str
    hot_criteria: str
    utp: str | None = None


class DocumentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    uri: str
    checksum: str


class StaffingSlotIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_key: str | None = None
    count: int | None = Field(default=None, ge=1)
    level_min: str | None = None


class StaffingIntentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    package_code: str | None = None
    slots: list[StaffingSlotIn] | None = None


class CommercialIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: UUID | None = None
    entitlement_required: bool = True


class FounderHandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    handoff_id: UUID
    strategy_id: UUID
    strategy_version: str = Field(min_length=1)
    founder_sub: str = Field(min_length=1)
    room_type: RoomType
    project: ProjectIn
    strategy: StrategyIn
    documents: list[DocumentIn] | None = None
    staffing_intent: StaffingIntentIn | None = None
    commercial: CommercialIn | None = None


class HandoffStatus(str, Enum):
    created = "created"
    already_exists = "already_exists"


class FounderHandoffResponse(BaseModel):
    room_id: UUID
    status: HandoffStatus
    staffing_unlocked: bool


class EntitlementSource(str, Enum):
    order = "order"
    payments = "payments"
    stub = "stub"


class EntitlementGrantedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entitlement_id: UUID
    room_id: UUID
    order_id: UUID | None = None
    source: EntitlementSource = EntitlementSource.stub


class EntitlementStatus(str, Enum):
    granted = "granted"
    already_granted = "already_granted"


class EntitlementGrantedResponse(BaseModel):
    room_id: UUID
    staffing_unlocked: Literal[True] = True
    status: EntitlementStatus


class RoomDocumentOut(BaseModel):
    role: str
    uri: str
    checksum: str


class RoomStrategyOut(BaseModel):
    strategy_id: UUID
    strategy_version: str
    offer: str
    audience: str
    hot_criteria: str
    utp: str | None = None
    documents: list[RoomDocumentOut] | None = None
    staffing_intent: dict[str, Any] | None = None


class PendingStrategyOut(BaseModel):
    proposal_id: UUID
    strategy_version: str
    offer: str
    audience: str
    hot_criteria: str
    status: Literal["pending"] = "pending"


class RoomReadResponse(BaseModel):
    id: UUID
    name: str
    room_type: RoomType
    timezone: str
    founder_sub: str
    handoff_id: UUID
    staffing_unlocked: bool
    meeting_url: str | None = None
    strategy: RoomStrategyOut
    pending_strategy: PendingStrategyOut | None = None
    created_at: datetime


class SlotStatus(str, Enum):
    open = "open"
    filled = "filled"
    cancelled = "cancelled"


class FunctionSlotOut(BaseModel):
    id: UUID
    room_id: UUID
    role_key: str
    seat_index: int
    level_min: str | None = None
    status: SlotStatus
    freelancer_sub: str | None = None


class StaffingSlotsListResponse(BaseModel):
    room_id: UUID
    staffing_unlocked: Literal[True] = True
    slots: list[FunctionSlotOut]


class MaterializeStatus(str, Enum):
    materialized = "materialized"
    already_materialized = "already_materialized"


class StaffingMaterializeResponse(BaseModel):
    room_id: UUID
    status: MaterializeStatus
    slots: list[FunctionSlotOut]


class RematerializeStatus(str, Enum):
    rematerialized = "rematerialized"
    already_synced = "already_synced"


class StaffingRematerializeResponse(BaseModel):
    room_id: UUID
    status: RematerializeStatus
    slots: list[FunctionSlotOut]
    orphaned_filled: list[FunctionSlotOut] = []


class StrategyPublishedRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    publication_id: UUID
    room_id: UUID
    strategy_id: UUID
    strategy_version: str = Field(min_length=1)
    strategy: StrategyIn
    documents: list[DocumentIn] | None = None
    staffing_intent: StaffingIntentIn | None = None


class PublicationStatus(str, Enum):
    pending = "pending"
    already_exists = "already_exists"


class StrategyPublishedResponse(BaseModel):
    proposal_id: UUID
    room_id: UUID
    status: PublicationStatus


class StrategyDecision(str, Enum):
    accepted = "accepted"
    rejected = "rejected"


class StrategyDecideResponse(BaseModel):
    proposal_id: UUID
    room_id: UUID
    decision: StrategyDecision
    active_strategy_version: str


class RosterSource(str, Enum):
    stub = "stub"
    talent = "talent"


class RosterUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    freelancer_sub: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    skills: list[str] | None = None
    level: str | None = None
    source: RosterSource = RosterSource.stub


class RosterUpsertStatus(str, Enum):
    upserted = "upserted"
    already_exists = "already_exists"


class RosterUpsertResponse(BaseModel):
    freelancer_sub: str
    status: RosterUpsertStatus


class RosterMemberOut(BaseModel):
    freelancer_sub: str
    display_name: str
    skills: list[str] | None = None
    level: str | None = None
    source: RosterSource = RosterSource.stub


class RosterListResponse(BaseModel):
    members: list[RosterMemberOut]


class SlotAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    freelancer_sub: str = Field(min_length=1)


class AssignStatus(str, Enum):
    assigned = "assigned"
    already_assigned = "already_assigned"


class SlotAssignResponse(BaseModel):
    slot: FunctionSlotOut
    status: AssignStatus


class UnassignStatus(str, Enum):
    unassigned = "unassigned"


class SlotUnassignResponse(BaseModel):
    slot: FunctionSlotOut
    status: UnassignStatus


class ReassignStatus(str, Enum):
    reassigned = "reassigned"
    already_assigned = "already_assigned"


class SlotReassignResponse(BaseModel):
    slot: FunctionSlotOut
    status: ReassignStatus


class MatchCandidateOut(BaseModel):
    freelancer_sub: str
    display_name: str
    skills: list[str] | None = None
    level: str | None = None
    score: int


class SlotMatchResponse(BaseModel):
    slot_id: UUID
    candidates: list[MatchCandidateOut]


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    submitted = "submitted"
    done = "done"


class RoomTaskOut(BaseModel):
    id: UUID
    room_id: UUID
    title: str
    status: TaskStatus
    assignee_sub: str | None = None
    proof_uri: str | None = None
    proof_note: str | None = None
    reviewed_by_sub: str | None = None
    review_note: str | None = None
    created_at: datetime
    updated_at: datetime


class RoomTaskListResponse(BaseModel):
    room_id: UUID
    tasks: list[RoomTaskOut]


class RoomTaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    assignee_sub: str | None = None


class RoomTaskAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignee_sub: str = Field(min_length=1)


class RoomTaskCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proof_uri: str = Field(min_length=1)
    proof_note: str | None = None


class RoomTaskRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_note: str | None = None


class LeadStatus(str, Enum):
    open = "open"
    hot = "hot"
    handed_to_crm = "handed_to_crm"


class RoomLeadOut(BaseModel):
    id: UUID
    room_id: UUID
    title: str
    contact_name: str | None = None
    contact_email: str | None = None
    notes: str | None = None
    status: LeadStatus
    crm_ref: str | None = None
    deal_status: str | None = None
    deal_amount: str | None = None  # decimal as string
    deal_currency: str | None = None
    deal_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RoomLeadListResponse(BaseModel):
    room_id: UUID
    leads: list[RoomLeadOut]


class RoomLeadCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    contact_name: str | None = None
    contact_email: str | None = None
    notes: str | None = None


class LeadHandoffStatus(str, Enum):
    handed = "handed"
    already_handed = "already_handed"


class LeadHandoffResponse(BaseModel):
    lead: RoomLeadOut
    crm_ref: str
    status: LeadHandoffStatus


class RoomHealthRoomOut(BaseModel):
    room_type: RoomType
    name: str
    staffing_unlocked: bool
    strategy_id: UUID | None = None
    strategy_version: str | None = None


class RoomHealthSlotsOut(BaseModel):
    total: int = 0
    open: int = 0
    filled: int = 0
    cancelled: int = 0


class RoomHealthTasksOut(BaseModel):
    todo: int = 0
    in_progress: int = 0
    submitted: int = 0
    done: int = 0


class RoomHealthLeadsOut(BaseModel):
    total: int = 0
    hot: int = 0
    handed_to_crm: int = 0


class RoomHealthEarningsOut(BaseModel):
    total_amount: str = "0.00"
    currency: str
    entries_count: int = 0


class RoomHealthOut(BaseModel):
    room_id: UUID
    captured_at: datetime
    room: RoomHealthRoomOut
    slots: RoomHealthSlotsOut
    tasks: RoomHealthTasksOut
    leads: RoomHealthLeadsOut
    earnings: RoomHealthEarningsOut


class RoomHealthPublishStatus(str, Enum):
    published = "published"


class RoomHealthPublishResponse(BaseModel):
    outbox_id: UUID
    event_type: Literal["RoomHealthSnapshot"]
    status: RoomHealthPublishStatus
    snapshot: RoomHealthOut


class MeetStatus(str, Enum):
    created = "created"
    already_exists = "already_exists"


class MeetEnsureResponse(BaseModel):
    meeting_url: str
    status: MeetStatus


class EarningsEntryOut(BaseModel):
    id: UUID
    room_id: UUID
    task_id: UUID
    freelancer_sub: str
    amount: str  # decimal as string
    currency: str
    source: str
    created_at: datetime


class EarningsListResponse(BaseModel):
    room_id: UUID
    total_amount: str  # decimal as string
    currency: str
    entries: list[EarningsEntryOut]


class DealStatus(str, Enum):
    won = "won"
    lost = "lost"
    in_progress = "in_progress"
    unknown = "unknown"


class CrmDealStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crm_ref: str = Field(min_length=1)
    deal_status: DealStatus
    amount: float | None = None
    currency: str | None = None


class CrmDealStatusResponse(BaseModel):
    room_id: UUID
    lead_id: UUID
    crm_ref: str
    deal_status: str
    deal_amount: str | None = None  # decimal as string
    deal_currency: str | None = None
    deal_updated_at: datetime | None = None


class TerminateMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1)
    slot_id: UUID | None = None


class TerminateMemberResponse(BaseModel):
    status: str  # "terminated"
    freelancer_sub: str
    slot_ids: list[UUID]


class RoomTerminationOut(BaseModel):
    id: UUID
    room_id: UUID
    freelancer_sub: str
    reason: str
    terminated_by_sub: str
    slot_ids: list[UUID]
    created_at: datetime


class RoomTerminationListResponse(BaseModel):
    room_id: UUID
    terminations: list[RoomTerminationOut]


class RoomMessageOut(BaseModel):
    id: UUID
    room_id: UUID
    author_sub: str
    body: str
    created_at: datetime


class RoomMessageListResponse(BaseModel):
    room_id: UUID
    messages: list[RoomMessageOut]


class RoomMessageCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=1, max_length=2000)
