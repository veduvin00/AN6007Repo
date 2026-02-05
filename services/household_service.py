import csv
import json
import os
import random
import string

households = {}

# Get the project root directory (parent of services folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This is the services folder
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Go up one level to project root

# Storage is at the same level as services
STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage")
HOUSEHOLD_FILE_JSON = os.path.join(STORAGE_DIR, "households.json")
HOUSEHOLD_FILE_CSV = os.path.join(STORAGE_DIR, "households.txt")

print(f"[INIT] Looking for households.json at: {HOUSEHOLD_FILE_JSON}")

def load_households():
    global households
    households.clear()

    if os.path.exists(HOUSEHOLD_FILE_JSON):
        try:
            with open(HOUSEHOLD_FILE_JSON, "r") as f:
                data = json.load(f)
                # Load as dictionaries directly
                for hid, h_data in data.items():
                    households[hid] = h_data
            print(f"✅ Loaded {len(households)} households from {HOUSEHOLD_FILE_JSON}")
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
    else:
        print(f"⚠️ households.json not found at {HOUSEHOLD_FILE_JSON}")

    if os.path.exists(HOUSEHOLD_FILE_CSV):
        try:
            with open(HOUSEHOLD_FILE_CSV, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 3:
                        hid = row[0]
                        if hid not in households:
                            members = row[1].split(";")
                            postal = row[2]
                            households[hid] = {
                                "household_id": hid,
                                "members": members,
                                "postal_code": postal,
                                "vouchers": {}
                            }
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")

def save_households():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    try:
        with open(HOUSEHOLD_FILE_JSON, "w") as f:
            json.dump(households, f, indent=2)
        print(f"✅ Saved {len(households)} households to {HOUSEHOLD_FILE_JSON}")
    except Exception as e:
        print(f"❌ Error saving households: {e}")

def register_household(data):
    # Generate unique household ID with collision check
    max_attempts = 100
    for attempt in range(max_attempts):
        hid = "H" + "".join(str(random.randint(0, 9)) for _ in range(11))
        if hid not in households:
            break
    else:
        # If we couldn't find a unique ID after max_attempts, use timestamp
        import time
        hid = f"H{int(time.time() * 1000) % 100000000000:011d}"
    
    print(f"🆔 Generated unique household ID: {hid}")

    new_household = {
        "household_id": hid,
        "members": data.get("members", []),
        "postal_code": data.get("postal_code", ""),
        "vouchers": {}
    }
    
    households[hid] = new_household
    save_households()
    
    return {
        "household_id": hid, 
        "message": "Success",
        "claim_link": f"/ui/claim/{hid}"
    }, 200

def get_redemption_balance(household_id):
    if household_id not in households:
        return {"error": "Household not found"}, 404
    
    household = households[household_id]
    
    # Return the vouchers structure
    return {
        "household_id": household_id,
        "vouchers": household.get("vouchers", {})
    }, 200

# Initialize on import
load_households()