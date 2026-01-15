import csv
import os
from datetime import datetime

def redeem_voucher(household_id, data):
    if not data:
        return {"error": "Invalid JSON body"}, 400

    required = ["transaction_id", "merchant_id", "voucher_code", "denomination", "amount"]
    for field in required:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400

    os.makedirs("storage/redemptions", exist_ok=True)
    now = datetime.now()
    filename = f"storage/redemptions/Redeem{now.strftime('%Y%m%d%H')}.csv"

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            data["transaction_id"],
            household_id,
            data["merchant_id"],
            now.strftime("%Y%m%d%H%M%S"),
            data["voucher_code"],
            data["denomination"],
            data["amount"],
            "Completed",
            "Final denomination used"
        ])

    return {"message": "Redemption successful"}, 200
