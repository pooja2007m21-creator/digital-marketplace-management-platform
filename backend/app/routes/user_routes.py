from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import User, Order, OrderStatus, Wishlist, Cart, Product, ProductStatus
from ..schemas import UserOut, UserUpdate, CustomerDashboardOut, OrderOut, ProductOut
from ..dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get profile of current authenticated user."""
    return current_user


@router.put("/me", response_model=UserOut)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile information for current user."""
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me")
def delete_current_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account."""
    db.delete(current_user)
    db.commit()
    return {"message": "Account successfully deleted"}


@router.get("/dashboard", response_model=CustomerDashboardOut)
def get_customer_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get customer dashboard data, summary counts, recent orders, and recommendations."""
    # Total orders
    total_orders = db.query(Order).filter(Order.user_id == current_user.id).count()
    
    # Pending orders
    pending_orders = db.query(Order).filter(
        Order.user_id == current_user.id,
        Order.order_status.in_([OrderStatus.PLACED, OrderStatus.CONFIRMED, OrderStatus.PROCESSING, OrderStatus.SHIPPED, OrderStatus.OUT_FOR_DELIVERY])
    ).count()

    # Wishlist count
    wishlist = db.query(Wishlist).filter(Wishlist.user_id == current_user.id).first()
    wishlist_count = len(wishlist.items) if wishlist else 0

    # Cart count
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    cart_count = sum(item.quantity for item in cart.items) if cart else 0

    # Recent orders (latest 5)
    recent_orders_db = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).limit(5).all()
    
    recent_orders = []
    for order in recent_orders_db:
        recent_orders.append(OrderOut.model_validate(order))

    # Recommended products (top active products)
    recom_db = db.query(Product).filter(
        Product.status == ProductStatus.ACTIVE
    ).order_by(func.random()).limit(4).all()

    recommended_products = []
    for p in recom_db:
        p_out = ProductOut.model_validate(p)
        p_out.category_name = p.category.name if p.category else None
        p_out.seller_name = p.seller.business_name if p.seller else None
        if p.reviews:
            p_out.rating_avg = round(sum(r.rating for r in p.reviews) / len(p.reviews), 1)
            p_out.review_count = len(p.reviews)
        recommended_products.append(p_out)

    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,
        "recent_orders": recent_orders,
        "recommended_products": recommended_products
    }
