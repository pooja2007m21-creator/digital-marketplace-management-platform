from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Wishlist, WishlistItem, Product, Cart, CartItem
from ..schemas import WishlistOut, WishlistItemOut, WishlistAdd
from ..dependencies import get_current_user
from .product_routes import format_product_out
from .cart_routes import get_or_create_user_cart

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


def get_or_create_user_wishlist(user_id: int, db: Session) -> Wishlist:
    wishlist = db.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=user_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)
    return wishlist


def build_wishlist_response(wishlist: Wishlist) -> WishlistOut:
    items_out = []
    for item in wishlist.items:
        if item.product:
            items_out.append(WishlistItemOut(
                id=item.id,
                wishlist_id=item.wishlist_id,
                product_id=item.product_id,
                product=format_product_out(item.product)
            ))
    return WishlistOut(
        id=wishlist.id,
        user_id=wishlist.user_id,
        items=items_out,
        item_count=len(items_out)
    )


@router.get("", response_model=WishlistOut)
def get_wishlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's wishlist."""
    wishlist = get_or_create_user_wishlist(current_user.id, db)
    return build_wishlist_response(wishlist)


@router.post("", response_model=WishlistOut)
def add_to_wishlist(
    item_in: WishlistAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a product to wishlist."""
    product = db.query(Product).filter(Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    wishlist = get_or_create_user_wishlist(current_user.id, db)
    existing = db.query(WishlistItem).filter(
        WishlistItem.wishlist_id == wishlist.id,
        WishlistItem.product_id == item_in.product_id
    ).first()

    if not existing:
        item = WishlistItem(wishlist_id=wishlist.id, product_id=item_in.product_id)
        db.add(item)
        db.commit()
        db.refresh(wishlist)

    return build_wishlist_response(wishlist)


@router.delete("/{product_id}", response_model=WishlistOut)
def remove_from_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a product from wishlist by product_id or wishlist_item_id."""
    wishlist = get_or_create_user_wishlist(current_user.id, db)
    item = db.query(WishlistItem).filter(
        WishlistItem.wishlist_id == wishlist.id,
        (WishlistItem.product_id == product_id) | (WishlistItem.id == product_id)
    ).first()

    if item:
        db.delete(item)
        db.commit()
        db.refresh(wishlist)

    return build_wishlist_response(wishlist)


@router.post("/{product_id}/move-to-cart")
def move_to_cart(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move product from wishlist to shopping cart."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Add to cart
    cart = get_or_create_user_cart(current_user.id, db)
    cart_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product_id
    ).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=1)
        db.add(cart_item)

    # Remove from wishlist
    wishlist = get_or_create_user_wishlist(current_user.id, db)
    wishlist_item = db.query(WishlistItem).filter(
        WishlistItem.wishlist_id == wishlist.id,
        WishlistItem.product_id == product_id
    ).first()
    if wishlist_item:
        db.delete(wishlist_item)

    db.commit()
    return {"message": "Product successfully moved to cart"}
