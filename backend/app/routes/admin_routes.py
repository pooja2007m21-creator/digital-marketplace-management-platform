from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import (
    User, UserRole, UserStatus, SellerProfile, SellerApprovalStatus,
    Product, ProductStatus, Category, Order, OrderItem, OrderStatus,
    Payment, PaymentStatus, Review
)
from ..schemas import (
    UserOut, UserStatusUpdate, SellerProfileOut, SellerStatusUpdate,
    ProductOut, OrderOut, OrderStatusUpdate, ReviewOut, AdminDashboardOut
)
from ..dependencies import get_current_admin
from .product_routes import format_product_out

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardOut)
def get_admin_dashboard(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Admin summary statistics and analytics."""
    total_customers = db.query(User).filter(User.role == UserRole.CUSTOMER).count()
    total_sellers = db.query(SellerProfile).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    
    # Revenue
    revenue_res = db.query(func.sum(Order.total_amount)).filter(
        Order.order_status != OrderStatus.CANCELLED
    ).scalar()
    total_revenue = round(float(revenue_res or 0.0), 2)

    pending_seller_approvals = db.query(SellerProfile).filter(
        SellerProfile.approval_status == SellerApprovalStatus.PENDING
    ).count()

    # Recent orders
    recent_orders_db = db.query(Order).order_by(Order.created_at.desc()).limit(6).all()
    recent_orders = [OrderOut.model_validate(o) for o in recent_orders_db]

    # Recent users
    recent_users_db = db.query(User).order_by(User.created_at.desc()).limit(6).all()
    recent_users = [UserOut.model_validate(u) for u in recent_users_db]

    # Category product counts
    cat_counts = []
    categories = db.query(Category).all()
    for cat in categories:
        count = db.query(Product).filter(Product.category_id == cat.id).count()
        cat_counts.append({"category": cat.name, "count": count})

    # Order status breakdown
    order_status_counts = {}
    for st in OrderStatus:
        st_count = db.query(Order).filter(Order.order_status == st).count()
        order_status_counts[st.value] = st_count

    # Sales overview dummy/aggregated
    sales_overview = [
        {"period": "Week 1", "sales": round(total_revenue * 0.2, 2), "orders": max(1, int(total_orders * 0.2))},
        {"period": "Week 2", "sales": round(total_revenue * 0.25, 2), "orders": max(1, int(total_orders * 0.25))},
        {"period": "Week 3", "sales": round(total_revenue * 0.25, 2), "orders": max(1, int(total_orders * 0.25))},
        {"period": "Week 4", "sales": round(total_revenue * 0.3, 2), "orders": max(1, int(total_orders * 0.3))},
    ]

    return {
        "total_customers": total_customers,
        "total_sellers": total_sellers,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_seller_approvals": pending_seller_approvals,
        "recent_orders": recent_orders,
        "recent_users": recent_users,
        "category_product_counts": cat_counts,
        "order_status_counts": order_status_counts,
        "sales_overview": sales_overview
    }


# ==========================================
# USER MANAGEMENT
# ==========================================

@router.get("/users", response_model=List[UserOut])
def list_users(
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin list users with search and filter."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((User.full_name.ilike(s)) | (User.email.ilike(s)) | (User.username.ilike(s)))
    
    users = query.order_by(User.created_at.desc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.patch("/users/{user_id}/status", response_model=UserOut)
def update_user_status(
    user_id: int,
    status_in: UserStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin activate, deactivate, or suspend a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change your own administrator status")

    user.status = status_in.status
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin delete a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own administrator account")

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


# ==========================================
# SELLER MANAGEMENT
# ==========================================

@router.get("/sellers", response_model=List[SellerProfileOut])
def list_sellers(
    approval_status: Optional[SellerApprovalStatus] = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin list sellers and pending applications."""
    query = db.query(SellerProfile)
    if approval_status:
        query = query.filter(SellerProfile.approval_status == approval_status)
    sellers = query.order_by(SellerProfile.created_at.desc()).all()
    return [SellerProfileOut.model_validate(s) for s in sellers]


@router.patch("/sellers/{seller_id}/status", response_model=SellerProfileOut)
def update_seller_approval_status(
    seller_id: int,
    status_in: SellerStatusUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin approve, reject, or suspend a seller profile."""
    seller = db.query(SellerProfile).filter(SellerProfile.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seller profile not found")

    seller.approval_status = status_in.approval_status
    db.commit()
    db.refresh(seller)
    return SellerProfileOut.model_validate(seller)


# ==========================================
# PRODUCT MANAGEMENT (ADMIN)
# ==========================================

@router.get("/products", response_model=List[ProductOut])
def list_admin_products(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin view all products across the marketplace."""
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return [format_product_out(p) for p in products]


@router.patch("/products/{product_id}/status", response_model=ProductOut)
def update_product_status_admin(
    product_id: int,
    data: Dict[str, str],
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin activate or deactivate a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    status_str = data.get("status", "ACTIVE")
    product.status = ProductStatus(status_str)
    db.commit()
    db.refresh(product)
    return format_product_out(product)


# ==========================================
# ORDER MANAGEMENT (ADMIN)
# ==========================================

@router.get("/orders", response_model=List[OrderOut])
def list_admin_orders(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin view all marketplace orders."""
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return [OrderOut.model_validate(o) for o in orders]


# ==========================================
# REVIEW MANAGEMENT (ADMIN)
# ==========================================

@router.get("/reviews", response_model=List[ReviewOut])
def list_admin_reviews(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin view and moderate all customer reviews."""
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    result = []
    for r in reviews:
        r_out = ReviewOut.model_validate(r)
        r_out.user_name = r.user.full_name if r.user else "Anonymous"
        r_out.product_name = r.product.name if r.product else ""
        result.append(r_out)
    return result


# ==========================================
# REPORTS & ANALYTICS
# ==========================================

@router.get("/reports")
def get_admin_reports(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed marketplace reports and metrics for export/presentation."""
    total_sales = db.query(func.sum(Order.total_amount)).filter(Order.order_status != OrderStatus.CANCELLED).scalar() or 0.0
    total_orders = db.query(Order).count()
    total_customers = db.query(User).filter(User.role == UserRole.CUSTOMER).count()
    total_sellers = db.query(SellerProfile).count()
    total_products = db.query(Product).count()

    # Top selling products
    order_items = db.query(OrderItem).all()
    prod_sales = {}
    for it in order_items:
        if it.product_id:
            if it.product_id not in prod_sales:
                prod_sales[it.product_id] = {"name": it.product_name, "units": 0, "revenue": 0.0}
            prod_sales[it.product_id]["units"] += it.quantity
            prod_sales[it.product_id]["revenue"] += it.subtotal

    top_products = sorted(prod_sales.values(), key=lambda x: x["revenue"], reverse=True)[:5]

    # Category share
    cat_distribution = []
    for cat in db.query(Category).all():
        p_count = db.query(Product).filter(Product.category_id == cat.id).count()
        cat_distribution.append({"category": cat.name, "count": p_count})

    return {
        "summary": {
            "total_sales": round(float(total_sales), 2),
            "total_orders": total_orders,
            "total_customers": total_customers,
            "total_sellers": total_sellers,
            "total_products": total_products
        },
        "top_selling_products": top_products,
        "category_distribution": cat_distribution
    }
