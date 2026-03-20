"""
Shared pytest fixtures for FinSight AI backend tests.
"""
import sys
from pathlib import Path

# Ensure 'backend/' is on sys.path so relative imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """FastAPI TestClient — no auth."""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Register a test user and return the JWT token."""
    resp = client.post(
        "/api/analysis/auth/register",
        json={"email": "test@example.com", "password": "testpass123", "full_name": "Test User"},
    )
    # If already registered, login instead
    if resp.status_code == 409:
        resp = client.post(
            "/api/analysis/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
        )
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Authorization header dict."""
    return {"Authorization": f"Bearer {auth_token}"}
