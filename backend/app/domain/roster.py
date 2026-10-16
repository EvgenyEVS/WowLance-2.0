"""C6 local roster: stub upsert of freelancers (Talent snapshot). No live Talent."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import FreelancerRoster
from app.domain.schemas import (
    RosterListResponse,
    RosterMemberOut,
    RosterSource,
    RosterUpsertRequest,
    RosterUpsertResponse,
    RosterUpsertStatus,
)

LIST_LIMIT = 200


def _member_out(row: FreelancerRoster) -> RosterMemberOut:
    return RosterMemberOut(
        freelancer_sub=row.freelancer_sub,
        display_name=row.display_name,
        skills=row.skills,
        level=row.level,
        source=RosterSource(row.source),
    )


def upsert_roster(
    db: Session, payload: RosterUpsertRequest
) -> RosterUpsertResponse:
    """Idempotent by freelancer_sub: same payload -> already_exists, else update."""
    row = db.get(FreelancerRoster, payload.freelancer_sub)
    if row is None:
        row = FreelancerRoster(
            freelancer_sub=payload.freelancer_sub,
            display_name=payload.display_name,
            skills=payload.skills,
            level=payload.level,
            source=payload.source.value,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return RosterUpsertResponse(
            freelancer_sub=row.freelancer_sub,
            status=RosterUpsertStatus.upserted,
        )

    unchanged = (
        row.display_name == payload.display_name
        and row.skills == payload.skills
        and row.level == payload.level
        and row.source == payload.source.value
    )
    if unchanged:
        return RosterUpsertResponse(
            freelancer_sub=row.freelancer_sub,
            status=RosterUpsertStatus.already_exists,
        )

    row.display_name = payload.display_name
    row.skills = payload.skills
    row.level = payload.level
    row.source = payload.source.value
    db.commit()
    db.refresh(row)
    return RosterUpsertResponse(
        freelancer_sub=row.freelancer_sub,
        status=RosterUpsertStatus.upserted,
    )


def list_roster(db: Session) -> RosterListResponse:
    rows = list(
        db.scalars(
            select(FreelancerRoster)
            .order_by(FreelancerRoster.display_name, FreelancerRoster.freelancer_sub)
            .limit(LIST_LIMIT)
        ).all()
    )
    return RosterListResponse(members=[_member_out(row) for row in rows])
