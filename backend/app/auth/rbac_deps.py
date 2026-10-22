"""FastAPI dependencies for C27 room-role guards."""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_actor_sub, get_optional_actor_sub
from app.db.session import get_db
from app.domain.rbac import (
    ActorRequiredError,
    ForbiddenRoleError,
    ROLES_ALL,
    ROLES_STAFF,
    RoomNotFoundError,
    require_role,
    require_task_work,
)


def map_rbac(exc: Exception) -> None:
    if isinstance(exc, RoomNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ActorRequiredError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if isinstance(exc, ForbiddenRoleError):
        raise HTTPException(status_code=403, detail="forbidden_role") from exc
    raise exc


def require_staff(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor_sub),
) -> str:
    try:
        require_role(db, room_id, actor, ROLES_STAFF)
    except (RoomNotFoundError, ActorRequiredError, ForbiddenRoleError) as exc:
        map_rbac(exc)
    return actor


def require_staff_optional(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str | None = Depends(get_optional_actor_sub),
) -> str | None:
    """For endpoints that historically had no X-Actor-Sub (materialize/match)."""
    try:
        require_role(db, room_id, actor, ROLES_STAFF)
    except (RoomNotFoundError, ActorRequiredError, ForbiddenRoleError) as exc:
        map_rbac(exc)
    return actor


def require_member(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor_sub),
) -> str:
    try:
        require_role(db, room_id, actor, ROLES_ALL)
    except (RoomNotFoundError, ActorRequiredError, ForbiddenRoleError) as exc:
        map_rbac(exc)
    return actor


def require_task_worker(
    room_id: uuid.UUID,
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor_sub),
) -> str:
    try:
        require_task_work(db, room_id, task_id, actor)
    except (RoomNotFoundError, ActorRequiredError, ForbiddenRoleError) as exc:
        map_rbac(exc)
    return actor
