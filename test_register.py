import urllib.request
import json

# First, let's try registering a new user
url = 'http://localhost:8000/api/auth/register'
data = json.dumps({
    'email': 'qa_user@datapulse.com',
    'password': 'qapassword12',
    'full_name': 'Tob'
}).encode('utf-8')

req = urllib.request.Request(
    url,
    data=data,
    headers={'Content-Type': 'application/json', 'User-Agent': 'Python'},
    method='POST'
)

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    print("✓ Registration successful!")
    print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
except urllib.error.HTTPError as e:
    error_msg = e.read().decode()
    print(f"HTTP Error {e.code}:")
    print(error_msg)
except Exception as e:
    print(f"✗ Registration failed: {e}")
