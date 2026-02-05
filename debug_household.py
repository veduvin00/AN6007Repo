"""
Test Token Generation
"""
import requests

print("Testing Token Generation API")
print("=" * 50)

# Test with a real household ID
household_id = "H45942386245"  # The one you tested
vouchers = {
    "2": 5,
    "5": 2
}

print(f"\nGenerating token for {household_id}")
print(f"Vouchers: {vouchers}")

try:
    response = requests.post(
        "http://localhost:8000/api/token/generate",
        json={
            "household_id": household_id,
            "vouchers": vouchers
        }
    )
    
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("\n✅ Token generation works!")
        print(f"Token: {response.json()['token']}")
    else:
        print("\n❌ Token generation failed!")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("=" * 50)