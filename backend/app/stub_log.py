"""Structured stub logs for internal POST (C32). No PII payloads."""

from __future__ import annotations

import logging

logger = logging.getLogger("wowlance.stub")


def log_stub(event: str, outcome: str, **fields: object) -> None:
    bits = [f"event={event}", f"outcome={outcome}"]
    for key in (
        "room_id",
        "handoff_id",
        "entitlement_id",
        "crm_ref",
        "strategy_id",
        "proposal_id",
    ):
        val = fields.get(key)
        if val is not None:
            bits.append(f"{key}={val}")
    logger.info(" ".join(bits))
