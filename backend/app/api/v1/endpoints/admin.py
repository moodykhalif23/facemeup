import json
from datetime import datetime, timezone, UTC

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.errors import AppError
from app.core.redis_client import get_redis_client
from app.models.order import LoyaltyLedger, Order
from app.models.product import ProductCatalog
from app.models.profile import SkinProfileHistory
from app.models.user import User, RefreshToken
from app.services.profile_service import get_profile_history
from app.services.training_scheduler import process_user_captured_images
from app.services.training_manifest import refresh_training_manifest

router = APIRouter()

# Dashboard stats

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> dict:
    """Aggregate numbers for the admin dashboard."""
    total_users = db.execute(select(func.count()).select_from(User).where(User.deleted_at.is_(None))).scalar_one()
    total_orders = db.execute(select(func.count()).select_from(Order)).scalar_one()
    total_products = db.execute(select(func.count()).select_from(ProductCatalog)).scalar_one()
    total_analyses = db.execute(select(func.count()).select_from(SkinProfileHistory).where(SkinProfileHistory.deleted_at.is_(None))).scalar_one()

    # Revenue = sum of all order items
    orders = db.execute(select(Order)).scalars().all()
    total_revenue = 0.0
    for order in orders:
        try:
            items = json.loads(order.items_json or "[]")
            for item in items:
                total_revenue += float(item.get("price", 0)) * int(item.get("quantity", 1))
        except Exception:
            pass

    # Skin-type distribution from latest profile per user
    skin_dist_rows = db.execute(
        select(SkinProfileHistory.skin_type, func.count().label("cnt"))
        .where(SkinProfileHistory.deleted_at.is_(None))
        .group_by(SkinProfileHistory.skin_type)
    ).all()
    skin_distribution = {row.skin_type: row.cnt for row in skin_dist_rows}

    # Recent 5 orders
    recent_orders = db.execute(
        select(Order).order_by(Order.created_at.desc()).limit(5)
    ).scalars().all()
    recent_order_list = [
        {
            "id": o.id,
            "user_id": o.user_id,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        }
        for o in recent_orders
    ]

    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "total_products": total_products,
        "total_analyses": total_analyses,
        "total_revenue": round(total_revenue, 2),
        "skin_distribution": skin_distribution,
        "recent_orders": recent_order_list,
    }

# User management


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """Return users with pagination (skip/limit)."""
    total = db.execute(select(func.count()).select_from(User).where(User.deleted_at.is_(None))).scalar_one()
    rows = db.execute(
        select(User).where(User.deleted_at.is_(None))
        .order_by(User.created_at.desc()).offset(skip).limit(limit)
    ).scalars().all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "created_at": u.created_at.isoformat(),
            }
            for u in rows
        ],
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> dict:
    """Change a user's role. Payload: { role: 'customer' | 'advisor' | 'admin' }"""
    new_role = payload.get("role", "").strip()
    if new_role not in ("customer", "advisor", "admin"):
        raise AppError(400, "invalid_role", "Role must be customer, advisor, or admin")

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise AppError(404, "not_found", "User not found")
    if user.id == current_user.id:
        raise AppError(400, "self_role_change", "Cannot change your own role")

    user.role = new_role
    db.commit()
    return {"id": user.id, "role": user.role}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin")),
) -> dict:
    """Soft-delete a user — sets deleted_at, preserving all associated data."""
    if user_id == current_user.id:
        raise AppError(400, "self_delete", "Cannot delete your own account")

    user = db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    ).scalar_one_or_none()
    if not user:
        raise AppError(404, "not_found", "User not found")

    # Revoke all active refresh tokens
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))

    user.deleted_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    return {"deleted": user_id, "soft": True}


# Reports

