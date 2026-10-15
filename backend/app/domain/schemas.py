"""Pydantic models mirroring contracts/wowlance/FounderHandoff.v1.yaml."""

from __future__ import annotations

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
