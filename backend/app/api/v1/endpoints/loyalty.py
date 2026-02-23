from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.order import LoyaltyLedger
from app.models.user import User
from app.schemas.loyalty import LoyaltyBalance, LoyaltyTransaction


router = APIRouter()


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
    points: int = Query(default=0, ge=-1000, le=1000),
    reason: str = Query(default="Manual adjustment"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LoyaltyBalance:
    db.add(LoyaltyLedger(user_id=current_user.id, points=points, reason=reason))
    db.commit()
    return get_balance(db, current_user)
