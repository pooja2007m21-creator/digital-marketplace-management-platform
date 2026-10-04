# Digital Marketplace Management Platform

A modern, secure, responsive, and full-featured Full-Stack Web Technology Project demonstrating multi-vendor marketplace workflows, role-based authorization (Admin, Seller, Customer), inventory synchronization, RESTful API integrations, simulated checkout, and verified buyer reviews.

---

## Project Overview

The **Digital Marketplace Management Platform** provides a centralized digital marketplace where customers can discover products, perform dynamic filtering and instant searches, manage shopping carts and wishlists, place orders with simulated payments, track live order fulfillment timelines, and review verified purchases. The system empowers independent merchants with a dedicated Seller Portal for catalog and stock management, while providing platform administrators with full oversight over users, seller onboarding verifications, product catalog moderation, category taxonomies, and analytics reports.

---

## Problem Statement

Traditional single-vendor e-commerce websites limit scalability and diversity for consumers. Creating a multi-vendor marketplace introduces significant technical complexities:
1. **Role-based access control & permission separation** between platform administrators, independent merchants, and customers.
2. **Dynamic inventory tracking & race conditions** during order checkout (automatic status updates to `OUT_OF_STOCK` and automated stock replenishment upon cancellations).
3. **Verified buyer review credibility** ensuring only users who completed orders can submit ratings.
4. **Transparent fulfillment tracking** with multi-step visual timelines.

This platform resolves these challenges using clean REST API design, SQLAlchemy ORM with SQLite, JWT authentication, and responsive Bootstrap 5 interfaces.

---

## Objectives

- Implement a robust **Python FastAPI backend** with RESTful endpoints, CORS configuration, dependency injection, and Pydantic validation.
- Implement **Role-Based Access Control (RBAC)** across three distinct actor roles: `CUSTOMER`, `SELLER`, and `ADMIN`.
- Provide a **modern, responsive frontend** built with HTML5, CSS3, JavaScript (Fetch API), Bootstrap 5, and FontAwesome 6.
- Enable **multi-vendor product management**, category organization, and automated low-stock warnings.
- Build a **database-connected shopping cart & wishlist** tied directly to customer profiles.
- Provide a **simulated checkout & payment workflow** generating unique transaction references (`TXN-DEMO-XXXX`) and instant order receipts.
- Implement a **6-stage visual order tracking timeline** (`PLACED` &rarr; `CONFIRMED` &rarr; `PROCESSING` &rarr; `SHIPPED` &rarr; `OUT_FOR_DELIVERY` &rarr; `DELIVERED`).

---

## User Roles & Capabilities

### 1. Customer
- Register and login with secure JWT token storage.
- Explore products with real-time multi-criteria filtering (Category, Price Slider, Stock Status, Customer Rating, Discount).
- Sort by Newest, Price (Low/High), Rating, Popularity, and Discount.
- View product details, high-res galleries, technical specifications, and verified customer reviews.
- Manage shopping cart (live delivery & tax calculations, quantity modifiers).
- Manage wishlist with one-click "Move to Cart".
- Checkout with delivery address and simulated payment selection (COD vs Simulated Online Card/UPI).
- View order history, track visual progress timeline, and cancel pending orders.
- Submit verified customer reviews on purchased products.
- Manage profile details and update account security passwords.

### 2. Seller
- Register a merchant profile with business name, address, and description (enters `PENDING` approval status).
- Access the **Seller Portal** upon Administrator approval.
- Overview dashboard with sales metrics, revenue chart (Chart.js), recent orders, and low-stock alerts.
- Create, edit, activate/deactivate, and delete store products.
- Upload product image assets with safe extension and file size verification.
- Fast inline inventory management (real-time stock and price adjustments).
- Receive and manage customer orders containing store items with fulfillment status updates.

### 3. Administrator
- Root control over platform operations via the **Admin Console**.
- Real-time KPI summary (Total Customers, Total Merchants, Total Products, Gross Revenue, Orders).
- Sales distribution bar charts and Order Status breakdown donut charts.
- **User Management:** Search, filter by role, activate/deactivate accounts, and delete users.
- **Seller Approval System:** Review merchant applications with `APPROVE`, `REJECT`, `SUSPEND`, and `ACTIVATE` actions.
- **Product Moderation:** Activate/deactivate items across any seller.
- **Category Taxonomies:** Create, edit, and safely delete categories (preventing orphaned products).
- **Global Order Oversight:** Track and override order fulfillment stages.
- **Review Moderation:** Remove inappropriate customer feedback.
- **Reports & Analytics:** Exportable and printable marketplace revenue summaries and top-selling products by volume.

