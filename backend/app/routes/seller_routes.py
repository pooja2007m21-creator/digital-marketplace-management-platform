from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import (
    SellerProfile, Product, Order, OrderItem, OrderStatus, ProductStatus, SellerApprovalStatus, UserRole
)
from ..schemas import SellerDashboardOut, ProductOut, ProductCreate, ProductUpdate, OrderOut, OrderStatusUpdate
from ..dependencies import get_current_seller, get_current_user
from .product_routes import format_product_out

router = APIRouter(prefix="/seller", tags=["Seller"])


@router.get("/dashboard", response_model=SellerDashboardOut)
def get_seller_dashboard(
    seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Retrieve seller analytics, sales stats, low-stock alerts, and recent orders."""
    # Product counts
    total_products = db.query(Product).filter(Product.seller_id == seller.id).count()
    active_products = db.query(Product).filter(
        Product.seller_id == seller.id,
        Product.status == ProductStatus.ACTIVE
    ).count()
    low_stock_products = db.query(Product).filter(
        Product.seller_id == seller.id,
        Product.stock_quantity <= 5
    ).count()

    # Seller orders
    seller_order_items = db.query(OrderItem).filter(OrderItem.seller_id == seller.id).all()
    order_ids = list(set(item.order_id for item in seller_order_items))
    
    total_orders = len(order_ids)
    
    # Calculate total revenue from seller's items
    total_sales = sum(item.subtotal for item in seller_order_items)
    
    # Pending orders count
    pending_orders = db.query(Order).filter(
        Order.id.in_(order_ids),
        Order.order_status.in_([OrderStatus.PLACED, OrderStatus.CONFIRMED, OrderStatus.PROCESSING])
    ).count() if order_ids else 0

    # Low stock items list
    low_stock_db = db.query(Product).filter(
        Product.seller_id == seller.id,
        Product.stock_quantity <= 5
    ).limit(5).all()
    low_stock_items = [format_product_out(p) for p in low_stock_db]

    # Recent orders list
    recent_orders = []
    if order_ids:
        recent_orders_db = db.query(Order).filter(
            Order.id.in_(order_ids)
        ).order_by(Order.created_at.desc()).limit(6).all()
        for ord in recent_orders_db:
            # Filter items for this seller
            seller_items = [i for i in ord.items if i.seller_id == seller.id]
            seller_order_total = sum(i.subtotal for i in seller_items)
            recent_orders.append({
                "id": ord.id,
                "order_number": ord.order_number,
                "customer_name": ord.customer_name,
                "items_count": len(seller_items),
                "seller_total": seller_order_total,
                "order_status": ord.order_status.value,
                "payment_status": ord.payment_status.value,
                "created_at": ord.created_at.strftime("%b %d, %Y %H:%M")
            })

    # Top selling products
    top_selling = []
    prod_sales: Dict[int, Dict[str, Any]] = {}
    for item in seller_order_items:
        if item.product_id:
            if item.product_id not in prod_sales:
                prod_sales[item.product_id] = {
                    "product_id": item.product_id,
                    "name": item.product_name,
                    "units_sold": 0,
                    "revenue": 0.0
                }
            prod_sales[item.product_id]["units_sold"] += item.quantity
            prod_sales[item.product_id]["revenue"] += item.subtotal

    sorted_prod_sales = sorted(prod_sales.values(), key=lambda x: x["revenue"], reverse=True)[:5]

    # Monthly sales dummy/calculated
    monthly_sales = [
        {"month": "Jan", "sales": round(total_sales * 0.1, 2)},
        {"month": "Feb", "sales": round(total_sales * 0.15, 2)},
        {"month": "Mar", "sales": round(total_sales * 0.2, 2)},
        {"month": "Apr", "sales": round(total_sales * 0.25, 2)},
        {"month": "May", "sales": round(total_sales * 0.3, 2)},
    ]

    return {
        "total_products": total_products,
        "active_products": active_products,
        "low_stock_products": low_stock_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_sales": round(total_sales, 2),
        "recent_orders": recent_orders,
        "low_stock_items": low_stock_items,
        "top_selling_products": sorted_prod_sales,
        "monthly_sales": monthly_sales
    }


@router.get("/products", response_model=List[ProductOut])
def get_seller_products(
    seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """List all products owned by current seller."""
    products = db.query(Product).filter(
        Product.seller_id == seller.id
    ).order_by(Product.created_at.desc()).all()
    return [format_product_out(p) for p in products]


@router.get("/orders")
def get_seller_orders(
    seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """List all customer orders containing products from this seller."""
    seller_items = db.query(OrderItem).filter(OrderItem.seller_id == seller.id).all()
    order_ids = list(set(i.order_id for i in seller_items))
    if not order_ids:
        return []

    orders_db = db.query(Order).filter(Order.id.in_(order_ids)).order_by(Order.created_at.desc()).all()
    result = []
    for ord in orders_db:
        items = [
            {
                "id": it.id,
                "product_id": it.product_id,
                "product_name": it.product_name,
                "product_image": it.product_image,
                "quantity": it.quantity,
                "unit_price": it.unit_price,
                "subtotal": it.subtotal
            }
            for it in ord.items if it.seller_id == seller.id
        ]
        seller_subtotal = sum(i["subtotal"] for i in items)
        result.append({
            "id": ord.id,
            "order_number": ord.order_number,
            "customer_name": ord.customer_name,
            "customer_email": ord.customer_email,
            "customer_phone": ord.customer_phone,
            "delivery_address": ord.delivery_address,
            "seller_subtotal": seller_subtotal,
            "order_status": ord.order_status.value,
            "payment_method": ord.payment_method.value,
            "payment_status": ord.payment_status.value,
            "created_at": ord.created_at.strftime("%Y-%m-%d %H:%M"),
            "items": items
        })
    return result


@router.put("/inventory/{product_id}")
def update_product_inventory(
    product_id: int,
    data: Dict[str, Any],
    seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Quick update for stock quantity and price in seller inventory table."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.seller_id == seller.id
    ).first()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or unauthorized")

    if "stock_quantity" in data:
        new_stock = int(data["stock_quantity"])
        product.stock_quantity = max(0, new_stock)
        if product.stock_quantity <= 0:
            product.status = ProductStatus.OUT_OF_STOCK
        elif product.status == ProductStatus.OUT_OF_STOCK and product.stock_quantity > 0:
            product.status = ProductStatus.ACTIVE

    if "price" in data:
        product.price = float(data["price"])

    if "status" in data:
        try:
            product.status = ProductStatus(data["status"])
        except ValueError:
            pass

    db.commit()
    db.refresh(product)
    return format_product_out(product)
