from uuid import uuid4
import products  # products.py module


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
# GET /api/products  (list products)
# -------------------------------------------------
def test_list_products_returns_list(client, monkeypatch):
    """
    GET /api/products should return a JSON list.
    We monkeypatch fetchApiProducts to avoid real DummyJSON HTTP calls.
    """
    monkeypatch.setattr(products, "fetchApiProducts", lambda: None)

    resp = client.get("/api/products")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)


# -------------------------------------------------
# POST /api/products  (create product)
# -------------------------------------------------
def test_create_product_requires_jwt(client):
    """
    POST /api/products without a token should return 401.
    """
    resp = client.post(
        "/api/products",
        json={
            "name": "Test Product",
            "price": 9.99,
        },
    )
    assert resp.status_code == 401  # missing Authorization header


def test_create_product_missing_name_or_price_returns_400(client):
    headers = register_and_login(client)

    # Missing name
    resp = client.post(
        "/api/products",
        json={"price": 9.99},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "name required"

    # Missing price
    resp = client.post(
        "/api/products",
        json={"name": "No Price"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "name required"


def test_create_product_invalid_inventory_returns_400(client):
    headers = register_and_login(client)

    resp = client.post(
        "/api/products",
        json={
            "name": "Bad Inventory",
            "price": 10.0,
            "inventory": "not-an-int",
            "image_url": "",
            "available": True,
            "description": "Test desc",
        },
        headers=headers,
    )
    assert resp.status_code == 400
    # matches products.py: "inventory should be an integer"
    assert resp.get_json()["error"] == "inventory should be an integer"


def test_create_product_success_returns_201(client):
    headers = register_and_login(client)

    resp = client.post(
        "/api/products",
        json={
            "name": "Huawei Matebook X Pro",
            "price": 1399.99,
            "inventory": 75,
            "image_url": "https://cdn.dummyjson.com/product-images/laptops/huawei-matebook-x-pro/thumbnail.webp",
            "available": True,
            "description": "The Huawei Matebook X Pro is a slim and stylish laptop with a high-resolution touchscreen display, offering a premium experience for users on the go.",
        },
        headers=headers,
    )
    assert resp.status_code == 201

    product = resp.get_json()
    assert product["name"] == "Olive Oil"
    assert product["price"] == 12.5
    assert product["inventory"] == 10
    assert product["available"] is True
    assert "id" in product


# -------------------------------------------------
# GET /api/products/<id>
# -------------------------------------------------
def test_get_product_requires_jwt(client):
    resp = client.get("/api/products/1")
    assert resp.status_code == 401  # missing JWT


def test_get_product_not_found_returns_404(client):
    headers = register_and_login(client)

    resp = client.get("/api/products/999999", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "product not found"


def test_get_product_success_returns_200(client):
    headers = register_and_login(client)

    # First create a product
    resp = client.post(
        "/api/products",
        json={
            "name": "Rice",
            "price": 5.99,
            "inventory": 50,
            "image_url": "",
            "available": True,
            "description": "Long grain rice",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    product_id = resp.get_json()["id"]

    # Now retrieve it
    resp = client.get(f"/api/products/{product_id}", headers=headers)
    assert resp.status_code == 200

    product = resp.get_json()
    assert product["id"] == product_id
    assert product["name"] == "Rice"
    assert product["price"] == 5.99


# -------------------------------------------------
# PUT /api/products/<id>  (update)
# -------------------------------------------------
def test_update_product_requires_jwt(client):
    resp = client.put(
        "/api/products/1",
        json={"name": "No Token Update"},
    )
    assert resp.status_code == 401  # missing JWT


def test_update_product_not_found_returns_404(client):
    headers = register_and_login(client)

    resp = client.put(
        "/api/products/999999",
        json={"name": "Does Not Exist"},
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not found"


def test_update_product_invalid_inventory_returns_400(client):
    headers = register_and_login(client)

    # Create a product
    resp = client.post(
        "/api/products",
        json={
            "name": "Sugar",
            "price": 3.5,
            "inventory": 15,
            "image_url": "",
            "available": True,
            "description": "White sugar",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    product_id = resp.get_json()["id"]

    # Update with invalid inventory
    resp = client.put(
        f"/api/products/{product_id}",
        json={"inventory": "invalid"},
        headers=headers,
    )
    assert resp.status_code == 400
    # matches products.py: "inventory should be integer"
    assert resp.get_json()["error"] == "inventory should be integer"


def test_update_product_success_returns_200(client):
    headers = register_and_login(client)

    # Create a product
    resp = client.post(
        "/api/products",
        json={
            "name": "Flour",
            "price": 4.0,
            "inventory": 20,
            "available": True,
            "image_url": "",
            "description": "All-purpose flour",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    product_id = resp.get_json()["id"]

    # Update several fields
    resp = client.put(
        f"/api/products/{product_id}",
        json={
            "name": "Flour Updated",
            "price": 5.5,
            "inventory": 40,
            "available": False,
            "description": "Updated flour description",
        },
        headers=headers,
    )
    assert resp.status_code == 200

    updated = resp.get_json()
    assert updated["id"] == product_id
    assert updated["name"] == "Flour Updated"
    assert updated["price"] == 5.5
    assert updated["inventory"] == 40
    assert updated["available"] is False
    assert updated["description"] == "Updated flour description"


# -------------------------------------------------
# DELETE /api/products/<id>  (delete)
# -------------------------------------------------
def test_delete_product_requires_jwt(client):
    resp = client.delete("/api/products/1")
    assert resp.status_code == 401  # missing JWT


def test_delete_product_not_found_returns_404(client):
    headers = register_and_login(client)

    resp = client.delete("/api/products/999999", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "not found"


def test_delete_product_success_returns_200(client):
    headers = register_and_login(client)

    # Create a product
    resp = client.post(
        "/api/products",
        json={
            "name": "Honey",
            "price": 9.99,
            "inventory": 5,
            "available": True,
            "image_url": "",
            "description": "Natural honey",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    product_id = resp.get_json()["id"]

    # Delete it
    resp = client.delete(f"/api/products/{product_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "deleted"

    # Confirm it no longer exists
    resp = client.get(f"/api/products/{product_id}", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "product not found"
