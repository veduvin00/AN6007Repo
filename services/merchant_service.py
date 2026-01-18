import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MERCHANT_FILE = os.path.join(BASE_DIR, "..", "storage", "merchants.txt")

def register_merchant(data):
    if not data:
        return {"error": "Invalid JSON body"}, 400

    os.makedirs("storage", exist_ok=True)

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

    return {"message": "Merchant registered successfully"}, 201
