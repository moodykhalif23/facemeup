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


class OrderItemDetail(BaseModel):
    product_name: str
    quantity: int
    price: float


class OrderDetailResponse(BaseModel):
    id: int
    order_number: str
    created_at: datetime
    status: str
    total: float
    items: list[OrderItemDetail]
