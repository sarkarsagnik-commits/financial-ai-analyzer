"""
Frontend JWT handler — manages token storage and injects
Authorization headers for API calls made from Streamlit.
"""
import streamlit as st
from datetime import datetime
import requests
from config import API_BASE_URL


def save_token(token: str):
    st.session_state["jwt_token"] = token
    st.session_state["token_saved_at"] = datetime.utcnow().isoformat()


def get_token():
    return st.session_state.get("jwt_token")


def clear_token():
    st.session_state.pop("jwt_token", None)
    st.session_state.pop("token_saved_at", None)
    st.session_state["authenticated"] = False


def get_auth_headers() -> dict:
    token = get_token()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def login(email: str, password: str) -> dict:
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/analysis/auth/login",
            json={"email": email, "password": password},
            timeout=10,
        )
        if resp.status_code == 200:
            save_token(resp.json()["access_token"])
            return {"ok": True, "error": None}
        return {"ok": False, "error": resp.json().get("detail", "Login failed")}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "Cannot connect to backend. Is FastAPI running on port 8000?"}


def register(email: str, password: str, full_name: str = "") -> dict:
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/analysis/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
            timeout=10,
        )
        if resp.status_code == 200:
            save_token(resp.json()["access_token"])
            return {"ok": True, "error": None}
        return {"ok": False, "error": resp.json().get("detail", "Registration failed")}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "Cannot connect to backend."}