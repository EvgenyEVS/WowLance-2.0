"""C27 room members: list + founder promote to teamlead."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_actor_sub
from app.auth.rbac_deps import map_rbac
from app.db.models import Room
from app.db.session import get_db
from app.domain.rbac import (
    ActorRequiredError,
    ForbiddenRoleError,
    ROLE_FOUNDER,
    RoomNotFoundError,
    list_memberships,
    require_role,
    upsert_membership,
)
from app.domain.schemas import (
    RoomMemberListResponse,
    RoomMemberOut,
    RoomMemberPromoteRequest,
    RoomMemberRole,
)

router = APIRouter(prefix="/api/v1/rooms", tags=["members"])


def _out(row) -> RoomMemberOut:
    return RoomMemberOut(
        user_sub=row.user_sub,
        role=RoomMemberRole(row.role),
        created_at=row.created_at,
    )


@router.get(
    "/{room_id}/members",
    response_model=RoomMemberListResponse,
    responses={
        200: {"description": "Membership list"},
        404: {"description": "room_id does not exist"},
    },
)
def get_room_members(
    room_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RoomMemberListResponse:
    try:
        rows = list_memberships(db, room_id)
    except RoomNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RoomMemberListResponse(
        room_id=room_id,
        members=[_out(row) for row in rows],
    )


@router.post(
    "/{room_id}/members",
    response_model=RoomMemberOut,
    responses={
        200: {"description": "teamlead upserted"},
        403: {"description": "forbidden_role"},
        404: {"description": "room_id does not exist"},
        422: {"description": "validation or missing actor"},
    },
)
def post_room_member(
    room_id: uuid.UUID,
    payload: RoomMemberPromoteRequest,
    db: Session = Depends(get_db),
    actor: str = Depends(get_actor_sub),
) -> RoomMemberOut:
    try:
        if db.get(Room, room_id) is None:
            raise RoomNotFoundError("room_id does not exist")
        require_role(db, room_id, actor, {ROLE_FOUNDER})
        row = upsert_membership(db, room_id, payload.freelancer_sub, payload.role)
        db.commit()
        db.refresh(row)
    except (RoomNotFoundError, ActorRequiredError, ForbiddenRoleError) as exc:
        map_rbac(exc)
        raise
    return _out(row)
