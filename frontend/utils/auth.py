from utils.jwt_handler import login, register, clear_token


def authenticate_user(email: str, password: str) -> dict:
    """Wrapper used by login page. Returns {'ok': bool, 'error': str|None}."""
    return login(email, password)


def register_user(email: str, password: str, full_name: str = "") -> dict:
    return register(email, password, full_name)


def logout():
    clear_token()