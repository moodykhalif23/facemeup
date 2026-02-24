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


class LoyaltyReward(BaseModel):
    id: int
    name: str
    points_required: int
    description: str
    available: bool


class LoyaltyResponse(BaseModel):
    points: int
    tier: str
    next_tier: str | None
    points_to_next_tier: int
    lifetime_points: int
    rewards: list[LoyaltyReward]