@router.get("/reports")
def list_reports(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    total = db.execute(
        select(func.count()).select_from(SkinProfileHistory)
        .where(SkinProfileHistory.deleted_at.is_(None))
    ).scalar_one()
    rows = db.execute(
        select(SkinProfileHistory, User)
        .join(User, User.id == SkinProfileHistory.user_id)
        .where(SkinProfileHistory.deleted_at.is_(None))
        .order_by(SkinProfileHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    reports = []
    for record, user in rows:
        reports.append({
            "id": record.id,
            "user_id": record.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "skin_type": record.skin_type,
            "conditions": [v for v in record.conditions_csv.split(",") if v],
            "confidence": record.confidence,
            "created_at": record.created_at.isoformat(),
            "questionnaire": json.loads(record.questionnaire_json) if record.questionnaire_json else None,
            "skin_type_scores": json.loads(record.skin_type_scores_json) if record.skin_type_scores_json else None,
            "condition_scores": json.loads(record.condition_scores_json) if record.condition_scores_json else None,
            "inference_mode": record.inference_mode,
            "report_image_base64": record.report_image_base64,
            "capture_images": json.loads(record.capture_images_json) if record.capture_images_json else None,
        })

    return {"total": total, "skip": skip, "limit": limit, "reports": reports}


@router.delete("/reports/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> dict:
    """Soft-delete a single skin analysis report."""
    record = db.get(SkinProfileHistory, report_id)
    if not record or record.deleted_at is not None:
        raise AppError(404, "not_found", "Report not found")
    record.deleted_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    return {"deleted": report_id, "soft": True}


@router.get("/reports/{user_id}")
def get_user_reports(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> dict:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        raise AppError(404, "not_found", "User not found")

    history = get_profile_history(db, user_id)
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        },
        "history": history,
    }

# Order management


@router.get("/orders")
def list_all_orders(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """Return orders with pagination (skip/limit)."""
    total = db.execute(select(func.count()).select_from(Order)).scalar_one()
    rows = db.execute(
        select(Order, User.email)
        .join(User, User.id == Order.user_id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    orders = []
    for order, email in rows:
        try:
            items = json.loads(order.items_json or "[]")
        except Exception:
            items = []
        total = sum(
            float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in items
        )
        orders.append({
            "id": order.id,
            "order_number": f"ORD-{order.created_at.year}-{str(order.id).zfill(3)}",
            "user_email": email,
            "user_id": order.user_id,
            "channel": order.channel,
            "status": order.status,
            "total": order.total if order.total is not None else round(total, 2),
            "items_count": len(items),
            "items": items,
            "wc_order_id": order.wc_order_id,
            "created_at": order.created_at.isoformat(),
        })

    return {"total": total, "skip": skip, "limit": limit, "orders": orders}


@router.put("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin")),
) -> dict:
    """Update an order's status. Payload: { status: 'created' | 'paid' | 'shipped' | 'delivered' | 'cancelled' }"""
    valid = {"created", "paid", "shipped", "delivered", "cancelled"}
    new_status = payload.get("status", "").strip()
    if new_status not in valid:
        raise AppError(400, "invalid_status", f"Status must be one of: {', '.join(sorted(valid))}")


    order = db.execute(select(Order).where(Order.id == order_id)).scalar_one_or_none()
    if not order:
        raise AppError(404, "not_found", "Order not found")

    order.status = new_status
    db.commit()
    return {"id": order.id, "status": order.status}

# ──────────────────────────────────────────────────────────────────────────────
# Training data sync + manifest refresh
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/training/sync")
def sync_training_assets(
    _: User = Depends(require_roles("admin")),
) -> dict:
    """
    Move user-captured images into training data and refresh the manifest CSV.
    """
    try:
        sync_result = process_user_captured_images()
        manifest = refresh_training_manifest()
        return {
            "sync": sync_result,
            "manifest": manifest,
        }
    except Exception as exc:
        raise AppError(500, "training_sync_failed", f"Training sync failed: {exc}")

@router.get("/model/status")
def model_status(
    _: User = Depends(require_roles("admin")),
) -> dict:
    """Check Ollama connectivity and which models are in use."""
    import httpx
    from app.core.config import settings
    try:
        r = httpx.get(f"{settings.ollama_url.rstrip('/')}/api/tags", timeout=5.0)
        available = [m["name"] for m in r.json().get("models", [])]
        return {
            "ollama": "ok",
            "vision_model": settings.ollama_vision_model,
            "text_model": settings.ollama_text_model,
            "available_models": available,
        }
    except Exception as exc:
        return {"ollama": "unreachable", "error": str(exc)}


# Cache management

@router.post("/cache/clear")
def clear_cache(
    _: User = Depends(require_roles("admin")),
) -> dict:
    """Flush all cached keys (products, recommendations)."""
    try:
        redis = get_redis_client()
        keys = redis.keys("products:*") + redis.keys("recommend:*")
        if keys:
            redis.delete(*keys)
        return {"cleared": len(keys), "keys": [k.decode() if isinstance(k, bytes) else k for k in keys]}
    except Exception as exc:
        raise AppError(500, "cache_error", str(exc))
