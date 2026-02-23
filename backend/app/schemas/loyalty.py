from datetime import datetime

from pydantic import BaseModel


class LoyaltyTransaction(BaseModel):
    id: int
    points: int
    reason: str
    created_at: datetime


class LoyaltyBalance(BaseModel):
    user_id: str
    balance: int
    transactions: list[LoyaltyTransaction]
