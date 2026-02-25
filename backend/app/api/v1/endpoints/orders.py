import json
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.order import Order
from app.models.user import User
from app.schemas.orders import CreateOrderRequest, OrderResponse, OrderDetailResponse, OrderItemDetail


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


@router.get("", response_model=dict)
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """List all orders for the current user with full details"""
    from app.models.product import ProductCatalog
    
    rows = db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    ).scalars()

    orders = []
    for row in rows:
        # Parse items from JSON
        items_data = json.loads(row.items_json) if row.items_json else []
        items = []
        total = 0.0
        
        for item_data in items_data:
            # Handle both old format (sku) and new format (product_id)
            product_name = item_data.get('product_name')
            price = item_data.get('price')
            quantity = item_data.get('quantity', 1)
            
            # If old format without product_name/price, try to fetch from database
            if not product_name or price is None:
                sku = item_data.get('sku')
                if sku:
                    product = db.execute(
                        select(ProductCatalog).where(ProductCatalog.sku == sku)
                    ).scalar_one_or_none()
                    
                    if product:
                        product_name = product.name
                        price = product.price or 0.0
            
            # Final fallback
            if not product_name:
                product_name = 'Product'
            if price is None:
                price = 0.0
            
            items.append({
                'product_name': product_name,
                'quantity': quantity,
                'price': price
            })
            total += price * quantity
        
        orders.append({
            'id': row.id,
            'order_number': f'ORD-{datetime.now().year}-{str(row.id).zfill(3)}',
            'created_at': row.created_at.isoformat(),
            'status': row.status,
            'total': total,
            'items': items
        })

    return {'orders': orders}


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrderDetailResponse:
    """Get detailed information about a specific order"""
    row = db.execute(
        select(Order)
        .where(Order.id == order_id)
        .where(Order.user_id == current_user.id)
    ).scalar_one_or_none()
    
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Parse items from JSON
    items_data = json.loads(row.items_json) if row.items_json else []
    items = []
    total = 0.0
    
    for item_data in items_data:
        product_name = item_data.get('product_name', 'Product')
        price = item_data.get('price', 29.99)
        quantity = item_data.get('quantity', 1)
        
        items.append(OrderItemDetail(
            product_name=product_name,
            quantity=quantity,
            price=price
        ))
        total += price * quantity
    
    return OrderDetailResponse(
        id=row.id,
        order_number=f'ORD-{datetime.now().year}-{str(row.id).zfill(3)}',
        created_at=row.created_at,
        status=row.status,
        total=total,
        items=items
    )
