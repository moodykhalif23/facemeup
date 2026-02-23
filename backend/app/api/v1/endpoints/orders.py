import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.order import Order
from app.models.user import User
from app.schemas.orders import CreateOrderRequest, OrderResponse


router = APIRouter()


@router.post("", response_model=OrderResponse)
def create_order(
    payload: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    order = Order(
        user_id=current_user.id,
        channel=payload.channel,
        items_json=json.dumps([item.model_dump() for item in payload.items]),
        status="created",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return OrderResponse(
        order_id=order.id,
        status=order.status,
        channel=order.channel,
        created_at=order.created_at,
    )


@router.get("", response_model=list[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    rows = db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    ).scalars()

    return [
        OrderResponse(order_id=row.id, status=row.status, channel=row.channel, created_at=row.created_at)
        for row in rows
    ]
