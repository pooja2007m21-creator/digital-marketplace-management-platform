import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from .database import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class SellerApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class ProductStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class OrderStatus(str, enum.Enum):
    PLACED = "PLACED"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    COD = "COD"
    SIMULATED_ONLINE = "SIMULATED_ONLINE"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    avatar = Column(String(255), nullable=True)
    
    # Address details
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    seller_profile = relationship("SellerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    cart = relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
    wishlist = relationship("Wishlist", back_populates="user", uselist=False, cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    reviews = relationship("Review", back_populates="user")


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(150), nullable=False)
    business_description = Column(Text, nullable=True)
    business_address = Column(Text, nullable=True)
    approval_status = Column(SQLEnum(SellerApprovalStatus), default=SellerApprovalStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="seller_profile")
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    image = Column(String(255), nullable=True)
    icon = Column(String(100), nullable=True, default="fa-box")
    status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    name = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    brand = Column(String(100), nullable=True)
    price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0) # Percentage e.g. 10.0 for 10%
    stock_quantity = Column(Integer, default=0, nullable=False)
    image = Column(String(255), nullable=True)
    specifications = Column(Text, nullable=True) # JSON or key-value formatted
    status = Column(SQLEnum(ProductStatus), default=ProductStatus.ACTIVE, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seller = relationship("SellerProfile", back_populates="products")
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    wishlist_items = relationship("WishlistItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    @property
    def final_price(self) -> float:
        if self.discount and self.discount > 0:
            return round(self.price * (1 - (self.discount / 100.0)), 2)
        return round(self.price, 2)


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")


class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wishlist")
    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id = Column(Integer, primary_key=True, index=True)
    wishlist_id = Column(Integer, ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    wishlist = relationship("Wishlist", back_populates="items")
    product = relationship("Product", back_populates="wishlist_items")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    
    subtotal = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    delivery_charge = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.COD, nullable=False)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    order_status = Column(SQLEnum(OrderStatus), default=OrderStatus.PLACED, nullable=False)
    
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    delivery_address = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.id", ondelete="SET NULL"), nullable=True)
    
    product_name = Column(String(200), nullable=False)
    product_image = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    transaction_reference = Column(String(100), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False) # 1 to 5
    title = Column(String(150), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
