from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32))
    items_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="created")
    total: Mapped[float] = mapped_column(Float, nullable=True)
    wc_order_id: Mapped[int] = mapped_column(Integer, nullable=True, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LoyaltyLedger(Base):
    __tablename__ = "loyalty_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id"), index=True)
    points: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
