"""Authentication service - IMPLEMENTED."""

import hashlib
import os
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + key.hex()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        salt_hex, key_hex = hashed.split(':')
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', plain.encode('utf-8'), salt, 100000)
        return key == new_key
    except:
        return False


def create_user(db: Session, user_data: UserCreate):
    """Create a new user. Returns None if email exists."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        return None
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
