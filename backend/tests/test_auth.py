"""Authentication tests - IMPLEMENTED."""



def test_register_success(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "new@example.com",
            "password": "Password123",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_weak_password_short(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "short@example.com",
            "password": "a1",
            "full_name": "Short Pass User",
        },
    )
    assert resp.status_code == 422
    assert "Password must be at least 8 characters long" in resp.text


def test_register_weak_password_no_letters(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "noletters@example.com",
            "password": "123456789",
            "full_name": "No Letters User",
        },
    )
    assert resp.status_code == 422
    assert "Password must contain at least one letter" in resp.text


def test_register_weak_password_no_numbers(client):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "nonumbers@example.com",
            "password": "passwordonly",
            "full_name": "No Numbers User",
        },
    )
    assert resp.status_code == 422
    assert "Password must contain at least one number" in resp.text


def test_login_success(client):
    # Register first
    client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "Password123",
            "full_name": "Login User",
        },
    )
    # Then login
    resp = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "Password123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "Password123",
            "full_name": "Wrong User",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "wrong@example.com", "password": "badpassword123"},
    )
    assert resp.status_code == 401
