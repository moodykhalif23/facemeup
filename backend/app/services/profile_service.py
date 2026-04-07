import json
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
            id=row.id,
            created_at=row.created_at,
            skin_type=row.skin_type,
            conditions=[v for v in row.conditions_csv.split(",") if v],
            confidence=row.confidence,
            user_feedback=row.user_feedback,
            questionnaire=json.loads(row.questionnaire_json) if row.questionnaire_json else None,
            skin_type_scores=json.loads(row.skin_type_scores_json) if row.skin_type_scores_json else None,
            condition_scores=json.loads(row.condition_scores_json) if row.condition_scores_json else None,
            inference_mode=row.inference_mode,
            report_image_base64=row.report_image_base64,
            capture_images=json.loads(row.capture_images_json) if row.capture_images_json else None,
        )
        for row in rows
    ]


def append_profile(
    db: Session,
    user_id: str,
    skin_type: str,
    conditions: list[str],
    confidence: float,
    questionnaire: dict | None = None,
    skin_type_scores: dict | None = None,
    condition_scores: dict | None = None,
    inference_mode: str | None = None,
    report_image_base64: str | None = None,
    capture_images: list[str] | None = None,
) -> None:
    row = SkinProfileHistory(
        user_id=user_id,
        skin_type=skin_type,
        conditions_csv=",".join(conditions),
        confidence=confidence,
        questionnaire_json=json.dumps(questionnaire) if questionnaire else None,
        skin_type_scores_json=json.dumps(skin_type_scores) if skin_type_scores else None,
        condition_scores_json=json.dumps(condition_scores) if condition_scores else None,
        inference_mode=inference_mode,
        report_image_base64=report_image_base64,
        capture_images_json=json.dumps(capture_images) if capture_images else None,
    )
    db.add(row)
    db.commit()
