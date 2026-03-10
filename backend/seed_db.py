#!/usr/bin/env python3
"""
Database seeding script - creates tables and adds initial user
Run this from the backend directory: python seed_db.py
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.dataset import Dataset, DatasetFile
from app.models.rule import ValidationRule
from app.models.check_result import CheckResult, QualityScore
from app.services.auth_service import hash_password

def seed_database():
    """Create tables and seed initial user"""
    print("🌱 Seeding DataPulse database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
    
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing = db.query(User).filter(User.email == "qa_user@datapulse.com").first()
        if existing:
            print(f"✓ User already exists: {existing.email}")
            return
        
        # Create new user
        new_user = User(
            email="qa_user@datapulse.com",
            hashed_password=hash_password("qapassword12"),
            full_name="Tob",
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✓ User created successfully!")
        print(f"  Email: qa_user@datapulse.com")
        print(f"  Name: Tob")
        print(f"  Password: qapassword12")
        
    except Exception as e:
        print(f"✗ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