---

## Technology Stack

- **Frontend:**
  - HTML5, CSS3 (Custom design system & CSS variables)
  - JavaScript (ES6+, Fetch API, Async/Await)
  - Bootstrap 5.3 (Responsive Grid & Modals)
  - FontAwesome 6 (Icons)
  - Chart.js (Interactive dashboards & analytics)
- **Backend:**
  - Python 3.10+
  - FastAPI (Modern, high-performance web framework)
  - SQLAlchemy 2.0 (ORM & relation mappings)
  - Pydantic v2 (Data validation & serialization schemas)
  - PyJWT & Bcrypt (Password hashing & JWT Token Auth)
  - Python-Multipart (Safe file & image uploads)
  - Uvicorn (ASGI server)
- **Database:**
  - SQLite (Local development / evaluation)
  - Readily upgradable to PostgreSQL via SQLAlchemy connection strings

---

## System Architecture

```
[ Web Browser Client (HTML5 / Bootstrap 5 / Vanilla JS) ]
                          |
                  REST API Requests (Fetch) + Bearer JWT
                          |
                          v
         [ FastAPI Application (main.py) ]
    /api/auth     /api/products    /api/cart     /api/orders
    /api/users    /api/categories  /api/wishlist /api/seller /api/admin
                          |
              [ Dependency Injection Layer ]
        (get_db, get_current_user, get_current_seller, get_current_admin)
                          |
             [ SQLAlchemy ORM Models ]
                          |
             [ SQLite Database (digital_marketplace.db) ]
```

---

## Database Design

```
+-----------------------------------------------------------------------------------+
|                                  DATABASE SCHEMA                                  |
+-----------------------------------------------------------------------------------+

 users
  ├── id (PK)
  ├── full_name, username (UQ), email (UQ), phone
  ├── password_hash, role (CUSTOMER | SELLER | ADMIN), status (ACTIVE | INACTIVE)
  └── address, city, state, postal_code, created_at

 seller_profiles
  ├── id (PK)
  ├── user_id (FK -> users.id)
  ├── business_name, business_description, business_address
  └── approval_status (PENDING | APPROVED | REJECTED | SUSPENDED)

 categories
  ├── id (PK)
  ├── name (UQ), description, image, icon, status
  └── created_at

 products
  ├── id (PK)
  ├── seller_id (FK -> seller_profiles.id)
  ├── category_id (FK -> categories.id)
  ├── name, description, sku (UQ), brand, price, discount, stock_quantity
  ├── image, specifications, status (ACTIVE | INACTIVE | OUT_OF_STOCK)
  └── created_at, updated_at

 carts & cart_items
  ├── cart_id (FK -> carts.id), product_id (FK -> products.id), quantity

 wishlists & wishlist_items
  ├── wishlist_id (FK -> wishlists.id), product_id (FK -> products.id)

 orders & order_items
  ├── id (PK), user_id (FK -> users.id), order_number (UQ)
  ├── subtotal, discount, tax, delivery_charge, total_amount
  ├── payment_method (COD | SIMULATED_ONLINE), payment_status, order_status
  └── customer_name, customer_email, customer_phone, delivery_address

 payments
  ├── id (PK), order_id (FK -> orders.id)
  ├── payment_method, transaction_reference (UQ), amount, status

 reviews
  ├── id (PK), product_id (FK -> products.id), user_id (FK -> users.id)
  ├── rating (1-5), title, comment, created_at
```

---

## API Documentation

