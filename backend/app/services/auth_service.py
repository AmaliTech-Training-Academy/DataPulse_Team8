"""Authentication service - IMPLEMENTED."""

import hashlib

import bcrypt
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserCreate


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if (
        hashed.startswith("$2b$")
        or hashed.startswith("$2y$")
        or hashed.startswith("$2a$")
    ):
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    # Fallback to legacy SHA-256
    legacy_hash = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    return legacy_hash == hashed


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

    # On-the-fly migration to bcrypt if using legacy hash
    if not (
        user.hashed_password.startswith("$2b$")
        or user.hashed_password.startswith("$2y$")
        or user.hashed_password.startswith("$2a$")
    ):
        user.hashed_password = hash_password(password)
        db.commit()

    return user
