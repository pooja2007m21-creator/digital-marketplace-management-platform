import os
import uuid
import shutil
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func
from ..database import get_db
from ..models import Product, ProductStatus, Category, SellerProfile, Review, User, UserRole, SellerApprovalStatus
from ..schemas import ProductCreate, ProductUpdate, ProductOut, ProductListResponse
from ..dependencies import get_current_user, get_current_seller

router = APIRouter(prefix="/products", tags=["Products"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads", "products")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".svg", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024 # 5MB


def format_product_out(p: Product) -> ProductOut:
    p_out = ProductOut.model_validate(p)
    p_out.category_name = p.category.name if p.category else "Uncategorized"
    p_out.seller_name = p.seller.business_name if p.seller else "Marketplace"
    if p.reviews:
        p_out.rating_avg = round(sum(r.rating for r in p.reviews) / len(p.reviews), 1)
        p_out.review_count = len(p.reviews)
    else:
        p_out.rating_avg = 0.0
        p_out.review_count = 0
    return p_out


@router.get("", response_model=ProductListResponse)
def list_products(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search query across name, description, brand, seller"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    seller_id: Optional[int] = Query(None, description="Filter by seller profile ID"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    min_rating: Optional[float] = Query(None, description="Minimum average rating (1-5)"),
    availability: Optional[str] = Query(None, description="in_stock or out_of_stock"),
    has_discount: Optional[bool] = Query(None, description="Only discounted items"),
    sort_by: Optional[str] = Query("newest", description="price_asc, price_desc, rating, newest, popularity, discount"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100)
):
    """Retrieve products with advanced search, filtering, sorting, and pagination."""
    query = db.query(Product).join(Product.seller).filter(
        Product.status != ProductStatus.INACTIVE,
        SellerProfile.approval_status == SellerApprovalStatus.APPROVED
    )

    # Search filter
    if search:
        search_clean = f"%{search.strip()}%"
        query = query.join(Product.category).filter(
            or_(
                Product.name.ilike(search_clean),
                Product.description.ilike(search_clean),
                Product.brand.ilike(search_clean),
                SellerProfile.business_name.ilike(search_clean),
                Category.name.ilike(search_clean)
            )
        )

    # Category filter
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Seller filter
    if seller_id:
        query = query.filter(Product.seller_id == seller_id)

    # Price range filter
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Availability filter
    if availability == "in_stock":
        query = query.filter(Product.stock_quantity > 0, Product.status == ProductStatus.ACTIVE)
    elif availability == "out_of_stock":
        query = query.filter(or_(Product.stock_quantity <= 0, Product.status == ProductStatus.OUT_OF_STOCK))

    # Discount filter
    if has_discount:
        query = query.filter(Product.discount > 0)

    # Execute and calculate ratings if needed
    all_filtered = query.all()
    
    # Filter by rating in memory or query
    if min_rating and min_rating > 0:
        filtered_by_rating = []
        for p in all_filtered:
            avg_r = (sum(r.rating for r in p.reviews) / len(p.reviews)) if p.reviews else 0.0
            if avg_r >= min_rating:
                filtered_by_rating.append(p)
        all_filtered = filtered_by_rating

    # Sorting
    if sort_by == "price_asc":
        all_filtered.sort(key=lambda x: x.final_price)
    elif sort_by == "price_desc":
        all_filtered.sort(key=lambda x: x.final_price, reverse=True)
    elif sort_by == "rating":
        all_filtered.sort(
            key=lambda x: (sum(r.rating for r in x.reviews) / len(x.reviews)) if x.reviews else 0.0,
            reverse=True
        )
    elif sort_by == "popularity":
        all_filtered.sort(key=lambda x: len(x.order_items), reverse=True)
    elif sort_by == "discount":
        all_filtered.sort(key=lambda x: x.discount or 0.0, reverse=True)
    else:  # newest
        all_filtered.sort(key=lambda x: x.created_at, reverse=True)

    # Pagination
    total = len(all_filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = all_filtered[start_idx:end_idx]

    return {
        "items": [format_product_out(p) for p in paged_items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": total_pages
    }


@router.get("/{product_id}", response_model=ProductOut)
def get_product_details(product_id: int, db: Session = Depends(get_db)):
    """Get single product details with seller info, category info, and ratings."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return format_product_out(product)


@router.post("/upload-image")
def upload_product_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload product image safely and return image URL."""
    if current_user.role not in [UserRole.SELLER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only sellers and admins can upload product images")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type {ext}. Safe extensions allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_filename = f"prod_{uuid.uuid4().hex[:12]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": unique_filename,
        "image_url": f"/uploads/products/{unique_filename}",
        "message": "Image uploaded successfully"
    }


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Create a new product (Seller or Admin)."""
    # Verify category exists
    category = db.query(Category).filter(Category.id == product_in.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Category ID")

    # Generate or verify SKU
    sku = product_in.sku or f"SKU-{uuid.uuid4().hex[:8].upper()}"
    existing_sku = db.query(Product).filter(Product.sku == sku).first()
    if existing_sku:
        sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"

    initial_status = ProductStatus.OUT_OF_STOCK if product_in.stock_quantity <= 0 else (product_in.status or ProductStatus.ACTIVE)

    product = Product(
        seller_id=current_seller.id,
        category_id=product_in.category_id,
        name=product_in.name,
        description=product_in.description,
        sku=sku,
        brand=product_in.brand,
        price=product_in.price,
        discount=product_in.discount or 0.0,
        stock_quantity=product_in.stock_quantity,
        image=product_in.image or "/uploads/products/placeholder.svg",
        specifications=product_in.specifications,
        status=initial_status
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return format_product_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Update existing product (Owner Seller or Admin)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    # Verify ownership if not admin
    if current_seller.user.role != UserRole.ADMIN and product.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to modify this product")

    update_data = product_in.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(product, key, val)

    # Check stock vs status
    if product.stock_quantity <= 0 and product.status == ProductStatus.ACTIVE:
        product.status = ProductStatus.OUT_OF_STOCK
    elif product.stock_quantity > 0 and product.status == ProductStatus.OUT_OF_STOCK:
        product.status = ProductStatus.ACTIVE

    db.commit()
    db.refresh(product)
    return format_product_out(product)


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_seller: SellerProfile = Depends(get_current_seller),
    db: Session = Depends(get_db)
):
    """Delete product (Owner Seller or Admin)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    if current_seller.user.role != UserRole.ADMIN and product.seller_id != current_seller.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to delete this product")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}
