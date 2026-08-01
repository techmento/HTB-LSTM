"""Password hashing, login/logout, and the auth dependency used to protect routes.

Uses only the Python standard library (hashlib + secrets + hmac) — salted
SHA-256 for password storage and a random URL-safe token for sessions. This
is a reasonable, dependency-free level of security for a university project
demo; a production system would use a stronger KDF such as bcrypt/argon2.
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone

from fastapi import Header, HTTPException

from app import db

# Default admin account seeded on first run if no users exist yet.
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = os.environ.get("DASHBOARD_ADMIN_PASSWORD", "admin123")


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Returns (hash, salt). Generates a new random salt if one isn't given."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return digest, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    digest, _ = hash_password(password, salt)
    return hmac.compare_digest(digest, expected_hash)


def seed_default_admin():
    """Creates the default admin account the first time the app runs."""
    if db.count_users() == 0:
        password_hash, salt = hash_password(DEFAULT_ADMIN_PASSWORD)
        db.create_user(DEFAULT_ADMIN_USERNAME, password_hash, salt)


def login(username: str, password: str) -> str:
    """Verifies credentials and returns a new session token, or raises ValueError."""
    user = db.get_user_by_username(username)
    if not user or not verify_password(password, user["salt"], user["password_hash"]):
        raise ValueError("Invalid username or password")

    token = secrets.token_urlsafe(32)
    db.create_session(token, user["id"], datetime.now(timezone.utc).isoformat())
    return token


def logout(token: str):
    db.delete_session(token)


def get_current_user(authorization: str = Header(default=None)):
    """FastAPI dependency: requires a valid 'Authorization: Bearer <token>' header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.removeprefix("Bearer ")
    session = db.get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return session
