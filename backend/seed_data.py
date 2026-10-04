import os
import sys
import uuid
from datetime import datetime, timedelta

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import (
    User, UserRole, UserStatus, SellerProfile, SellerApprovalStatus,
    Category, Product, ProductStatus, Cart, Wishlist,
    Order, OrderItem, OrderStatus, Payment, PaymentMethod, PaymentStatus, Review
)
from app.security import hash_password

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "products")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def create_svg_placeholder(filename: str, title: str, category: str, bg_color: str = "#4f46e5"):
    """Generate a clean SVG placeholder image."""
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
  <rect width="600" height="600" fill="{bg_color}" rx="24"/>
  <circle cx="300" cy="220" r="100" fill="#ffffff" opacity="0.15"/>
  <rect x="230" y="160" width="140" height="120" rx="16" fill="#ffffff" opacity="0.9"/>
  <path d="M260 210 L300 240 L340 210" stroke="{bg_color}" stroke-width="8" stroke-linecap="round" fill="none"/>
  <text x="300" y="380" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">{title[:28]}</text>
  <rect x="200" y="420" width="200" height="36" rx="18" fill="#ffffff" opacity="0.2"/>
  <text x="300" y="444" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="600" fill="#ffffff" text-anchor="middle">{category.upper()}</text>
  <text x="300" y="520" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" fill="#ffffff" opacity="0.75" text-anchor="middle">Digital Marketplace Verified</text>
</svg>"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    return f"/uploads/products/{filename}"


