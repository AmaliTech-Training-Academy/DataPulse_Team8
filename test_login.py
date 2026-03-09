import urllib.request
import json

url = 'http://localhost:8000/api/auth/login'
data = json.dumps({
    'email': 'qa_user@datapulse.com',
    'password': 'qapassword12'
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
    print("✓ Login successful!")
    print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
except urllib.error.HTTPError as e:
    print(f"✗ HTTP Error: {e.code} - {e.read().decode()}")
except Exception as e:
    print(f"✗ Login failed: {e}")
