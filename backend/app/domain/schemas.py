"""Pydantic models mirroring contracts/wowlance/FounderHandoff.v1.yaml."""

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
    staffing_unlocked: Literal[False] = False


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


class RoomReadResponse(BaseModel):
    id: UUID
    name: str
    room_type: RoomType
    timezone: str
    founder_sub: str
    handoff_id: UUID
    staffing_unlocked: bool
    strategy: RoomStrategyOut
    created_at: datetime
