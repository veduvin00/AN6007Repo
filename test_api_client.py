"""
Test API Client - Check if all methods exist
"""
import sys

print("Testing api_client...")
print("=" * 50)

try:
    from api_client import api_client
    print("✅ Successfully imported api_client")
except Exception as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# Check all methods exist
methods = [
    'register_household',
    'get_balance',
    'claim_vouchers',
    'generate_token',
    'get_transactions',
    'get_notifications',
    'mark_notification_read',
    'register_merchant',
    'redeem_token',
    'get_merchant',  # This is the one that's missing
    'check_connection'
]

print("\nChecking methods:")
print("-" * 50)

missing = []
for method in methods:
    if hasattr(api_client, method):
        print(f"✅ {method}")
    else:
        print(f"❌ {method} - MISSING!")
        missing.append(method)

print("=" * 50)

if missing:
    print(f"\n❌ Missing {len(missing)} method(s): {', '.join(missing)}")
    print("\nYou need to update your api_client.py file!")
    print("Copy the complete version from api_client.py (the one I created)")
else:
    print("\n✅ All methods present! api_client is complete.")

# Test connection
print("\nTesting Flask API connection...")
if api_client.check_connection():
    print("✅ Flask API is running at http://localhost:8000")
else:
    print("❌ Cannot connect to Flask API")
    print("   Make sure you're running: python app.py")