def seed_database():
    print("Initializing database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Seeding Users...")
        # 1. ADMIN USER
        admin_user = User(
            full_name="Marketplace Administrator",
            username="admin",
            email="admin@marketplace.com",
            phone="+91 9876543210",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            address="Level 10, Marketplace Tower",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001"
        )
        db.add(admin_user)
        db.flush()

        # Admin cart and wishlist
        db.add(Cart(user_id=admin_user.id))
        db.add(Wishlist(user_id=admin_user.id))

        # 2. SELLERS
        seller1_user = User(
            full_name="Vikram Mehta",
            username="seller_apex",
            email="apextech@marketplace.com",
            phone="+91 9811223344",
            password_hash=hash_password("seller123"),
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            address="Tech Zone 4, Cyber City",
            city="Hyderabad",
            state="Telangana",
            postal_code="500081"
        )
        db.add(seller1_user)
        db.flush()
        seller1_profile = SellerProfile(
            user_id=seller1_user.id,
            business_name="Apex Tech Hub",
            business_description="Premium smart gadgets, audio, laptops, and innovative electronics.",
            business_address="Shop 102, Cyber Towers, Hitec City, Hyderabad",
            approval_status=SellerApprovalStatus.APPROVED
        )
        db.add(seller1_profile)
        db.add(Cart(user_id=seller1_user.id))
        db.add(Wishlist(user_id=seller1_user.id))

        seller2_user = User(
            full_name="Ananya Verma",
            username="seller_vogue",
            email="voguetrends@marketplace.com",
            phone="+91 9822334455",
            password_hash=hash_password("seller123"),
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            address="Fashion Street, Linking Road",
            city="Mumbai",
            state="Maharashtra",
            postal_code="400050"
        )
        db.add(seller2_user)
        db.flush()
        seller2_profile = SellerProfile(
            user_id=seller2_user.id,
            business_name="Vogue Trends & Apparel",
            business_description="Contemporary urban fashion, premium apparel, footwear, and designer accessories.",
            business_address="Linking Road Fashion Mall, Bandra West, Mumbai",
            approval_status=SellerApprovalStatus.APPROVED
        )
        db.add(seller2_profile)
        db.add(Cart(user_id=seller2_user.id))
        db.add(Wishlist(user_id=seller2_user.id))

        seller3_user = User(
            full_name="Ramesh Sharma",
            username="seller_bookcraft",
            email="bookcraft@marketplace.com",
            phone="+91 9833445566",
            password_hash=hash_password("seller123"),
            role=UserRole.SELLER,
            status=UserStatus.ACTIVE,
            address="Heritage Square, Daryaganj",
            city="New Delhi",
            state="Delhi",
            postal_code="110002"
        )
        db.add(seller3_user)
        db.flush()
        seller3_profile = SellerProfile(
            user_id=seller3_user.id,
            business_name="BookCraft & Stationery",
            business_description="Classic literature, academic resources, journals, and executive office stationery.",
            business_address="Heritage Book Alley, Daryaganj, New Delhi",
            approval_status=SellerApprovalStatus.PENDING # Demonstrates Pending Approval workflow
        )
        db.add(seller3_profile)
        db.add(Cart(user_id=seller3_user.id))
        db.add(Wishlist(user_id=seller3_user.id))

        # 3. CUSTOMERS
        customers_data = [
            ("John Doe", "johndoe", "john.doe@example.com", "+91 9988776655", "Flat 402, Green Valley Apartments", "Bengaluru", "Karnataka", "560034"),
            ("Sarah Smith", "sarahsmith", "sarah.smith@example.com", "+91 9877665544", "12B Sunrise Enclave", "Pune", "Maharashtra", "411001"),
            ("Rahul Sharma", "rahulsharma", "rahul.sharma@example.com", "+91 9766554433", "74 Park View Colony", "New Delhi", "Delhi", "110016"),
            ("Priya Patel", "priyapatel", "priya.patel@example.com", "+91 9655443322", "88 Marine Drive", "Mumbai", "Maharashtra", "400020"),
            ("Alex Taylor", "alextaylor", "alex.taylor@example.com", "+91 9544332211", "Flat 101 Lakefront Heights", "Chennai", "Tamil Nadu", "600028"),
        ]

        customer_users = []
        for name, uname, email, phone, addr, city, st, pin in customers_data:
            c_user = User(
                full_name=name,
                username=uname,
                email=email,
                phone=phone,
                password_hash=hash_password("customer123"),
                role=UserRole.CUSTOMER,
                status=UserStatus.ACTIVE,
                address=addr,
                city=city,
                state=st,
                postal_code=pin
            )
            db.add(c_user)
            db.flush()
            db.add(Cart(user_id=c_user.id))
            db.add(Wishlist(user_id=c_user.id))
            customer_users.append(c_user)

        print("Seeding Categories...")
        categories_data = [
            ("Electronics", "Smartphones, Laptops, Audio Gear & Wearables", "fa-laptop", "#2563eb"),
            ("Fashion", "Men & Women Apparel, Casual & Formal Wear", "fa-tshirt", "#db2777"),
            ("Books", "Bestsellers, Academic, Sci-Fi & Self-Development", "fa-book", "#d97706"),
            ("Home & Kitchen", "Modern Cookware, Decor, Furnishings & Appliances", "fa-couch", "#059669"),
            ("Sports & Fitness", "Gym Equipment, Activewear, Footwear & Accessories", "fa-dumbbell", "#ea580c"),
            ("Beauty & Personal Care", "Skincare, Fragrances, Grooming & Cosmetics", "fa-spa", "#9333ea"),
            ("Stationery & Office", "Notebooks, Pens, Planners & Art Supplies", "fa-pen-fancy", "#0284c7"),
            ("Accessories", "Watches, Bags, Wallets, Sunglasses & Jewelry", "fa-gem", "#4f46e5"),
        ]

        categories_map = {}
        for cat_name, desc, icon, color in categories_data:
            cat_img = create_svg_placeholder(f"cat_{cat_name.lower().replace(' ', '_')}.svg", cat_name, "Category", color)
            cat = Category(
                name=cat_name,
                description=desc,
                image=cat_img,
                icon=icon,
                status="ACTIVE"
            )
            db.add(cat)
            db.flush()
            categories_map[cat_name] = cat

        print("Seeding Products...")
        products_data = [
            # Electronics (Seller 1)
            {
                "seller": seller1_profile,
                "category": categories_map["Electronics"],
                "name": "Aura Pro Wireless Noise-Cancelling Headphones",
                "description": "Engineered with 40mm custom drivers and active noise cancellation (ANC), offering up to 35 hours of battery life and ultra-low latency wireless connectivity.",
                "brand": "SonicAura",
                "price": 8999.00,
                "discount": 15.0,
                "stock": 45,
                "sku": "ELEC-AURAPRO-01",
                "specs": "Driver: 40mm | Battery: 35h | Bluetooth 5.3 | ANC: 38dB | Fast Charge: 10m for 5h",
                "color": "#1e3a8a"
            },
            {
                "seller": seller1_profile,
                "category": categories_map["Electronics"],
                "name": "UltraView 4K UHD Smart OLED Monitor 27-inch",
                "description": "Stunning 4K resolution with 144Hz refresh rate, 99% DCI-P3 color accuracy, and HDR400 for professional creators and gamers.",
                "brand": "VisionX",
                "price": 34999.00,
                "discount": 10.0,
                "stock": 12,
                "sku": "ELEC-ULTRAVIEW-02",
                "specs": "Resolution: 3840x2160 | Refresh: 144Hz | Panel: IPS OLED | Ports: 2x HDMI 2.1, DP 1.4, USB-C 65W",
                "color": "#0f172a"
            },
            {
                "seller": seller1_profile,
                "category": categories_map["Electronics"],
                "name": "PulseFit Pro Smartwatch with AMOLED Display",
                "description": "Comprehensive health tracking including ECG, SpO2, Sleep stages, and 100+ workout modes with 14-day battery life.",
                "brand": "PulseFit",
                "price": 4499.00,
                "discount": 20.0,
                "stock": 25,
                "sku": "ELEC-PULSEFIT-03",
                "specs": "Display: 1.43\" AMOLED | Water Resistance: 5ATM | GPS: Built-in Dual Band | Battery: 14 Days",
                "color": "#0284c7"
            },
            {
                "seller": seller1_profile,
                "category": categories_map["Electronics"],
                "name": "HyperGlide Ergonomic Mechanical Keyboard",
                "description": "Hot-swappable tactile switches, per-key RGB backlighting, aircraft-grade aluminum frame, and multi-device Bluetooth/2.4G.",
                "brand": "KeyMaster",
                "price": 5499.00,
                "discount": 5.0,
                "stock": 3, # Low stock alert trigger
                "sku": "ELEC-HYPERGLIDE-04",
                "specs": "Switches: Gateron Brown | Layout: 75% | Connectivity: Tri-Mode | Battery: 4000mAh",
                "color": "#312e81"
            },

            # Fashion (Seller 2)
            {
                "seller": seller2_profile,
                "category": categories_map["Fashion"],
                "name": "Urban Classic Pure Linen Casual Shirt",
                "description": "Crafted from 100% breathable organic European linen with tailored fit, mother-of-pearl buttons, and lightweight all-day comfort.",
                "brand": "VogueAura",
                "price": 2199.00,
                "discount": 10.0,
                "stock": 50,
                "sku": "FASH-LINENSHIRT-01",
                "specs": "Material: 100% Organic Linen | Fit: Regular Slim | Collar: Spread | Sleeve: Full",
                "color": "#831843"
            },
            {
                "seller": seller2_profile,
                "category": categories_map["Fashion"],
                "name": "EdgeFlex Denim Stretch Jacket - Midnight Blue",
                "description": "Classic vintage washed denim with 2% elastane for seamless mobility. Features reinforced brass buttons and internal utility pockets.",
                "brand": "DenimCraft",
                "price": 3899.00,
                "discount": 25.0,
                "stock": 18,
                "sku": "FASH-DENIMJKT-02",
                "specs": "Fabric: 98% Cotton 2% Elastane | Wash: Medium Indigo Vintage | Closure: Button Placket",
                "color": "#1e293b"
            },
            {
                "seller": seller2_profile,
                "category": categories_map["Fashion"],
                "name": "AeroStep Breathable Lightweight Running Shoes",
                "description": "Ultra-responsive nitrogen-infused foam midsole with high-grip rubber outsole for effortless performance and street style.",
                "brand": "AeroSport",
                "price": 3299.00,
                "discount": 15.0,
                "stock": 30,
                "sku": "FASH-AEROSTEP-03",
                "specs": "Upper: Engineered Jacquard Mesh | Midsole: NitroFoam | Weight: 240g | Drop: 8mm",
                "color": "#be185d"
            },

            # Books (Seller 1 or Admin)
            {
                "seller": seller1_profile,
                "category": categories_map["Books"],
                "name": "System Architecture & Scalable Web Systems",
                "description": "Comprehensive guide covering microservices, distributed caching, database sharding, event-driven architectures, and cloud resilience.",
                "brand": "TechPress",
                "price": 1299.00,
                "discount": 10.0,
                "stock": 40,
                "sku": "BOOK-SYSARCH-01",
                "specs": "Pages: 580 | Edition: 3rd Revised | Language: English | Format: Hardcover",
                "color": "#78350f"
            },
            {
                "seller": seller1_profile,
                "category": categories_map["Books"],
                "name": "Mastering Full-Stack Web Development with Python",
                "description": "From FastAPI backend design, ORMs, JWT security to modern responsive frontend interfaces, REST API patterns, and deployment.",
                "brand": "O'Reilly Media",
                "price": 1499.00,
                "discount": 20.0,
                "stock": 35,
                "sku": "BOOK-FULLSTACK-02",
                "specs": "Pages: 640 | Publisher: TechNova | Format: Paperback | Year: 2026",
                "color": "#92400e"
            },

            # Home & Kitchen (Seller 2)
            {
                "seller": seller2_profile,
                "category": categories_map["Home & Kitchen"],
                "name": "AromaBlend Barista Touch Espresso Machine",
                "description": "15-bar Italian pump with integrated conical burr grinder, micro-foam steam wand, and precision PID temperature control.",
                "brand": "AromaBrew",
                "price": 18499.00,
                "discount": 12.0,
                "stock": 8,
                "sku": "HOME-ESPRESSO-01",
                "specs": "Pressure: 15 Bar | Grinder: 30 Settings | Tank: 2.0L | Boiler: Thermoblock Fast Heat",
                "color": "#064e3b"
            },
            {
                "seller": seller2_profile,
                "category": categories_map["Home & Kitchen"],
                "name": "Nordic Minimalist Ceramic Dinnerware Set (16 Pcs)",
                "description": "Handcrafted stoneware finished in matte charcoal glaze. Microwave, oven, and dishwasher safe.",
                "brand": "TerraLiving",
                "price": 4299.00,
                "discount": 15.0,
                "stock": 15,
                "sku": "HOME-CERAMIC-02",
                "specs": "Pieces: 16 (4 Dinner, 4 Salad, 4 Bowls, 4 Mugs) | Material: Lead-free Stoneware",
                "color": "#047857"
            },

            # Sports & Fitness (Seller 1)
            {
                "seller": seller1_profile,
                "category": categories_map["Sports & Fitness"],
                "name": "FlexiCore Adjustable Dumbbell Set (2.5kg - 24kg)",
                "description": "Quick-turn dial mechanism replaces 15 sets of weights in a compact, durable space-saving footprint with anti-roll base.",
                "brand": "IronForge",
                "price": 12999.00,
                "discount": 18.0,
                "stock": 4, # Low stock alert
                "sku": "SPRT-DUMBBELL-01",
                "specs": "Weight Range: 2.5 - 24 kg | Increment: 15 adjustments | Coating: Thermoplastic Rubber",
                "color": "#7c2d12"
            },

            # Beauty & Personal Care (Seller 2)
            {
                "seller": seller2_profile,
                "category": categories_map["Beauty & Personal Care"],
                "name": "Botanical Glow Hyaluronic & Vitamin C Facial Serum",
                "description": "Pure botanical active formulation designed to boost skin hydration, brighten dull complexion, and support collagen elasticity.",
                "brand": "PureGlow",
                "price": 1199.00,
                "discount": 10.0,
                "stock": 60,
                "sku": "BEAUTY-SERUM-01",
                "specs": "Volume: 50ml | Skin Type: All Skin Types | Key Actives: 2% HA, 10% Vitamin C, Niacinamide",
                "color": "#581c87"
            },

            # Stationery (Seller 2)
            {
                "seller": seller2_profile,
                "category": categories_map["Stationery & Office"],
                "name": "Executive Leather Bound Refillable Journal & Pen Set",
                "description": "Hand-stitched genuine leather cover with 120gsm archival-grade fountain-pen friendly ivory paper and brushed brass rollerball pen.",
                "brand": "ArtisanCraft",
                "price": 1699.00,
                "discount": 15.0,
                "stock": 28,
                "sku": "STAT-JOURNAL-01",
                "specs": "Paper: 120 GSM Acid-Free | Binding: Refillable Leather Binder | Size: A5",
                "color": "#075985"
            },

            # Accessories (Seller 2)
            {
                "seller": seller2_profile,
                "category": categories_map["Accessories"],
                "name": "Chronos Automatic Sapphire Mechanical Watch",
                "description": "Self-winding mechanical movement with exhibition case-back, anti-reflective sapphire crystal, and premium Italian leather strap.",
                "brand": "Chronos",
                "price": 14999.00,
                "discount": 20.0,
                "stock": 9,
                "sku": "ACC-CHRONOS-01",
                "specs": "Case: 41mm 316L Stainless Steel | Glass: Sapphire Crystal | Water Resistance: 100M",
                "color": "#3730a3"
            },
            {
                "seller": seller2_profile,
                "category": categories_map["Accessories"],
                "name": "Voyager Anti-Theft Water-Resistant Laptop Backpack",
                "description": "TSA-friendly 180-degree lay-flat opening, hidden RFID-blocking pockets, USB charging pass-through, and padded 16\" laptop sleeve.",
                "brand": "UrbanPack",
                "price": 2899.00,
                "discount": 10.0,
                "stock": 35,
                "sku": "ACC-VOYAGER-02",
                "specs": "Capacity: 28L | Material: 900D Ballistic Nylon | Laptop Fit: Up to 16.5-inch",
                "color": "#1e1b4b"
            }
        ]

        created_products = []
        for p in products_data:
            img_filename = f"prod_{p['sku'].lower().replace('-', '_')}.svg"
            img_url = create_svg_placeholder(img_filename, p["name"], p["category"].name, p["color"])
            
            prod = Product(
                seller_id=p["seller"].id,
                category_id=p["category"].id,
                name=p["name"],
                description=p["description"],
                brand=p["brand"],
                price=p["price"],
                discount=p["discount"],
                stock_quantity=p["stock"],
                sku=p["sku"],
                image=img_url,
                specifications=p["specs"],
                status=ProductStatus.ACTIVE if p["stock"] > 0 else ProductStatus.OUT_OF_STOCK
            )
            db.add(prod)
            db.flush()
            created_products.append(prod)

        print("Seeding Sample Orders & Reviews...")
        # Customer 0 (John Doe) orders
        c_john = customer_users[0]
        c_sarah = customer_users[1]
        c_rahul = customer_users[2]

        # Order 1: Delivered
        p1 = created_products[0] # Headphones
        p2 = created_products[7] # Book 1
        subtotal_1 = round((p1.final_price * 1) + (p2.final_price * 1), 2)
        deliv_1 = 0.0 # Free delivery
        tax_1 = round(subtotal_1 * 0.05, 2)
        total_1 = round(subtotal_1 + deliv_1 + tax_1, 2)

        order1 = Order(
            user_id=c_john.id,
            order_number="ORD-20261001-A19F82",
            subtotal=subtotal_1,
            discount=0.0,
            tax=tax_1,
            delivery_charge=deliv_1,
            total_amount=total_1,
            payment_method=PaymentMethod.SIMULATED_ONLINE,
            payment_status=PaymentStatus.SUCCESS,
            order_status=OrderStatus.DELIVERED,
            customer_name=c_john.full_name,
            customer_email=c_john.email,
            customer_phone=c_john.phone,
            delivery_address=f"{c_john.address}, {c_john.city}, {c_john.state} - {c_john.postal_code}",
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add(order1)
        db.flush()

        db.add(OrderItem(
            order_id=order1.id,
            product_id=p1.id,
            seller_id=p1.seller_id,
            product_name=p1.name,
            product_image=p1.image,
            quantity=1,
            unit_price=p1.final_price,
            subtotal=p1.final_price
        ))
        db.add(OrderItem(
            order_id=order1.id,
            product_id=p2.id,
            seller_id=p2.seller_id,
            product_name=p2.name,
            product_image=p2.image,
            quantity=1,
            unit_price=p2.final_price,
            subtotal=p2.final_price
        ))
        db.add(Payment(
            order_id=order1.id,
            payment_method=PaymentMethod.SIMULATED_ONLINE,
            transaction_reference="TXN-DEMO-991823",
            amount=total_1,
            status=PaymentStatus.SUCCESS,
            created_at=datetime.utcnow() - timedelta(days=5)
        ))

        # Reviews for Order 1 items
        db.add(Review(
            product_id=p1.id,
            user_id=c_john.id,
            rating=5,
            title="Exceptional Audio Quality and ANC!",
            comment="The active noise cancellation is remarkable, and battery life easily lasts my entire work week. Highly recommended!"
        ))
        db.add(Review(
            product_id=p2.id,
            user_id=c_john.id,
            rating=5,
            title="A must-read for distributed systems engineers",
            comment="Well-structured, concise, and full of practical real-world architectural design patterns."
        ))

        # Order 2: Shipped
        p3 = created_products[4] # Linen Shirt
        p4 = created_products[14] # Chronos Watch
        subtotal_2 = round((p3.final_price * 2) + (p4.final_price * 1), 2)
        tax_2 = round(subtotal_2 * 0.05, 2)
        total_2 = round(subtotal_2 + tax_2, 2)

        order2 = Order(
            user_id=c_sarah.id,
            order_number="ORD-20261002-88B12C",
            subtotal=subtotal_2,
            discount=0.0,
            tax=tax_2,
            delivery_charge=0.0,
            total_amount=total_2,
            payment_method=PaymentMethod.SIMULATED_ONLINE,
            payment_status=PaymentStatus.SUCCESS,
            order_status=OrderStatus.SHIPPED,
            customer_name=c_sarah.full_name,
            customer_email=c_sarah.email,
            customer_phone=c_sarah.phone,
            delivery_address=f"{c_sarah.address}, {c_sarah.city}, {c_sarah.state} - {c_sarah.postal_code}",
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        db.add(order2)
        db.flush()
        db.add(OrderItem(
            order_id=order2.id,
            product_id=p3.id,
            seller_id=p3.seller_id,
            product_name=p3.name,
            product_image=p3.image,
            quantity=2,
            unit_price=p3.final_price,
            subtotal=round(p3.final_price * 2, 2)
        ))
        db.add(OrderItem(
            order_id=order2.id,
            product_id=p4.id,
            seller_id=p4.seller_id,
            product_name=p4.name,
            product_image=p4.image,
            quantity=1,
            unit_price=p4.final_price,
            subtotal=p4.final_price
        ))
        db.add(Payment(
            order_id=order2.id,
            payment_method=PaymentMethod.SIMULATED_ONLINE,
            transaction_reference="TXN-DEMO-441209",
            amount=total_2,
            status=PaymentStatus.SUCCESS,
            created_at=datetime.utcnow() - timedelta(days=2)
        ))

        # Order 3: Processing (Cash on Delivery)
        p5 = created_products[9] # Espresso Machine
        subtotal_3 = p5.final_price
        tax_3 = round(subtotal_3 * 0.05, 2)
        total_3 = round(subtotal_3 + tax_3, 2)

        order3 = Order(
            user_id=c_rahul.id,
            order_number="ORD-20261003-CC901A",
            subtotal=subtotal_3,
            discount=0.0,
            tax=tax_3,
            delivery_charge=0.0,
            total_amount=total_3,
            payment_method=PaymentMethod.COD,
            payment_status=PaymentStatus.PENDING,
            order_status=OrderStatus.PROCESSING,
            customer_name=c_rahul.full_name,
            customer_email=c_rahul.email,
            customer_phone=c_rahul.phone,
            delivery_address=f"{c_rahul.address}, {c_rahul.city}, {c_rahul.state} - {c_rahul.postal_code}",
            created_at=datetime.utcnow() - timedelta(hours=18)
        )
        db.add(order3)
        db.flush()
        db.add(OrderItem(
            order_id=order3.id,
            product_id=p5.id,
            seller_id=p5.seller_id,
            product_name=p5.name,
            product_image=p5.image,
            quantity=1,
            unit_price=p5.final_price,
            subtotal=p5.final_price
        ))
        db.add(Payment(
            order_id=order3.id,
            payment_method=PaymentMethod.COD,
            transaction_reference="TXN-COD-PENDING-1",
            amount=total_3,
            status=PaymentStatus.PENDING,
            created_at=datetime.utcnow() - timedelta(hours=18)
        ))

        # Additional Reviews
        db.add(Review(
            product_id=created_products[2].id, # Pulsefit
            user_id=customer_users[3].id,
            rating=4,
            title="Great fitness tracker for daily workouts",
            comment="The AMOLED screen is crisp outdoors and GPS connects fast. Battery is solid 12 days."
        ))
        db.add(Review(
            product_id=created_products[15].id, # Laptop backpack
            user_id=customer_users[4].id,
            rating=5,
            title="Perfect travel & work companion",
            comment="Very well constructed with durable zippers and smart pocket layout for laptops and chargers."
        ))

        db.commit()
        print("Database successfully seeded!")
        print("="*60)
        print("DEMO CREDENTIALS:")
        print("ADMIN:    admin@marketplace.com      / admin123")
        print("SELLER 1: apextech@marketplace.com   / seller123 (Approved)")
        print("SELLER 2: voguetrends@marketplace.com/ seller123 (Approved)")
        print("SELLER 3: bookcraft@marketplace.com  / seller123 (Pending)")
        print("CUSTOMER: john.doe@example.com       / customer123")
        print("CUSTOMER: sarah.smith@example.com    / customer123")
        print("="*60)

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
