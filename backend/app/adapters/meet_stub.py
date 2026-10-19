"""C14 stub Jitsi meet adapter: build a meet URL for a room.

No live Jitsi Admin API, no JWT in the link, no recording — see
`contracts/wowlance/RoomMeet.v1.yaml`. The base URL comes from
`MEET_BASE_URL` env, defaulting to `https://meet.jit.si`.
"""

from __future__ import annotations

import os
import uuid

MEET_BASE_URL = os.getenv("MEET_BASE_URL", "https://meet.jit.si").rstrip("/")


def build_meeting_url(room_id: uuid.UUID) -> str:
    """Stub Jitsi URL: `{MEET_BASE_URL}/wowlance-{room_id}`."""
    return f"{MEET_BASE_URL}/wowlance-{room_id}"
