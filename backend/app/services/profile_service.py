from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import SkinProfileHistory
from app.schemas.profile import ProfileRecord


def get_profile_history(db: Session, user_id: str) -> list[ProfileRecord]:
    rows = db.execute(
        select(SkinProfileHistory)
        .where(SkinProfileHistory.user_id == user_id)
        .order_by(SkinProfileHistory.created_at.desc())
    ).scalars()

    return [
        ProfileRecord(
            timestamp=row.created_at,
            skin_type=row.skin_type,
            conditions=[v for v in row.conditions_csv.split(",") if v],
            confidence=row.confidence,
        )
        for row in rows
    ]


def append_profile(db: Session, user_id: str, skin_type: str, conditions: list[str], confidence: float) -> None:
    row = SkinProfileHistory(
        user_id=user_id,
        skin_type=skin_type,
        conditions_csv=",".join(conditions),
        confidence=confidence,
    )
    db.add(row)
    db.commit()
