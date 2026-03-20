"""Tests for authentication endpoints."""


def test_register_and_login(client):
    """Register a new user, then login with same credentials."""
    # Register
    resp = client.post(
        "/api/analysis/auth/register",
        json={"email": "auth_test@example.com", "password": "secure123", "full_name": "Auth Test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Login with same credentials
    resp = client.post(
        "/api/analysis/auth/login",
        json={"email": "auth_test@example.com", "password": "secure123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_invalid_credentials(client):
    resp = client.post(
        "/api/analysis/auth/login",
        json={"email": "wrong@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_register_duplicate(client):
    """Registering the same email twice returns 409."""
    payload = {"email": "dup@example.com", "password": "pass123"}
    client.post("/api/analysis/auth/register", json=payload)
    resp = client.post("/api/analysis/auth/register", json=payload)
    assert resp.status_code == 409


def test_demo_login(client):
    """Demo login with email='demo@example.com', password='demo123'."""
    resp = client.post(
        "/api/analysis/auth/login",
        json={"email": "demo@example.com", "password": "demo123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_protected_endpoint_no_token(client):
    """Accessing a protected endpoint without token returns 401."""
    resp = client.get("/api/analysis/documents")
    assert resp.status_code == 401
