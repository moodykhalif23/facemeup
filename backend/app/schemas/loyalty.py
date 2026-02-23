from pydantic import BaseModel


class LoyaltyTransaction(BaseModel):
    points: int
    reason: str


class LoyaltyBalance(BaseModel):
    user_id: str
    balance: int
    transactions: list[LoyaltyTransaction]
