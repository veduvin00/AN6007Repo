"""
Test Flask API Endpoints
Run this to check if all endpoints exist
"""
import requests

base_url = "http://localhost:8000"

print("Testing Flask API Endpoints")
print("=" * 50)

# Test 1: Health check
print("\n1. Testing /api/health")
try:
    r = requests.get(f"{base_url}/api/health")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Get merchant (should return 404 for non-existent)
print("\n2. Testing /api/merchants/M999")
try:
    r = requests.get(f"{base_url}/api/merchants/M999")
    print(f"   Status: {r.status_code}")
    if r.headers.get('content-type') == 'application/json':
        print(f"   Response: {r.json()}")
    else:
        print(f"   ❌ Not JSON! Got: {r.text[:100]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Get merchant (existing)
print("\n3. Testing /api/merchants/M001")
try:
    r = requests.get(f"{base_url}/api/merchants/M001")
    print(f"   Status: {r.status_code}")
    if r.headers.get('content-type') == 'application/json':
        print(f"   Response: {r.json()}")
    else:
        print(f"   ❌ Not JSON! Got: {r.text[:100]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Get household balance
print("\n4. Testing /api/households/H45942386245/balance")
try:
    r = requests.get(f"{base_url}/api/households/H45942386245/balance")
    print(f"   Status: {r.status_code}")
    if r.headers.get('content-type') == 'application/json':
        print(f"   Response: {r.json()}")
    else:
        print(f"   ❌ Not JSON! Got: {r.text[:100]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("\nIf you see 'Not JSON!', your Flask app has errors.")
print("Check your Flask terminal for the actual error message!")