from datetime import datetime, timezone

from app.schemas.profile import ProfileRecord


IN_MEMORY_PROFILES: dict[str, list[ProfileRecord]] = {}


def get_profile_history(user_id: str) -> list[ProfileRecord]:
    return IN_MEMORY_PROFILES.get(user_id, [])


def append_profile(user_id: str, skin_type: str, conditions: list[str], confidence: float) -> None:
    history = IN_MEMORY_PROFILES.setdefault(user_id, [])
    history.append(
        ProfileRecord(
            timestamp=datetime.now(timezone.utc),
            skin_type=skin_type,
            conditions=conditions,
            confidence=confidence,
        )
    )
