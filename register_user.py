import json
import time
import urllib.request

# Wait a moment for API to be fully ready
time.sleep(2)

# Register the user
url = "http://localhost:8000/api/auth/register"
data = json.dumps(
    {"email": "qa_user@datapulse.com", "password": "qapassword12", "full_name": "Tob"}
).encode("utf-8")

req = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json", "User-Agent": "Python"},
    method="POST",
)

try:
    response = urllib.request.urlopen(req, timeout=10)
    result = json.loads(response.read().decode())
    print("✅ User registered successfully!")
    print("📧 Email: qa_user@datapulse.com")
    print("👤 Name: Tob")
    print("🔐 Password: qapassword12")
    print(f"🎫 Token: {result.get('access_token', 'N/A')[:50]}...")
except urllib.error.HTTPError as e:
    error_msg = e.read().decode()
    print(f"HTTP Error {e.code}:")
    print(error_msg)
except Exception as e:
    print(f"❌ Error: {e}")
    print("Make sure the backend is running on http://localhost:8000")
