#!/usr/bin/env python3
"""
Create user with new hash method
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from app.services.auth_service import hash_password

# Generate hash
hashed_pwd = hash_password("qapassword12")
print(f"Generated hash: {hashed_pwd}")

# Database connection
conn = psycopg2.connect(
    host="db",
    user="datapulse",
    password="datapulse",
    database="datapulse",
    port="5432"
)
cursor = conn.cursor()

# Delete existing user
cursor.execute("DELETE FROM users WHERE email = %s", ("qa_user@datapulse.com",))

# Insert new user
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