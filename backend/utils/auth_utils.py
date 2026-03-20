import hashlib
import os
import secrets
from typing import Optional


# ── Simple in-memory user store (swap with DB later) ──────────────────────
# Structure: { email: { "hashed_password": str, "id": str, "full_name": str } }
_USER_STORE: dict = {}


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Returns (hashed_password, salt)."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return hashed, salt


def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    hashed, _ = hash_password(plain_password, salt)
    return hashed == hashed_password


def create_user(email: str, password: str, full_name: Optional[str] = None) -> dict:
    """Register a new user. Raises ValueError if email already exists."""
    if email in _USER_STORE:
        raise ValueError("Email already registered")
    hashed, salt = hash_password(password)
    user_id = secrets.token_urlsafe(12)
    _USER_STORE[email] = {
        "id": user_id,
        "email": email,
        "full_name": full_name,
        "hashed_password": hashed,
        "salt": salt,
    }
    return {"id": user_id, "email": email, "full_name": full_name}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Returns user dict if credentials valid, else None."""
    # Demo login — disable in production with DISABLE_DEMO_LOGIN=1
    if not os.getenv("DISABLE_DEMO_LOGIN") and email == "1" and password == "1":
        return {"id": "demo-user", "email": "1", "full_name": "Demo User"}

    user = _USER_STORE.get(email)
    if not user:
        return None
    if verify_password(password, user["hashed_password"], user["salt"]):
        return {"id": user["id"], "email": user["email"], "full_name": user["full_name"]}
    return None