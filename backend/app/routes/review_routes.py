from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Review, Product, Order, OrderItem, OrderStatus, User, UserRole
from ..schemas import ReviewCreate, ReviewOut
from ..dependencies import get_current_user

router = APIRouter(tags=["Reviews"])


@router.get("/products/{product_id}/reviews", response_model=List[ReviewOut])
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    """Retrieve all approved reviews for a given product."""
    reviews = db.query(Review).filter(Review.product_id == product_id).order_by(Review.created_at.desc()).all()
    result = []
    for r in reviews:
        r_out = ReviewOut.model_validate(r)
        r_out.user_name = r.user.full_name if r.user else "Anonymous"
        r_out.product_name = r.product.name if r.product else ""
        result.append(r_out)
    return result


@router.post("/products/{product_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def submit_product_review(
    product_id: int,
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a review. Verifies that the customer has purchased this product (or is Admin for demo testing)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Check purchase verification
    if current_user.role != UserRole.ADMIN:
        has_purchased = db.query(OrderItem).join(Order).filter(
            Order.user_id == current_user.id,
            OrderItem.product_id == product_id
        ).first()

        if not has_purchased:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only verified buyers who have purchased this product can submit a review."
            )

    # Check if user already reviewed this product
    existing_review = db.query(Review).filter(
        Review.product_id == product_id,
        Review.user_id == current_user.id
    ).first()

    if existing_review:
        existing_review.rating = review_in.rating
        existing_review.title = review_in.title
        existing_review.comment = review_in.comment
        db.commit()
        db.refresh(existing_review)
        r_out = ReviewOut.model_validate(existing_review)
        r_out.user_name = current_user.full_name
        r_out.product_name = product.name
        return r_out

    review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=review_in.rating,
        title=review_in.title,
        comment=review_in.comment
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    r_out = ReviewOut.model_validate(review)
    r_out.user_name = current_user.full_name
    r_out.product_name = product.name
    return r_out


@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a review (Owner user or Admin)."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if current_user.role != UserRole.ADMIN and review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(review)
    db.commit()
    return {"message": "Review deleted successfully"}
