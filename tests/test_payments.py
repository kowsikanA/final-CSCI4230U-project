from uuid import uuid4
import stripe


# -------------------------------------------------
# Helper: register + login to get JWT headers
# -------------------------------------------------
def register_and_login(client):
    email = f"user_{uuid4().hex}@example.com"
    password = "Password123!"

    # Register
    resp = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "phone_number": "1234567890",
            "security_question": "What is the name of your first pet?",
            "security_answer": "Billy",
        },
    )
    assert resp.status_code == 201

    # Login
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    token = resp.get_json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


# -------------------------------------------------
# POST /payments/checkout  (Stripe checkout session)
# -------------------------------------------------

def test_checkout_requires_jwt(client):
    """
    POST /payments/checkout without a token should return 401.
    (jwt_required() handles this.)
    """
    resp = client.post("/payments/checkout")
    assert resp.status_code == 401


def test_checkout_empty_cart_returns_400(client):
    """
    When the user's cart is empty, payment checkout should return:
      400 + {"error": "cart is empty"}
    """
    headers = register_and_login(client)

    resp = client.post("/payments/checkout", headers=headers)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["error"] == "cart is empty"


def test_checkout_success_creates_session_and_clears_cart(client, monkeypatch):
    """
    Happy path:
      - Create a product
      - Add it to cart
      - Mock Stripe Session.create
      - Call /payments/checkout
      - Check 200, checkout_url, order_id
      - Cart is cleared
      - Order exists and is retrievable
    """
    headers = register_and_login(client)

    # 1) Create a product
    resp = client.post(
        "/api/products",
        json={
            "name": "Apple MacBook Pro 14 Inch Space Grey",
            "price": 1999.99,
            "inventory": 24,
            "available": True,
            "image_url": "https://cdn.dummyjson.com/product-images/laptops/apple-macbook-pro-14-inch-space-grey/thumbnail.webp",
            "description": "The MacBook Pro 14 Inch in Space Grey is a powerful and sleek laptop.",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    product_id = resp.get_json()["id"]

    # 2) Add to cart
    resp = client.post(
        "/api/cart",
        json={"product_id": product_id, "quantity": 2},
        headers=headers,
    )
    assert resp.status_code == 201

    # 3) Monkeypatch Stripe session creation
    class DummySession:
        def __init__(self, url):
            self.url = url

    def fake_create(**kwargs):
        # we don't care about the exact kwargs here, just that it's called
        return DummySession(url="https://example.com/checkout-session")

    monkeypatch.setattr(stripe.checkout.Session, "create", fake_create)

    # 4) Call checkout
    resp = client.post("/payments/checkout", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    assert "checkout_url" in data
    assert data["checkout_url"] == "https://example.com/checkout-session"
    assert "order_id" in data
    order_id = data["order_id"]

    # 5) Cart should now be empty
    resp = client.get("/api/cart", headers=headers)
    assert resp.status_code == 200
    cart_items = resp.get_json()
    assert cart_items == []

    # 6) Order should exist and be retrievable
    resp = client.get(f"/api/orders/{order_id}", headers=headers)
    assert resp.status_code == 200
    order = resp.get_json()
    assert order["id"] == order_id
    # your Order model has payment_status="pending" when created
    if "payment_status" in order:
        assert order["payment_status"] in ("pending", "paid")


def test_checkout_stripe_error_returns_500(client, monkeypatch):
    """
    If Stripe raises an exception, the endpoint should return:
      500 + {"error": "Stripe error: <message>"}
    payment.py catches a generic Exception, so we simulate that.
    """
    headers = register_and_login(client)

    # Create a product
    resp = client.post(
        "/api/products",
        json={
            "name": "Test Item",
            "price": 10.0,
            "inventory": 5,
            "available": True,
            "image_url": "",
            "description": "Test product for Stripe error path",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    product_id = resp.get_json()["id"]

    # Add to cart
    resp = client.post(
        "/api/cart",
        json={"product_id": product_id, "quantity": 1},
        headers=headers,
    )
    assert resp.status_code == 201

    # Monkeypatch Stripe to raise a generic Exception
    def fake_create(**kwargs):
        raise Exception("Something went wrong with Stripe")

    monkeypatch.setattr(stripe.checkout.Session, "create", fake_create)

    resp = client.post("/payments/checkout", headers=headers)
    assert resp.status_code == 500

    data = resp.get_json()
    assert "error" in data
    assert "Stripe error:" in data["error"]
