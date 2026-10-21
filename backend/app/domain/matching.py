"""C23 Matching lite: shortlist кандидатов из локального roster для open слота.

Читает только локальный roster. Live Talent API не вызывается. Match не меняет БД.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FreelancerRoster, Room, RoomFunctionSlot
from app.domain.schemas import MatchCandidateOut, SlotMatchResponse
from app.domain.staffing import (
    SlotNotFoundError,
    _require_unlocked_room,
)

DEFAULT_LIMIT = 5
MAX_LIMIT = 20


class SlotNotOpenError(Exception):
    """Slot is not open (match requires an open slot)."""


def _score_candidate(
    slot: RoomFunctionSlot, row: FreelancerRoster
) -> int:
    score = 0

    # +2 если level_min слота совместим с level фрилансера (или level_min отсутствует = ок).
    if slot.level_min is None:
        score += 2
    elif row.level is not None and row.level == slot.level_min:
        score += 2

    # +1 за каждый skill из role hints (role_key слота), пересекающийся с roster.skills.
    hints = [slot.role_key] if slot.role_key else []
    roster_skills = set(row.skills or [])
    score += len(set(hints) & roster_skills)

    return score


def match_candidates(
    db: Session,
    room_id: uuid.UUID,
    slot_id: uuid.UUID,
    limit: Optional[int] = None,
) -> SlotMatchResponse:
    """Вернуть shortlist кандидатов для open слота (чистое чтение, без записи в БД)."""
    if limit is None:
        limit = DEFAULT_LIMIT
    limit = max(1, min(limit, MAX_LIMIT))

    room = _require_unlocked_room(db, room_id)

    slot = db.get(RoomFunctionSlot, slot_id)
    if slot is None or slot.room_id != room.id:
        raise SlotNotFoundError("slot_id does not exist in this room")
    if slot.status != "open":
        raise SlotNotOpenError("slot_not_open")

    # Кандидаты: все из roster, кроме уже seated в этой комнате.
    seated_subs = set(
        db.scalars(
            select(RoomFunctionSlot.freelancer_sub).where(
                RoomFunctionSlot.room_id == room.id,
                RoomFunctionSlot.status == "filled",
                RoomFunctionSlot.freelancer_sub.is_not(None),
            )
        ).all()
    )

    rows = list(
        db.scalars(
            select(FreelancerRoster).order_by(FreelancerRoster.freelancer_sub)
        ).all()
    )

    scored: list[tuple[int, str, MatchCandidateOut]] = []
    for row in rows:
        if row.freelancer_sub in seated_subs:
            continue
        score = _score_candidate(slot, row)
        scored.append(
            (
                score,
                row.freelancer_sub,
                MatchCandidateOut(
                    freelancer_sub=row.freelancer_sub,
                    display_name=row.display_name,
                    skills=row.skills,
                    level=row.level,
                    score=score,
                ),
            )
        )

    scored.sort(key=lambda item: (-item[0], item[1]))
    top = [item[2] for item in scored[:limit]]

    return SlotMatchResponse(slot_id=slot.id, candidates=top)
