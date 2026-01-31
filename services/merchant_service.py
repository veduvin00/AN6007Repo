import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ensure the path points to the storage folder
STORAGE_DIR = os.path.join(BASE_DIR, "..", "storage")
MERCHANT_FILE = os.path.join(STORAGE_DIR, "merchants.txt")

# 1. Define the merchants dictionary to fix ImportError
merchants = {}

def load_merchants():
    """Load merchants from the text file into the in-memory dictionary"""
    if not os.path.exists(MERCHANT_FILE):
        return
    
    with open(MERCHANT_FILE, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 1:
                mid = row[0]
                merchants[mid] = {
                    "merchant_id": mid,
                    "merchant_name": row[1],
                    "uen": row[2],
                    "status": row[9] if len(row) > 9 else "Active"
                }

def register_merchant(data):
    if not data:
        return {"error": "Invalid JSON body"}, 400

    os.makedirs(STORAGE_DIR, exist_ok=True)

    # Write to file (Persistence)
    with open(MERCHANT_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            data.get("merchant_id"),
            data.get("merchant_name"),
            data.get("uen"),
            data.get("bank_name"),
            data.get("bank_code"),
            data.get("branch_code"),
            data.get("account_number"),
            data.get("account_holder"),
            datetime.now().strftime("%Y-%m-%d"),
            "Active"
        ])
    
    # 2. Synchronously update the in-memory dictionary to ensure login works immediately
    mid = data.get("merchant_id")
    merchants[mid] = data
    
    return {"message": "Merchant registered successfully"}, 201

# Initialize loading
load_merchants()