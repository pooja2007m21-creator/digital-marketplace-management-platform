import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .routes import (
    auth_routes, user_routes, category_routes, product_routes,
    cart_routes, wishlist_routes, order_routes, review_routes,
    seller_routes, admin_routes
)

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Digital Marketplace Management Platform API",
    description="Professional, full-stack REST API for Digital Marketplace Management Platform with multi-vendor support, customer ordering, role-based access control (Admin, Seller, Customer), simulated payments, and inventory management.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development and demonstration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_routes.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(category_routes.router, prefix="/api")
app.include_router(product_routes.router, prefix="/api")
app.include_router(cart_routes.router, prefix="/api")
app.include_router(wishlist_routes.router, prefix="/api")
app.include_router(order_routes.router, prefix="/api")
app.include_router(review_routes.router, prefix="/api")
app.include_router(seller_routes.router, prefix="/api")
app.include_router(admin_routes.router, prefix="/api")

# Mount upload directory for product images
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(os.path.join(UPLOADS_DIR, "products"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Mount frontend directory for optional direct single-server serving
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.get("/")
def root():
    return {
        "name": "Digital Marketplace Management Platform API",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "frontend_app": "/app/index.html"
    }
