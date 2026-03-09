#!/usr/bin/env python3
"""
Generate bcrypt hash inside container and insert user
"""
import bcrypt
import psycopg2

# Generate hash using bcrypt directly
password = b"qapassword12"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password, salt)

print(f"Generated hash: {hashed.decode()}")

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
""", ("qa_user@datapulse.com", hashed.decode(), "Tob", True))

conn.commit()
cursor.close()
conn.close()

print("✅ User created successfully!")
print("📧 Email: qa_user@datapulse.com")
print("👤 Name: Tob")
print("🔐 Password: qapassword12")