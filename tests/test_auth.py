def test_register_missing_password_returns_400(client):
    """
    If the client does not provide both email and password,
    /auth/register should return 400 with an error message.
    """
    # Missing password
    resp = client.post("/auth/register", json={"email": "test@example.com"})
    assert resp.status_code == 400

    data = resp.get_json()
    assert data is not None
    # Matches the exact message in auth.register()
    assert data["error"] == "Email and password required for registration"


def test_register_duplicate_email_returns_409(client):
    """
    Registering twice with the same email should fail with 409.
    """
    payload = {
        "email": "dupe@example.com",
        "password": "Password123!",
        "phone_number": "1234567890",
    }

    # First registration should succeed
    resp1 = client.post("/auth/register", json=payload)
    assert resp1.status_code == 201

    # Second registration with same email should fail
    resp2 = client.post("/auth/register", json=payload)
    assert resp2.status_code == 409

    data2 = resp2.get_json()
    assert data2 is not None
    assert data2["error"] == "Email already exists"


def test_login_wrong_password_returns_401(client):
    """
    If the password is wrong, /auth/login should return 401 with 'bad credentials'.
    """
    # First create a valid user via the real register endpoint
    register_payload = {
        "email": "loginuser@example.com",
        "password": "CorrectPassword1!",
        "phone_number": "5555555555",
    }
    reg_resp = client.post("/auth/register", json=register_payload)
    assert reg_resp.status_code == 201

    # Now try to log in with wrong password
    login_payload = {
        "email": "loginuser@example.com",
        "password": "WrongPassword!",
    }
    resp = client.post("/auth/login", json=login_payload)
    assert resp.status_code == 401

    data = resp.get_json()
    assert data is not None
    assert data["error"] == "bad credentials"


def test_login_success_returns_access_token(client):
    """
    Successful login should return a 200 and an access_token string.
    """
    # Create user via register
    register_payload = {
        "email": "success@example.com",
        "password": "MyStrongPass123!",
        "phone_number": "1112223333",
    }
    reg_resp = client.post("/auth/register", json=register_payload)
    assert reg_resp.status_code == 201

    # Login with correct credentials
    login_payload = {
        "email": "success@example.com",
        "password": "MyStrongPass123!",
    }
    resp = client.post("/auth/login", json=login_payload)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data is not None
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert data["access_token"]  # not empty
