from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Cart, CartItem, Product, ProductStatus
from ..schemas import CartOut, CartItemCreate, CartItemUpdate, CartItemOut, ProductOut
from ..dependencies import get_current_user
from .product_routes import format_product_out

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


def get_or_create_user_cart(user_id: int, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def build_cart_response(cart: Cart) -> CartOut:
    items_out = []
    subtotal = 0.0
    item_count = 0

    for item in cart.items:
        if item.product:
            p_out = format_product_out(item.product)
            item_subtotal = round(p_out.final_price * item.quantity, 2)
            subtotal += item_subtotal
            item_count += item.quantity
            
            items_out.append(CartItemOut(
                id=item.id,
                cart_id=item.cart_id,
                product_id=item.product_id,
                quantity=item.quantity,
                product=p_out,
                subtotal=item_subtotal
            ))

    subtotal = round(subtotal, 2)
    # Calculate delivery and tax logic
    # E.g. If subtotal > 1000, free delivery, else ₹50. Tax ~ 5%
    delivery_charge = 0.0 if (subtotal >= 1000 or subtotal == 0) else 50.0
    tax = round(subtotal * 0.05, 2)
    grand_total = round(subtotal + delivery_charge + tax, 2)

    return CartOut(
        id=cart.id,
        user_id=cart.user_id,
        items=items_out,
        item_count=item_count,
        subtotal=subtotal,
        discount=0.0,
        delivery_charge=delivery_charge,
        tax=tax,
        grand_total=grand_total
    )


@router.get("", response_model=CartOut)
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve current user's shopping cart."""
    cart = get_or_create_user_cart(current_user.id, db)
    return build_cart_response(cart)


@router.post("", response_model=CartOut)
def add_to_cart(
    item_in: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a product or increment quantity in the shopping cart."""
    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if product.status == ProductStatus.OUT_OF_STOCK or product.stock_quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product is currently out of stock")

    cart = get_or_create_user_cart(current_user.id, db)
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == item_in.product_id
    ).first()

    if existing_item:
        new_quantity = existing_item.quantity + item_in.quantity
        if new_quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock_quantity} items available in stock"
            )
        existing_item.quantity = new_quantity
    else:
        if item_in.quantity > product.stock_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {product.stock_quantity} items available in stock"
            )
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(cart_item)

    db.commit()
    db.refresh(cart)
    return build_cart_response(cart)


@router.put("/{item_id}", response_model=CartOut)
def update_cart_item(
    item_id: int,
    item_update: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update quantity of a cart item."""
    cart = get_or_create_user_cart(current_user.id, db)
    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    if item_update.quantity > item.product.stock_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {item.product.stock_quantity} items available in stock"
        )

    item.quantity = item_update.quantity
    db.commit()
    db.refresh(cart)
    return build_cart_response(cart)


@router.delete("/{item_id}", response_model=CartOut)
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a specific item from the cart."""
    cart = get_or_create_user_cart(current_user.id, db)
    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()

    if item:
        db.delete(item)
        db.commit()
        db.refresh(cart)

    return build_cart_response(cart)


@router.delete("", response_model=CartOut)
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all items in the user's shopping cart."""
    cart = get_or_create_user_cart(current_user.id, db)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    db.refresh(cart)
    return build_cart_response(cart)
