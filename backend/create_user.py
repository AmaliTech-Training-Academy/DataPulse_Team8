#!/usr/bin/env python3
"""
Create user directly in database with proper bcrypt hash
"""
import sys
import os
import psycopg2
from passlib.context import CryptContext

# Database connection parameters
DB_HOST = 'db'
DB_USER = 'datapulse'
DB_PASSWORD = 'datapulse'
DB_NAME = 'datapulse'
DB_PORT = '5432'

def create_user():
    """Create user with proper bcrypt hash"""
    try:
        # Generate hash using passlib
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_pwd = pwd_context.hash("qapassword12")

        print(f"Generated hash: {hashed_pwd}")

        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        cursor = conn.cursor()

        # Delete if exists
        cursor.execute("DELETE FROM users WHERE email = %s", ("qa_user@datapulse.com",))

        # Insert user
        cursor.execute("""
            INSERT INTO users (email, hashed_password, full_name, is_active, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, ("qa_user@datapulse.com", hashed_pwd, "Tob", True))

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ User created successfully!")
        print("📧 Email: qa_user@datapulse.com")
        print("👤 Name: Tob")
        print("🔐 Password: qapassword12")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_user()
