import csv
import json
import os
from datetime import datetime

# Get the project root directory (parent of services folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This is the services folder
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Go up one level to project root

# Storage is at the same level as services
STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage")
MERCHANT_FILE_TXT = os.path.join(STORAGE_DIR, "merchants.txt")
MERCHANT_FILE_JSON = os.path.join(STORAGE_DIR, "merchants.json")

print(f"[INIT] Looking for merchants at: {STORAGE_DIR}")

# Merchants dictionary
merchants = {}

def load_merchants():
    """Load merchants from text or JSON file"""
    global merchants
    merchants.clear()
    
    # Try JSON first
    if os.path.exists(MERCHANT_FILE_JSON):
        try:
            with open(MERCHANT_FILE_JSON, "r") as f:
                data = json.load(f)
                merchants.update(data)
            print(f"✅ Loaded {len(merchants)} merchants from JSON")
            return
        except Exception as e:
            print(f"⚠️ Error loading JSON: {e}")
    
    # Fallback to text file
    if os.path.exists(MERCHANT_FILE_TXT):
        try:
            with open(MERCHANT_FILE_TXT, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3:
                        mid = row[0]
                        merchants[mid] = {
                            "merchant_id": mid,
                            "merchant_name": row[1] if len(row) > 1 else "",
                            "uen": row[2] if len(row) > 2 else "",
                            "bank_name": row[3] if len(row) > 3 else "",
                            "bank_code": row[4] if len(row) > 4 else "",
                            "branch_code": row[5] if len(row) > 5 else "",
                            "account_number": row[6] if len(row) > 6 else "",
                            "account_holder": row[7] if len(row) > 7 else "",
                            "registration_date": row[8] if len(row) > 8 else "",
                            "status": row[9] if len(row) > 9 else "Active"
                        }
            print(f"✅ Loaded {len(merchants)} merchants from TXT")
        except Exception as e:
            print(f"⚠️ Error loading TXT: {e}")

def save_merchants():
    """Save merchants to both JSON and TXT"""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    # Save as JSON
    try:
        with open(MERCHANT_FILE_JSON, "w") as f:
            json.dump(merchants, f, indent=2)
        print(f"✅ Saved {len(merchants)} merchants to JSON")
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
    
    # Save as TXT (CSV format)
    try:
        with open(MERCHANT_FILE_TXT, "w", newline="") as f:
            writer = csv.writer(f)
            for mid, data in merchants.items():
                writer.writerow([
                    data.get("merchant_id", mid),
                    data.get("merchant_name", ""),
                    data.get("uen", ""),
                    data.get("bank_name", ""),
                    data.get("bank_code", ""),
                    data.get("branch_code", ""),
                    data.get("account_number", ""),
                    data.get("account_holder", ""),
                    data.get("registration_date", datetime.now().strftime("%Y-%m-%d")),
                    data.get("status", "Active")
                ])
        print(f"✅ Saved {len(merchants)} merchants to TXT")
    except Exception as e:
        print(f"❌ Error saving TXT: {e}")

def register_merchant(data):
    """Register a new merchant"""
    if not data:
        return {"error": "Invalid data"}, 400
    
    mid = data.get("merchant_id")
    if not mid:
        return {"error": "Merchant ID required"}, 400
    
    if mid in merchants:
        return {"error": "Merchant ID already exists"}, 400
    
    # Add registration date if not provided
    if "registration_date" not in data:
        data["registration_date"] = datetime.now().strftime("%Y-%m-%d")
    
    if "status" not in data:
        data["status"] = "Active"
    
    # Save to dictionary
    merchants[mid] = data
    
    # Persist to files
    save_merchants()
    
    return {"message": "Merchant registered successfully", "merchant_id": mid}, 201

# Initialize on import
load_merchants()