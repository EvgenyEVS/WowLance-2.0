"""C27 room RBAC lite: local membership roles (not Keycloak).

ROOM_RBAC_DISABLED=true (default) → require_role is a no-op so AUTH_DISABLED
demo and the existing pytest suite stay green. Strict tests flip the flag.
"""

from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Room, RoomMember, RoomTask

ROLE_FOUNDER = "founder"
ROLE_TEAMLEAD = "teamlead"
ROLE_MEMBER = "member"

ROLES_STAFF = frozenset({ROLE_FOUNDER, ROLE_TEAMLEAD})
ROLES_ALL = frozenset({ROLE_FOUNDER, ROLE_TEAMLEAD, ROLE_MEMBER})
_RANK = {ROLE_MEMBER: 0, ROLE_TEAMLEAD: 1, ROLE_FOUNDER: 2}


class RoomNotFoundError(Exception):
    """No room for the given id."""


class ActorRequiredError(Exception):
    """RBAC on, but no actor sub was provided."""


class ForbiddenRoleError(Exception):
    """Actor is missing from the room or the role is not allowed."""

    def __init__(self, detail: str = "forbidden_role") -> None:
        super().__init__(detail)
        self.detail = detail


def rbac_enabled() -> bool:
    return not settings.room_rbac_disabled


def get_membership(
    db: Session, room_id: uuid.UUID, user_sub: str
) -> RoomMember | None:
    return db.scalar(
        select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_sub == user_sub,
        )
    )


def upsert_membership(
    db: Session,
    room_id: uuid.UUID,
    user_sub: str,
    role: str,
) -> RoomMember:
    """Insert or keep/upgrade role. Never demote (founder stays founder)."""
    row = get_membership(db, room_id, user_sub)
    if row is None:
        row = RoomMember(room_id=room_id, user_sub=user_sub, role=role)
        db.add(row)
        return row
    if _RANK.get(role, 0) > _RANK.get(row.role, 0):
        row.role = role
    return row


def list_memberships(db: Session, room_id: uuid.UUID) -> list[RoomMember]:
    room = db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")
    return list(
        db.scalars(
            select(RoomMember)
            .where(RoomMember.room_id == room_id)
            .order_by(RoomMember.created_at.asc(), RoomMember.user_sub.asc())
        ).all()
    )


def require_role(
    db: Session,
    room_id: uuid.UUID,
    actor_sub: str | None,
    allowed: Iterable[str],
) -> str | None:
    """Return the actor role, or None when RBAC is disabled.

    Missing room → RoomNotFoundError (caller may map to 404).
    Missing actor when enabled → ActorRequiredError.
    Not a member / wrong role → ForbiddenRoleError (403 forbidden_role).
    """
    if not rbac_enabled():
        return None
    if db.get(Room, room_id) is None:
        raise RoomNotFoundError("room_id does not exist")
    if actor_sub is None or not actor_sub.strip():
        raise ActorRequiredError("X-Actor-Sub header is required")
    row = get_membership(db, room_id, actor_sub.strip())
    allowed_set = frozenset(allowed)
    if row is None or row.role not in allowed_set:
        raise ForbiddenRoleError("forbidden_role")
    return row.role


def require_task_work(
    db: Session,
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    actor_sub: str | None,
) -> str | None:
    """Staff may start/complete any task; member only their assignee_sub."""
    role = require_role(db, room_id, actor_sub, ROLES_ALL)
    if role != ROLE_MEMBER:
        return role
    task = db.get(RoomTask, task_id)
    if task is None or task.room_id != room_id:
        return role
    if task.assignee_sub != actor_sub:
        raise ForbiddenRoleError("forbidden_role")
    return role