FastAPI automatically generates interactive OpenAPI documentation:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Summary of Key Endpoints:

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new customer or merchant | No |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT token | No |
| `POST` | `/api/auth/forgot-password` | Request password reset code | No |
| `POST` | `/api/auth/reset-password` | Reset password using code | No |
| `GET` | `/api/users/me` | Get authenticated user profile | User |
| `PUT` | `/api/users/me` | Update customer address & info | User |
| `GET` | `/api/products` | Search, filter, and paginate products | No |
| `GET` | `/api/products/{id}` | Single product details & specs | No |
| `POST` | `/api/products/upload-image`| Upload product image asset | Seller / Admin |
| `GET` | `/api/categories` | List categories with product counts | No |
| `GET` | `/api/cart` | Get customer shopping cart | Customer |
| `POST` | `/api/cart` | Add product to cart | Customer |
| `PUT` | `/api/cart/{id}` | Update cart item quantity | Customer |
| `DELETE`| `/api/cart/{id}` | Remove item from cart | Customer |
| `GET` | `/api/wishlist` | Get saved wishlist items | Customer |
| `POST` | `/api/wishlist/{id}/move-to-cart` | Move wishlist product to cart | Customer |
| `POST` | `/api/orders` | Place order with simulated payment | Customer |
| `GET` | `/api/orders` | Customer order history list | Customer |
| `GET` | `/api/orders/{id}` | Order receipt & tracking status | Customer / Admin |
| `POST` | `/api/orders/{id}/cancel` | Cancel order & restore inventory | Customer / Admin |
| `POST` | `/api/products/{id}/reviews`| Submit verified buyer review | Customer (Buyer) |
| `GET` | `/api/seller/dashboard` | Seller revenue stats & analytics | Approved Seller |
| `GET` | `/api/seller/products` | List seller's products | Approved Seller |
| `PUT` | `/api/seller/inventory/{id}`| Fast inventory stock & price update | Approved Seller |
| `GET` | `/api/seller/orders` | List customer orders for seller | Approved Seller |
| `GET` | `/api/admin/dashboard` | Platform metrics & charts data | Administrator |
| `GET` | `/api/admin/users` | Admin user management list | Administrator |
| `PATCH`| `/api/admin/sellers/{id}/status`| Approve/Reject/Suspend seller | Administrator |
| `GET` | `/api/admin/reports` | Comprehensive revenue report | Administrator |

---

## Project Structure

```
digital_marketplace/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI entrypoint, CORS, static file mounts
│   │   ├── database.py           # SQLite connection & sessionmaker
│   │   ├── models.py             # SQLAlchemy models (User, Product, Order, etc.)
│   │   ├── schemas.py            # Pydantic validation schemas
│   │   ├── security.py           # Bcrypt hashing & PyJWT token utilities
│   │   ├── dependencies.py       # Auth guards (get_current_user, get_seller, get_admin)
│   │   │
│   │   ├── routes/
│   │   │   ├── auth_routes.py    # Login, register, password reset
│   │   │   ├── user_routes.py    # Customer profile & dashboard
│   │   │   ├── product_routes.py # Search, filter, sorting, pagination, image upload
│   │   │   ├── category_routes.py# Category CRUD
│   │   │   ├── cart_routes.py    # Shopping cart CRUD
│   │   │   ├── wishlist_routes.py# Wishlist CRUD & move to cart
│   │   │   ├── order_routes.py   # Checkout, stock deduction, receipts, cancellation
│   │   │   ├── review_routes.py  # Verified buyer reviews
│   │   │   ├── seller_routes.py  # Seller portal stats, inventory, orders
│   │   │   └── admin_routes.py   # Admin console operations & analytics
│   │   │
│   │   └── services/             # Modular service layers
│   │
│   ├── uploads/
│   │   └── products/             # Secure local product image storage
│   │
│   ├── requirements.txt
│   ├── seed_data.py              # Realistic sample data populator
│   └── digital_marketplace.db    # SQLite database file
│
├── frontend/
│   ├── index.html                # Marketplace homepage & hero banner
│   ├── login.html                # Universal login with 1-click demo badges
│   ├── register.html             # Customer & Seller registration
│   ├── products.html             # Catalog with sidebar filters & sorting
│   ├── product-details.html      # Product info, specs & verified reviews
│   ├── categories.html           # Browse categories grid
│   ├── cart.html                 # Shopping cart with live cost calculations
│   ├── wishlist.html             # Saved wishlist
│   ├── checkout.html             # Delivery address & simulated payment
│   ├── orders.html               # Customer order history
│   ├── order-details.html        # Order receipt & 6-stage visual tracking
│   ├── profile.html              # Customer profile & password change
│   ├── about.html                # Platform overview
│   ├── contact.html              # Contact support inquiry form
│   │
│   ├── seller/
│   │   ├── login.html            # Seller direct login
│   │   ├── dashboard.html        # Seller analytics & sales charts
│   │   ├── products.html         # Seller products management
│   │   ├── add-product.html      # Product creation/edit form with image preview
│   │   ├── inventory.html        # Fast stock & price editor
│   │   └── orders.html           # Seller orders fulfillment
│   │
│   ├── admin/
│   │   ├── login.html            # Admin direct login
│   │   ├── dashboard.html        # Admin metrics, revenue & status charts
│   │   ├── users.html            # User account moderation
│   │   ├── sellers.html          # Seller application approval/rejection
│   │   ├── products.html         # Catalog moderation
│   │   ├── categories.html       # Category CRUD modal
│   │   ├── orders.html           # Global order management
│   │   ├── reviews.html          # Customer review moderation
│   │   └── reports.html          # Sales & performance reports
│   │
│   ├── css/
│   │   ├── style.css             # Base typography, variables & toast notifications
│   │   ├── auth.css              # Auth card styling
│   │   ├── marketplace.css       # Product cards, badges, hero & search
│   │   ├── dashboard.css         # Sidebar layouts & stat cards
│   │   ├── seller.css            # Seller portal specific styling
│   │   └── admin.css             # Admin badge & management styles
│   │
│   ├── js/
│   │   ├── api.js                # Centralized API fetch wrapper, JWT & toast helpers
│   │   ├── auth.js               # Login, register, password reset & demo fillers
│   │   ├── products.js           # Catalog listing, filters, search & pagination
│   │   ├── product-details.js    # Gallery, quantity counter & reviews submission
│   │   ├── cart.js               # Cart CRUD & totals
│   │   ├── wishlist.js           # Wishlist & move to cart
│   │   ├── checkout.js           # Address validation & simulated checkout
│   │   ├── orders.js             # Order history & visual timeline tracker
│   │   ├── profile.js            # Customer profile settings
│   │   ├── seller.js             # Seller stats, Chart.js & inventory
│   │   └── admin.js              # Admin analytics, user moderation & reports
│   │
│   └── assets/
│       └── images/placeholder.svg
│
├── README.md
└── .gitignore
```

