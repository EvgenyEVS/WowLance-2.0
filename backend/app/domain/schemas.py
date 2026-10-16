"""Pydantic models mirroring OpenSpec contracts under contracts/wowlance/."""

from __future__ import annotations

from datetime import datetime
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


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class RoomTaskOut(BaseModel):
    id: UUID
    room_id: UUID
    title: str
    status: TaskStatus
    assignee_sub: str | None = None
    created_at: datetime
    updated_at: datetime


class RoomTaskListResponse(BaseModel):
    room_id: UUID
    tasks: list[RoomTaskOut]


class RoomTaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    assignee_sub: str | None = None
