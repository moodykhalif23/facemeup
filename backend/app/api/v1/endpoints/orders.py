from fastapi import APIRouter

from app.schemas.orders import CreateOrderRequest, OrderResponse


router = APIRouter()


@router.post("", response_model=OrderResponse)
def create_order(payload: CreateOrderRequest) -> OrderResponse:
    _ = payload
    return OrderResponse(order_id="ord_demo_001", status="created")


@router.get("/{user_id}", response_model=list[OrderResponse])
def list_orders(user_id: str) -> list[OrderResponse]:
    _ = user_id
    return [OrderResponse(order_id="ord_demo_001", status="created")]
