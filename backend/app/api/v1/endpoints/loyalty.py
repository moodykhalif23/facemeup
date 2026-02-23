from fastapi import APIRouter

from app.schemas.loyalty import LoyaltyBalance, LoyaltyTransaction


router = APIRouter()


@router.get("/{user_id}", response_model=LoyaltyBalance)
def get_balance(user_id: str) -> LoyaltyBalance:
    return LoyaltyBalance(
        user_id=user_id,
        balance=120,
        transactions=[LoyaltyTransaction(points=120, reason="Welcome bonus")],
    )


@router.post("/{user_id}/earn", response_model=LoyaltyBalance)
def earn_points(user_id: str, points: int = 0) -> LoyaltyBalance:
    return LoyaltyBalance(
        user_id=user_id,
        balance=max(0, 120 + points),
        transactions=[LoyaltyTransaction(points=points, reason="Manual adjustment")],
    )
