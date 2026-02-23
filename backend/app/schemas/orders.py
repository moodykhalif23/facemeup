from pydantic import BaseModel


class OrderItem(BaseModel):
    sku: str
    quantity: int


class CreateOrderRequest(BaseModel):
    user_id: str
    channel: str
    items: list[OrderItem]


class OrderResponse(BaseModel):
    order_id: str
    status: str
