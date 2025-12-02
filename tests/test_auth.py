#-----------------
# Register Tests
#-----------------

# Test ensures that missing credentials are handled 
def test_register_missing_password_returns_400(client):
    
    # Missing password
    resp = client.post("/auth/register", json={"email": "test@example.com", "security_question": "What is the name of your first pet?", "security_answer": "Fluffy"})
    assert resp.status_code == 400

    data = resp.get_json()
    assert data is not None
    # Matches the exact message in auth.register()
    assert data["error"] == "Email and password required for registration"


# Test ensures duplicate credentials are rejected
def test_register_duplicate_email_returns_409(client):
    payload = {
        "email": "dupe@example.com",
        "password": "Password123!",
        "phone_number": "1234567890",
        "security_question": "What is the name of your first pet?", 
        "security_answer": "Fluffy"    
    }

    # First registration should succeed
    resp1 = client.post("/auth/register", json=payload)
    assert resp1.status_code == 201

    # Second registration with same email fails 
    resp2 = client.post("/auth/register", json=payload)
    assert resp2.status_code == 409

    data2 = resp2.get_json()
    assert data2 is not None
    assert data2["error"] == "Email already exists"



#-----------------
# Login Tests
#-----------------

def test_login_missing_credentials_return_400(client):
    res = client.post("/auth/login", json={})
    assert res.status_code == 400

    data = res.get_json()
    assert data is not None
    assert data["error"] == "username and password required"

# Test handles wrong credentials
def test_login_wrong_password_returns_401(client):

    # Creates a user 
    register_payload = {
        "email": "loginuser@example.com",
        "password": "CorrectPassword1!",
        "phone_number": "5555555555",
        "security_question": "What is the name of your first pet?", 
        "security_answer": "Fluffy"  
    }
    reg_resp = client.post("/auth/register", json=register_payload)
    assert reg_resp.status_code == 201

    # Logging in with bad credentials
    login_payload = {
        "email": "loginuser@example.com",
        "password": "WrongPassword!",
    }
    resp = client.post("/auth/login", json=login_payload)
    assert resp.status_code == 401

    data = resp.get_json()
    assert data is not None
    assert data["error"] == "bad credentials"


# Ensures correct login works correctly 
def test_login_success_returns_access_token(client):
    # Create user via register
    register_payload = {
        "email": "success@example.com",
        "password": "MyStrongPass123!",
        "phone_number": "1112223333",
        "security_question": "In what city were you born?", 
        "security_answer": "Oshawa"  
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
    assert data["access_token"]  


#-----------------
# Forgot Password Tests
#-----------------

def test_forgot_password_missing_fields_returns_400(client):
    # Missing some fields should hit "Please fill in all fields."
    resp = client.post("/auth/forgot-password", json={ "email": "some@example.com", "security_answer": "whatever",},)
    assert resp.status_code == 400

    data = resp.get_json()
    assert data is not None
    assert data["error"] == "Please fill in all fields."


def test_forgot_password_password_mismatch_returns_400(client):
    # First create a valid user
    client.post( "/auth/register",json={
            "email": "mismatch@example.com",
            "password": "OldPass123!",
            "phone_number": "1231231234",
            "security_question": "What is the name of your first pet?",
            "security_answer": "Fluffy",
        },
    )

    # Now send forgot-password with mismatched passwords
    resp = client.post(
        "/auth/forgot-password",
        json={
            "email": "mismatch@example.com",
            "security_answer": "Fluffy",
            "new_password": "NewPass123!",
            "confirm_password": "DifferentPass!",
        },
    )
    assert resp.status_code == 400

    data = resp.get_json()
    assert data is not None
    assert data["error"] == "Passwords do not match."


def test_forgot_password_no_such_email_returns_404(client):
    resp = client.post(
        "/auth/forgot-password",
        json={
            "email": "doesnotexist@example.com",
            "security_answer": "Anything",
            "new_password": "SomePass123!",
            "confirm_password": "SomePass123!",
        },
    )
    assert resp.status_code == 404

    data = resp.get_json()
    assert data is not None
    assert data["error"] == "No account found with that email."


def test_forgot_password_wrong_security_answer_returns_401(client):
    client.post(
        "/auth/register",
        json={
            "email": "secq@example.com",
            "password": "OriginalPass123!",
            "phone_number": "9999999999",
            "security_question": "What is the name of your first pet?",
            "security_answer": "CorrectAnswer",
        },
    )

    # Forgot password with incorrect security answer
    resp = client.post(
        "/auth/forgot-password",
        json={
            "email": "secq@example.com",
            "security_answer": "WrongAnswer",
            "new_password": "NewPass123!",
            "confirm_password": "NewPass123!",
        },
    )
    assert resp.status_code == 401

    data = resp.get_json()
    assert data is not None
    assert data["error"] == "Security answer is incorrect."


def test_forgot_password_success_allows_login_with_new_password(client):
    # Create a user
    client.post(
        "/auth/register",
        json={
            "email": "reset@example.com",
            "password": "OldPass123!",
            "phone_number": "7777777777",
            "security_question": "What is the name of your first pet?",
            "security_answer": "Fluffy",
        },
    )

    # Reset password with correct info
    resp = client.post(
        "/auth/forgot-password",
        json={
            "email": "reset@example.com",
            "security_answer": "Fluffy",
            "new_password": "BrandNewPass123!",
            "confirm_password": "BrandNewPass123!",
        },
    )
    assert resp.status_code == 200

    data = resp.get_json()
    assert data is not None
    assert data["message"] == "Password updated. You can now log in."

    # Login should now work with the new password
    login_resp = client.post(
        "/auth/login", json={"email": "reset@example.com", "password": "BrandNewPass123!", },
    )
    assert login_resp.status_code == 200
    login_data = login_resp.get_json()
    assert login_data is not None
    assert "access_token" in login_data
    assert isinstance(login_data["access_token"], str)
    assert login_data["access_token"]