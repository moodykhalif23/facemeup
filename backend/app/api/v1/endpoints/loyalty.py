from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.order import LoyaltyLedger
from app.models.user import User
from app.schemas.loyalty import LoyaltyBalance, LoyaltyTransaction, LoyaltyReward, LoyaltyResponse


router = APIRouter()


@router.get("/{user_id}", response_model=LoyaltyResponse)
def get_loyalty_by_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LoyaltyResponse:
    """Get loyalty data for a specific user (must be current user or admin)"""
    # Only allow users to view their own loyalty data
    if current_user.id != user_id:
        # Could add admin check here if needed
        user_id = current_user.id
    
    rows = db.execute(
        select(LoyaltyLedger)
        .where(LoyaltyLedger.user_id == user_id)
        .order_by(LoyaltyLedger.created_at.desc())
    ).scalars()
    
    transactions = [
        LoyaltyTransaction(id=row.id, points=row.points, reason=row.reason, created_at=row.created_at)
        for row in rows
    ]
    balance = sum(t.points for t in transactions)
    
    # Calculate tier based on lifetime points
    lifetime_points = balance
    tier = "Bronze"
    next_tier = "Silver"
    points_to_next = 500
    
    if lifetime_points >= 2000:
        tier = "Platinum"
        next_tier = None
        points_to_next = 0
    elif lifetime_points >= 1000:
        tier = "Gold"
        next_tier = "Platinum"
        points_to_next = 2000 - lifetime_points
    elif lifetime_points >= 500:
        tier = "Silver"
        next_tier = "Gold"
        points_to_next = 1000 - lifetime_points
    else:
        points_to_next = 500 - lifetime_points
    
    # Define available rewards
    rewards = [
        LoyaltyReward(
            id=1,
            name="10% Off Next Purchase",
            points_required=500,
            description="Get 10% discount on your next order",
            available=balance >= 500
        ),
        LoyaltyReward(
            id=2,
            name="Free Shipping",
            points_required=300,
            description="Free shipping on your next order",
            available=balance >= 300
        ),
        LoyaltyReward(
            id=3,
            name="Free Sample Product",
            points_required=750,
            description="Get a free sample of any product",
            available=balance >= 750
        ),
        LoyaltyReward(
            id=4,
            name="20% Off Next Purchase",
            points_required=1000,
            description="Get 20% discount on your next order",
            available=balance >= 1000
        ),
        LoyaltyReward(
            id=5,
            name="Premium Gift Set",
            points_required=1500,
            description="Exclusive premium skincare gift set",
            available=balance >= 1500
        ),
    ]
    
    return LoyaltyResponse(
        points=balance,
        tier=tier,
        next_tier=next_tier,
        points_to_next_tier=points_to_next,
        lifetime_points=lifetime_points,
        rewards=rewards
    )


@router.get("", response_model=LoyaltyBalance)
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LoyaltyBalance:
    rows = db.execute(
        select(LoyaltyLedger)
        .where(LoyaltyLedger.user_id == current_user.id)
        .order_by(LoyaltyLedger.created_at.desc())
    ).scalars()
    transactions = [
        LoyaltyTransaction(id=row.id, points=row.points, reason=row.reason, created_at=row.created_at)
        for row in rows
    ]
    balance = sum(t.points for t in transactions)
    return LoyaltyBalance(user_id=current_user.id, balance=balance, transactions=transactions)


@router.post("/earn", response_model=LoyaltyBalance)
def earn_points(
    user_id: str = Query(...),
    points: int = Query(default=0, ge=-1000, le=1000),
    reason: str = Query(default="Manual adjustment"),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin", "advisor")),
) -> LoyaltyBalance:
    db.add(LoyaltyLedger(user_id=user_id, points=points, reason=reason))
    db.commit()

    rows = db.execute(
        select(LoyaltyLedger)
        .where(LoyaltyLedger.user_id == user_id)
        .order_by(LoyaltyLedger.created_at.desc())
    ).scalars()
    transactions = [
        LoyaltyTransaction(id=row.id, points=row.points, reason=row.reason, created_at=row.created_at)
        for row in rows
    ]
    balance = sum(t.points for t in transactions)
    return LoyaltyBalance(user_id=user_id, balance=balance, transactions=transactions)
