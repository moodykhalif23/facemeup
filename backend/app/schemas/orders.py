from datetime import datetime

from pydantic import BaseModel


class OrderItem(BaseModel):
    sku: str
    quantity: int


class CreateOrderRequest(BaseModel):
    channel: str
    items: list[OrderItem]


class OrderResponse(BaseModel):
    order_id: int
    status: str
    channel: str
    created_at: datetime
