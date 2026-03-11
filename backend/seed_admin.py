import os
import sys

# Add the backend folder to sys.path so we can import the 'app' module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bcrypt
from app.config import settings
from app.database import SessionLocal
from app.models.user import User


def seed_admin():
    db = SessionLocal()
    try:
        email = settings.ADMIN_EMAIL
        password = settings.ADMIN_PASSWORD
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

        existing_admin = db.query(User).filter(User.email == email).first()
        if existing_admin:
            print(f"Admin user '{email}' already exists.")
            return

        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name="System Admin",
            is_active=True,
            is_admin=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Admin user '{email}' successfully seeded with password '{password}'.")
    except Exception as e:
        db.rollback()
        print(f"Failed to seed admin: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
