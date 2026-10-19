"""C14 meet domain: ensure a stub Jitsi meeting URL for a room.

Idempotent: first ensure generates + saves the url (`status: created`);
repeat ensure returns the same url (`status: already_exists`). Unknown
room -> 404. Does not touch handoff/outbox/RoomCreated (C11) — parallel
clean slice: new column + new module only.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.adapters.meet_stub import build_meeting_url
from app.db.models import Room


class RoomNotFoundError(Exception):
    """No room for the given id."""


def ensure_meeting(db: Session, room_id: uuid.UUID) -> tuple[str, str]:
    """Return (meeting_url, status) where status is 'created' or 'already_exists'.

    Raises RoomNotFoundError when the room does not exist.
    """
    room = db.get(Room, room_id)
    if room is None:
        raise RoomNotFoundError("room_id does not exist")

    if room.meeting_url:
        return room.meeting_url, "already_exists"

    meeting_url = build_meeting_url(room_id)
    room.meeting_url = meeting_url
    db.commit()
    return meeting_url, "created"
