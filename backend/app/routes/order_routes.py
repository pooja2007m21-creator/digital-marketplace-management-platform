import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import (
    User, Order, OrderItem, Payment, Cart, CartItem, Product, ProductStatus,
    OrderStatus, PaymentMethod, PaymentStatus, UserRole
)
from ..schemas import CheckoutRequest, OrderOut, OrderStatusUpdate
from ..dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(
    checkout_data: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Place an order from customer's shopping cart with simulated payment / COD."""
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty. Add products before placing an order."
        )

    # 1. Validate stock and compute totals
    subtotal = 0.0
    items_to_create = []

    for item in cart.items:
        product = item.product
        if not product or product.status == ProductStatus.INACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.name if product else 'Unknown'}' is unavailable."
            )
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, Requested: {item.quantity}"
            )
        
        unit_price = product.final_price
        line_total = round(unit_price * item.quantity, 2)
        subtotal += line_total
        
        items_to_create.append({
            "product": product,
            "product_id": product.id,
            "seller_id": product.seller_id,
            "product_name": product.name,
            "product_image": product.image,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "subtotal": line_total
        })

    subtotal = round(subtotal, 2)
    delivery_charge = 0.0 if (subtotal >= 1000) else 50.0
    tax = round(subtotal * 0.05, 2)
    total_amount = round(subtotal + delivery_charge + tax, 2)

    # 2. Generate unique Order ID
    order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Payment status calculation
    payment_status = PaymentStatus.SUCCESS if checkout_data.payment_method == PaymentMethod.SIMULATED_ONLINE else PaymentStatus.PENDING

    # Format delivery address
    full_address = f"{checkout_data.delivery_address}, {checkout_data.city}, {checkout_data.state} - {checkout_data.postal_code}"

    # 3. Create Order
    order = Order(
        user_id=current_user.id,
        order_number=order_number,
        subtotal=subtotal,
        discount=0.0,
        tax=tax,
        delivery_charge=delivery_charge,
        total_amount=total_amount,
        payment_method=checkout_data.payment_method,
        payment_status=payment_status,
        order_status=OrderStatus.PLACED,
        customer_name=checkout_data.customer_name,
        customer_email=checkout_data.customer_email,
        customer_phone=checkout_data.customer_phone,
        delivery_address=full_address
    )
    db.add(order)
    db.flush()

    # 4. Create Order Items & Update Inventory Stock
    for item_data in items_to_create:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            seller_id=item_data["seller_id"],
            product_name=item_data["product_name"],
            product_image=item_data["product_image"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"]
        )
        db.add(order_item)

        # Deduct stock
        prod = item_data["product"]
        prod.stock_quantity -= item_data["quantity"]
        if prod.stock_quantity <= 0:
            prod.stock_quantity = 0
            prod.status = ProductStatus.OUT_OF_STOCK

    # 5. Create Payment record
    txn_ref = f"TXN-DEMO-{uuid.uuid4().hex[:8].upper()}"
    payment = Payment(
        order_id=order.id,
        payment_method=checkout_data.payment_method,
        transaction_reference=txn_ref,
        amount=total_amount,
        status=payment_status
    )
    db.add(payment)

    # 6. Clear shopping cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()

    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(order)


@router.get("", response_model=List[OrderOut])
def get_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List orders belonging to the logged-in customer."""
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_at.desc()).all()
    return [OrderOut.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single order details by ID."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Authorization check
    if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
        # Check if user is seller of any product in this order
        is_order_seller = any(item.seller_id == getattr(current_user.seller_profile, 'id', None) for item in order.items)
        if not is_order_seller:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this order")

    return OrderOut.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel order if it is in PLACED or CONFIRMED state and restore inventory."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role != UserRole.ADMIN and order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if order.order_status not in [OrderStatus.PLACED, OrderStatus.CONFIRMED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in '{order.order_status.value}' status."
        )

    order.order_status = OrderStatus.CANCELLED
    
    # Restore stock
    for item in order.items:
        if item.product_id:
            prod = db.query(Product).filter(Product.id == item.product_id).first()
            if prod:
                prod.stock_quantity += item.quantity
                if prod.stock_quantity > 0 and prod.status == ProductStatus.OUT_OF_STOCK:
                    prod.status = ProductStatus.ACTIVE

    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(order)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update order status (Seller or Admin)."""
    if current_user.role not in [UserRole.SELLER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    order.order_status = status_update.order_status
    if status_update.order_status == OrderStatus.DELIVERED:
        if order.payment_status != PaymentStatus.SUCCESS:
            order.payment_status = PaymentStatus.SUCCESS
            if order.payment:
                order.payment.status = PaymentStatus.SUCCESS

    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(order)
