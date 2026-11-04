"""
User Authentication & Persistence Service Module
Provides secure password hashing, email normalization, and user management
using PostgreSQL (with SQLite fallback) via SQLAlchemy.
"""

import os
import hmac
import hashlib
import secrets
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from database.connection import engine, SessionLocal, Base
from database.models.user import User


def init_user_table():
    """Ensures the users table exists and seeds the default demo account."""
    User.__table__.create(bind=engine, checkfirst=True)
    seed_demo_user_if_missing()


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a random salt.
    Format: pbkdf2_sha256$100000$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2_sha256$100000${salt.hex()}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a password against the stored PBKDF2-HMAC-SHA256 hash using constant-time comparison.
    """
    try:
        parts = password_hash.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])
        computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(expected_hash, computed_hash)
    except Exception:
        return False


def normalize_email(email: str) -> str:
    """Consistently normalizes email addresses by trimming whitespace and lowercasing."""
    if not email:
        return ""
    return email.strip().lower()


def seed_demo_user_if_missing():
    """Seeds the demo user (demo@example.com / Demo@123) if not present."""
    db: Session = SessionLocal()
    try:
        norm_email = normalize_email("demo@example.com")
        existing = db.query(User).filter(User.email == norm_email).first()
        if not existing:
            demo_user = User(
                email=norm_email,
                password_hash=hash_password("Demo@123"),
                full_name="Demo User",
            )
            db.add(demo_user)
            db.commit()
    except Exception as exc:
        db.rollback()
        print(f"[AUTH SEED NOTICE] Could not seed demo user: {exc}")
    finally:
        db.close()


def register_user(full_name: str, email: str, password: str) -> Dict[str, Any]:
    """
    Registers a new user in the database.
    Email is normalized (trimmed and lowercased).
    Password is never altered prior to hashing.
    """
    norm_email = normalize_email(email)
    if not norm_email or "@" not in norm_email:
        return {"success": False, "message": "Please enter a valid email address.", "status_code": 400}

    if not password or len(password) < 8:
        return {"success": False, "message": "Password must be at least 8 characters.", "status_code": 400}

    if not full_name or not full_name.strip():
        return {"success": False, "message": "Full name is required.", "status_code": 400}

    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == norm_email).first()
        if existing:
            return {
                "success": False,
                "message": "An account with this email address already exists.",
                "status_code": 409,
            }

        new_user = User(
            email=norm_email,
            password_hash=hash_password(password),
            full_name=full_name.strip(),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "success": True,
            "message": "Account created successfully! Please sign in.",
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "name": new_user.full_name,
            },
            "status_code": 201,
        }
    except Exception as exc:
        db.rollback()
        return {"success": False, "message": f"Database error during registration: {str(exc)}", "status_code": 500}
    finally:
        db.close()


def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticates a user by email and password.
    Email is normalized (trimmed and lowercased).
    Password verification uses constant-time hash comparison.
    """
    norm_email = normalize_email(email)
    if not norm_email or not password:
        return {"success": False, "message": "Invalid email or password.", "status_code": 401}

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == norm_email).first()
        if not user or not verify_password(password, user.password_hash):
            return {"success": False, "message": "Invalid email or password.", "status_code": 401}

        # Generate a secure session token
        token = secrets.token_hex(24)

        return {
            "success": True,
            "message": "Login successful!",
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
            },
            "status_code": 200,
        }
    except Exception as exc:
        return {"success": False, "message": f"Database error during authentication: {str(exc)}", "status_code": 500}
    finally:
        db.close()
