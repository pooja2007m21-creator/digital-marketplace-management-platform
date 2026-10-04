from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from .models import UserRole, UserStatus, SellerApprovalStatus, ProductStatus, OrderStatus, PaymentMethod, PaymentStatus


# ==========================================
# AUTH & USER SCHEMAS
# ==========================================

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=6)
    user_type: UserRole = UserRole.CUSTOMER
    # Optional seller fields if registering as SELLER
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    business_address: Optional[str] = None


class UserLogin(BaseModel):
    username_or_email: str
    password: str
    remember_me: Optional[bool] = False


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str = Field(..., min_length=6)


class UserOut(BaseModel):
    id: int
    full_name: str
    username: str
    email: str
    phone: Optional[str] = None
    role: UserRole
    status: UserStatus
    avatar: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    avatar: Optional[str] = None


class UserStatusUpdate(BaseModel):
    status: UserStatus


# ==========================================
# SELLER PROFILE SCHEMAS
# ==========================================

class SellerProfileOut(BaseModel):
    id: int
    user_id: int
    business_name: str
    business_description: Optional[str] = None
    business_address: Optional[str] = None
    approval_status: SellerApprovalStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserOut] = None

    model_config = ConfigDict(from_attributes=True)


class SellerProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    business_address: Optional[str] = None


class SellerStatusUpdate(BaseModel):
    approval_status: SellerApprovalStatus


# ==========================================
# CATEGORY SCHEMAS
# ==========================================

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    image: Optional[str] = None
    icon: Optional[str] = "fa-box"
    status: Optional[str] = "ACTIVE"


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[str] = None


class CategoryOut(CategoryBase):
    id: int
    created_at: datetime
    product_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# PRODUCT SCHEMAS
# ==========================================

class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    category_id: int
    brand: Optional[str] = None
    price: float = Field(..., gt=0)
    discount: Optional[float] = Field(0.0, ge=0, le=100)
    stock_quantity: int = Field(0, ge=0)
    sku: Optional[str] = None
    image: Optional[str] = None
    specifications: Optional[str] = None
    status: Optional[ProductStatus] = ProductStatus.ACTIVE


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    discount: Optional[float] = None
    stock_quantity: Optional[int] = None
    sku: Optional[str] = None
    image: Optional[str] = None
    specifications: Optional[str] = None
    status: Optional[ProductStatus] = None


class ProductOut(BaseModel):
    id: int
    seller_id: int
    category_id: int
    name: str
    description: Optional[str] = None
    sku: str
    brand: Optional[str] = None
    price: float
    discount: float
    final_price: float
    stock_quantity: int
    image: Optional[str] = None
    specifications: Optional[str] = None
    status: ProductStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Associated info
    category_name: Optional[str] = None
    seller_name: Optional[str] = None
    rating_avg: Optional[float] = 0.0
    review_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    page_size: int
    pages: int


# ==========================================
# CART SCHEMAS
# ==========================================

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1)


class CartItemOut(BaseModel):
    id: int
    cart_id: int
    product_id: int
    quantity: int
    product: Optional[ProductOut] = None
    subtotal: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class CartOut(BaseModel):
    id: int
    user_id: int
    items: List[CartItemOut] = []
    item_count: int = 0
    subtotal: float = 0.0
    discount: float = 0.0
    delivery_charge: float = 0.0
    tax: float = 0.0
    grand_total: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# WISHLIST SCHEMAS
# ==========================================

class WishlistAdd(BaseModel):
    product_id: int


class WishlistItemOut(BaseModel):
    id: int
    wishlist_id: int
    product_id: int
    product: Optional[ProductOut] = None

    model_config = ConfigDict(from_attributes=True)


class WishlistOut(BaseModel):
    id: int
    user_id: int
    items: List[WishlistItemOut] = []
    item_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ORDER & CHECKOUT SCHEMAS
# ==========================================

class CheckoutRequest(BaseModel):
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    delivery_address: str
    city: str
    state: str
    postal_code: str
    payment_method: PaymentMethod = PaymentMethod.COD
    # If simulated online payment:
    card_number: Optional[str] = None
    upi_id: Optional[str] = None


class OrderItemOut(BaseModel):
    id: int
    order_id: int
    product_id: Optional[int] = None
    seller_id: Optional[int] = None
    product_name: str
    product_image: Optional[str] = None
    quantity: int
    unit_price: float
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


class PaymentOut(BaseModel):
    id: int
    order_id: int
    payment_method: PaymentMethod
    transaction_reference: str
    amount: float
    status: PaymentStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    user_id: int
    order_number: str
    subtotal: float
    discount: float
    tax: float
    delivery_charge: float
    total_amount: float
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    order_status: OrderStatus
    customer_name: str
    customer_email: str
    customer_phone: str
    delivery_address: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItemOut] = []
    payment: Optional[PaymentOut] = None

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    order_status: OrderStatus


# ==========================================
# REVIEW SCHEMAS
# ==========================================

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., min_length=2, max_length=150)
    comment: str = Field(..., min_length=5)


class ReviewOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    rating: int
    title: str
    comment: str
    created_at: datetime
    user_name: Optional[str] = None
    product_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# DASHBOARDS & ANALYTICS SCHEMAS
# ==========================================

class CustomerDashboardOut(BaseModel):
    total_orders: int
    pending_orders: int
    wishlist_count: int
    cart_count: int
    recent_orders: List[OrderOut] = []
    recommended_products: List[ProductOut] = []


class SellerDashboardOut(BaseModel):
    total_products: int
    active_products: int
    low_stock_products: int
    total_orders: int
    pending_orders: int
    total_sales: float
    recent_orders: List[Dict[str, Any]] = []
    low_stock_items: List[ProductOut] = []
    top_selling_products: List[Dict[str, Any]] = []
    monthly_sales: List[Dict[str, Any]] = []


class AdminDashboardOut(BaseModel):
    total_customers: int
    total_sellers: int
    total_products: int
    total_orders: int
    total_revenue: float
    pending_seller_approvals: int
    recent_orders: List[OrderOut] = []
    recent_users: List[UserOut] = []
    category_product_counts: List[Dict[str, Any]] = []
    order_status_counts: Dict[str, int] = {}
    sales_overview: List[Dict[str, Any]] = []
