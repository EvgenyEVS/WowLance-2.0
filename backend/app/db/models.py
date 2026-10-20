"""SQLAlchemy models for C1–C7: handoff, entitlement, slots, strategy, tasks."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """Shadow identity (Keycloak `sub`). No password / local auth in C1."""

    __tablename__ = "users"

    sub: Mapped[str] = mapped_column(String(255), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    rooms: Mapped[list[Room]] = relationship(back_populates="founder")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="Europe/Moscow"
    )
    founder_sub: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.sub"), nullable=False, index=True
    )
    handoff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    staffing_unlocked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    meeting_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    # Canonical fingerprint of the accepted handoff payload (conflict detection).
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    founder: Mapped[User] = relationship(back_populates="rooms")
    strategy_snapshots: Mapped[list[StrategySnapshot]] = relationship(
        back_populates="room"
    )
    strategy_proposals: Mapped[list[StrategyProposal]] = relationship(
        back_populates="room"
    )
    entitlements: Mapped[list[Entitlement]] = relationship(back_populates="room")
    function_slots: Mapped[list[RoomFunctionSlot]] = relationship(
        back_populates="room"
    )
    tasks: Mapped[list[RoomTask]] = relationship(back_populates="room")
    leads: Mapped[list[RoomLead]] = relationship(back_populates="room")


class StrategySnapshot(Base):
    """Immutable strategy snapshot. History: one active, rest superseded."""

    __tablename__ = "strategy_snapshots"
    __table_args__ = (
        Index(
            "uq_strategy_snapshots_one_active",
            "room_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    documents: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    staffing_intent: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    commercial: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    room: Mapped[Room] = relationship(back_populates="strategy_snapshots")


class StrategyProposal(Base):
    """Inbox of a published strategy version awaiting Accept/Reject."""

    __tablename__ = "strategy_proposals"
    __table_args__ = (
        Index(
            "uq_strategy_proposals_one_pending",
            "room_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    documents: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    staffing_intent: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    decided_by_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)

    room: Mapped[Room] = relationship(back_populates="strategy_proposals")


class Entitlement(Base):
    """Idempotent staffing unlock from Order/Payments (or stub)."""

    __tablename__ = "entitlements"

    entitlement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="stub")
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    room: Mapped[Room] = relationship(back_populates="entitlements")


class RoomFunctionSlot(Base):
    """A purchased/intended seat in the room. C4: open, unassigned."""

    __tablename__ = "room_function_slots"
    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "role_key",
            "seat_index",
            name="uq_room_function_slot_seat",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_key: Mapped[str] = mapped_column(String(64), nullable=False)
    seat_index: Mapped[int] = mapped_column(Integer, nullable=False)
    level_min: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="open", server_default="open"
    )
    freelancer_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    room: Mapped[Room] = relationship(back_populates="function_slots")


class FreelancerRoster(Base):
    """C6: local snapshot of a freelancer (stub Talent). Service-global, not per-room."""

    __tablename__ = "freelancer_roster"

    freelancer_sub: Mapped[str] = mapped_column(String(255), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    skills: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(
        String(32), nullable=False, default="stub", server_default="stub"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RoomTask(Base):
    """Room task tracker: todo -> in_progress -> submitted -> done.

    C7 minimal tracker; C10 Quality Gate lite adds proof_uri/proof_note on
    submit and reviewed_by_sub/review_note on accept/reject.
    assignee_sub is a free string (no FK to roster — that is C6).
    """

    __tablename__ = "room_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="todo", server_default="todo"
    )
    assignee_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    proof_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_sub: Mapped[str | None] = mapped_column(String(255), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    room: Mapped[Room] = relationship(back_populates="tasks")


class RoomLead(Base):
    """C9 lead inside a room. Lifecycle: open -> hot -> handed_to_crm."""

    __tablename__ = "room_leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="open", server_default="open"
    )
    crm_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    room: Mapped[Room] = relationship(back_populates="leads")


class OutboxMessage(Base):
    """Minimal service outbox (C9): HotLeadToCrm persisted with status=sent."""

    __tablename__ = "outbox_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class EarningsEntry(Base):
    """C16 stub earnings ledger: one row per accepted task (UNIQUE task_id)."""

    __tablename__ = "earnings_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("room_tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    freelancer_sub: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    source: Mapped[str] = mapped_column(
        String(32), nullable=False, default="task_accepted"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RoomTermination(Base):
    """C17 termination journal: one row per member termination event."""

    __tablename__ = "room_terminations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    freelancer_sub: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    terminated_by_sub: Mapped[str] = mapped_column(String(255), nullable=False)
    slot_ids: Mapped[list[uuid.UUID]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
