from uuid import uuid4

# register and login since this is the account used to test add to cart
def register_and_login(client):
    email = f"user_{uuid4().hex}@example.com"
    password = "Password123!"

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

    # login
    resp = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


# GET /api/cart - empty
def test_list_cart_initially_empty(client):
    headers = register_and_login(client)

    resp = client.get("/api/cart", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert data == []


# POST /api/cart
def test_add_to_cart_missing_productId_400(client):
    headers = register_and_login(client)

    resp = client.post("/api/cart", json={}, headers=headers)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["error"] == "product_id required"


def test_add_to_cart_success_201(client):
    headers = register_and_login(client)

    resp = client.post(
        "/api/cart",
        json={
            "product_id": 121,
            "quantity": 2,
            "name": "iPhone 5s",
            "price": 199.99,
            "image_url": "https://cdn.dummyjson.com/product-images/groceries/cooking-oil/thumbnail.webp",
            "description": (
                "The iPhone 5s is a classic smartphone known for its compact design "
                "and advanced features during its release. While it's an older model, "
                "it still provides a reliable user experience."
            ),
        },
        headers=headers,
    )

    assert resp.status_code == 201
    cart_item = resp.get_json()
    assert cart_item["product_id"] == 121
    assert cart_item["quantity"] == 2
    assert "id" in cart_item


# GET /api/cart (with item)
def test_list_cart_contains_added_item(client):
    headers = register_and_login(client)

    # Add item
    resp = client.post(
        "/api/cart",
        json={
            "product_id": 121,
            "quantity": 2,
            "name": "iPhone 5s",
            "price": 199.99,
            "image_url": "https://cdn.dummyjson.com/product-images/groceries/cooking-oil/thumbnail.webp",
            "description": (
                "The iPhone 5s is a classic smartphone known for its compact design "
                "and advanced features during its release. While it's an older model, "
                "it still provides a reliable user experience."
            ),
        },
        headers=headers,
    )
    assert resp.status_code == 201
    cart_item = resp.get_json()
    cart_id = cart_item["id"]

    # List cart
    resp = client.get("/api/cart", headers=headers)
    assert resp.status_code == 200

    items = resp.get_json()
    assert isinstance(items, list)
    assert any(i["id"] == cart_id for i in items)


# PUT /api/cart/<id>
def test_update_cart_invalid_quantity_400(client):
    headers = register_and_login(client)

    # Add item
    resp = client.post(
        "/api/cart",
        json={
            "product_id": 122,
            "quantity": 1,
            "name": "iPhone 6",
            "price": 299.99,
            "image_url": "https://cdn.dummyjson.com/product-images/smartphones/iphone-6/thumbnail.webp",
            "description": (
                "The iPhone 6 is a stylish and capable smartphone with a larger "
                "display and improved performance."
            ),
        },
        headers=headers,
    )
    assert resp.status_code == 201
    cart_id = resp.get_json()["id"]

    # Update quantity to invalid value
    resp = client.put(
        f"/api/cart/{cart_id}",
        json={"quantity": 0},
        headers=headers,
    )
    assert resp.status_code == 400

    data = resp.get_json()
    assert data["error"] == "quantity must be > 0"


def test_update_cart_success_200(client):
    headers = register_and_login(client)

    # Add item
    resp = client.post(
        "/api/cart",
        json={
            "product_id": 122,
            "quantity": 1,
            "name": "iPhone 6",
            "price": 299.99,
            "image_url": "https://cdn.dummyjson.com/product-images/smartphones/iphone-6/thumbnail.webp",
            "description": (
                "The iPhone 6 is a stylish and capable smartphone with a larger "
                "display and improved performance."
            ),
        },
        headers=headers,
    )
    assert resp.status_code == 201
    cart_id = resp.get_json()["id"]

    # Update quantity to 5 (valid)
    resp = client.put(
        f"/api/cart/{cart_id}",
        json={"quantity": 5},
        headers=headers,
    )
    assert resp.status_code == 200

    updated = resp.get_json()
    assert updated["id"] == cart_id
    assert updated["quantity"] == 5


# DELETE /api/cart/<id>
def test_delete_cart_success_200(client):
    headers = register_and_login(client)

    # Add item
    resp = client.post(
        "/api/cart",
        json={
            "product_id": 122,
            "quantity": 1,
            "name": "iPhone 6",
            "price": 299.99,
            "image_url": "https://cdn.dummyjson.com/product-images/smartphones/iphone-6/thumbnail.webp",
            "description": (
                "The iPhone 6 is a stylish and capable smartphone with a larger "
                "display and improved performance."
            ),
        },
        headers=headers,
    )
    assert resp.status_code == 201
    cart_id = resp.get_json()["id"]

    # Delete the item
    resp = client.delete(f"/api/cart/{cart_id}", headers=headers)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["message"] == "deleted"

    # Ensure it no longer appears in cart
    resp = client.get("/api/cart", headers=headers)
    assert resp.status_code == 200
    items = resp.get_json()
    assert all(i["id"] != cart_id for i in items)
