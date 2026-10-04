import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/")
    assert res.status_code == 200
    print("Health check passed:", res.json())

def test_products_list():
    res = client.get("/api/products")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert len(data["items"]) > 0
    print(f"Products list passed: {len(data['items'])} items found.")

def test_customer_login():
    res = client.post("/api/auth/login", json={
        "username_or_email": "john.doe@example.com",
        "password": "customer123"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    print("Customer login passed. Token generated.")
    return token

def test_cart_and_order(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Get products
    prod_res = client.get("/api/products")
    first_prod_id = prod_res.json()["items"][0]["id"]
    
    # 2. Add to cart
    cart_res = client.post("/api/cart", json={"product_id": first_prod_id, "quantity": 1}, headers=headers)
    assert cart_res.status_code == 200
    print("Cart addition passed:", cart_res.json()["item_count"], "items in cart.")
    
    # 3. Place order
    order_payload = {
        "customer_name": "John Doe",
        "customer_email": "john.doe@example.com",
        "customer_phone": "+91 9988776655",
        "delivery_address": "402 Green Valley",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560034",
        "payment_method": "SIMULATED_ONLINE"
    }
    order_res = client.post("/api/orders", json=order_payload, headers=headers)
    assert order_res.status_code == 201
    order_data = order_res.json()
    print("Order placement passed. Order Number:", order_data["order_number"], "Status:", order_data["order_status"])

def test_admin_dashboard():
    # Admin login
    res = client.post("/api/auth/login", json={
        "username_or_email": "admin@marketplace.com",
        "password": "admin123"
    })
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    dash_res = client.get("/api/admin/dashboard", headers=headers)
    assert dash_res.status_code == 200
    data = dash_res.json()
    print("Admin dashboard passed. Total products:", data["total_products"], "Revenue:", data["total_revenue"])

if __name__ == "__main__":
    test_health()
    test_products_list()
    token = test_customer_login()
    test_cart_and_order(token)
    test_admin_dashboard()
    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
