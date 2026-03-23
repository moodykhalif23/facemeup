from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SkinProfileHistory(Base):
    __tablename__ = "skin_profile_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    skin_type: Mapped[str] = mapped_column(String(64))
    conditions_csv: Mapped[str] = mapped_column(String(512))
    confidence: Mapped[float] = mapped_column(Float)
    questionnaire_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    skin_type_scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    condition_scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    inference_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    report_image_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
