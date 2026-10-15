"""SQLAlchemy models for C1 FounderHandoff and C2 Entitlement."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text
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
