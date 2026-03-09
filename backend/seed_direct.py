#!/usr/bin/env python3
"""
Direct database seeding - inserts user with pre-hashed password
"""
import sys
import os
import psycopg2
from psycopg2.extras import execute_values

# Database connection parameters - must match your docker-compose env
DB_HOST = os.getenv('DB_HOST', 'db')
DB_USER = os.getenv('DB_USER', 'datapulse')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'datapulse')
DB_NAME = os.getenv('DB_NAME', 'datapulse')
DB_PORT = os.getenv('DB_PORT', '5432')

def seed_user():
    """Insert user directly into database"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = %s", ("qa_user@datapulse.com",))
        if cursor.fetchone():
            print("✓ User already exists")
            cursor.close()
            conn.close()
            return
        
        # Use bcrypt to hash the password properly
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_pwd = pwd_context.hash("qapassword12")
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (email, hashed_password, full_name, is_active, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, ("qa_user@datapulse.com", hashed_pwd, "Tob", True))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ User created successfully!")
        print("  Email: qa_user@datapulse.com")
        print("  Name: Tob")
        print("  Password: qapassword12")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_user()