---

## Installation & Setup

### 1. Backend Setup

1. Open your terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Populate the database with realistic sample categories, products, merchants, users, orders, and reviews:
   ```bash
   python seed_data.py
   ```

5. Start the FastAPI backend server with Uvicorn:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

The backend REST API is now live at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

### 2. Frontend Setup

You can run the frontend in any of the following ways:

#### Option A: Direct FastAPI Static Mount (Recommended - No extra server needed!)
The backend mounts the frontend static directory automatically. Simply open:
- **Storefront:** [http://127.0.0.1:8000/app/index.html](http://127.0.0.1:8000/app/index.html)
- **Seller Portal:** [http://127.0.0.1:8000/app/seller/dashboard.html](http://127.0.0.1:8000/app/seller/dashboard.html)
- **Admin Console:** [http://127.0.0.1:8000/app/admin/dashboard.html](http://127.0.0.1:8000/app/admin/dashboard.html)

#### Option B: VS Code Live Server or Local Static Server
If serving `frontend/` on port 5500 or 3000 (e.g. via VS Code Live Server):
- The frontend is pre-configured in `frontend/js/api.js` to automatically communicate with `http://127.0.0.1:8000/api` via enabled CORS.

---

## Demo Credentials

The platform includes convenient 1-click demo credential chips on the login pages. You can also use the credentials below:

| Role | Name / Business | Username / Email | Password | Status |
|---|---|---|---|---|
| **Administrator** | Marketplace Admin | `admin@marketplace.com` | `admin123` | Active |
| **Seller 1** | Apex Tech Hub | `apextech@marketplace.com` | `seller123` | Approved |
| **Seller 2** | Vogue Trends | `voguetrends@marketplace.com` | `seller123` | Approved |
| **Seller 3** | BookCraft & Stationery | `bookcraft@marketplace.com` | `seller123` | Pending Approval |
| **Customer 1** | John Doe | `john.doe@example.com` | `customer123` | Active |
| **Customer 2** | Sarah Smith | `sarah.smith@example.com` | `customer123` | Active |

---

## Security Features

- **Password Hashing:** Passwords are encrypted using modern `bcrypt` algorithms before saving into the database.
- **JWT Authorization:** Role-encoded JSON Web Tokens with expiry validation protect private API routes.
- **Role-Based Guards:** Independent verification checks ensure Customers cannot access merchant tools and Sellers cannot modify peer products.
- **SQL Injection Defense:** Strict SQLAlchemy parameterized queries and ORM object graphs prevent raw SQL vulnerabilities.
- **Image Upload Security:** Whitelisted MIME and file extensions (`.jpg`, `.jpeg`, `.png`, `.webp`, `.svg`) with UUID-based unique server file paths.
- **Sensitive Data Privacy:** Password hashes are omitted from serialized API responses.

---

## Future Enhancements

- **PostgreSQL / MySQL Migration:** Production deployment with containerized PostgreSQL.
- **Real Payment Gateway Integration:** Razorpay / Stripe webhook event integration.
- **Email Notifications:** Automated transactional emails via SMTP/SendGrid.
- **Real-Time WebSockets:** Live chat between buyers and merchants.

---

## Author

Developed for **Full-Stack Web Technology Academic Project Demonstration**.
All rights reserved © 2026.
