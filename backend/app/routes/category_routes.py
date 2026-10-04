from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Category, Product, User
from ..schemas import CategoryCreate, CategoryUpdate, CategoryOut
from ..dependencies import get_current_admin

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    """List all active categories with product counts."""
    categories = db.query(Category).all()
    result = []
    for cat in categories:
        prod_count = db.query(Product).filter(Product.category_id == cat.id).count()
        cat_out = CategoryOut.model_validate(cat)
        cat_out.product_count = prod_count
        result.append(cat_out)
    return result


@router.get("/{category_id}", response_model=CategoryOut)
def get_category_by_id(category_id: int, db: Session = Depends(get_db)):
    """Get category details by ID."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    prod_count = db.query(Product).filter(Product.category_id == cat.id).count()
    cat_out = CategoryOut.model_validate(cat)
    cat_out.product_count = prod_count
    return cat_out


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new product category (Admin only)."""
    existing = db.query(Category).filter(Category.name.ilike(category_in.name)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")
    
    category = Category(
        name=category_in.name,
        description=category_in.description,
        image=category_in.image,
        icon=category_in.icon or "fa-box",
        status=category_in.status or "ACTIVE"
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    cat_out = CategoryOut.model_validate(category)
    cat_out.product_count = 0
    return cat_out


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update existing category (Admin only)."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    update_data = category_in.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(category, key, val)
    
    db.commit()
    db.refresh(category)
    prod_count = db.query(Product).filter(Product.category_id == category.id).count()
    cat_out = CategoryOut.model_validate(category)
    cat_out.product_count = prod_count
    return cat_out


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete category if no products are assigned (Admin only)."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    prod_count = db.query(Product).filter(Product.category_id == category_id).count()
    if prod_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: {prod_count} product(s) are associated with this category. Please reassign or delete products first."
        )
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}
