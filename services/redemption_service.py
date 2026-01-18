import csv
import os
from datetime import datetime
from services.household_service import households, save_households

def redeem_voucher(household_id, data):
    if not data:
        return {"error": "Invalid request body"}, 400

    required = ["merchant_id", "voucher_code", "denomination", "amount"]
    for field in required:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400

    if household_id not in households:
        return {"error": "Household not found"}, 404

    household = households[household_id]

    # ✅ Safe extraction + normalization
    voucher_code = data.get("voucher_code")
    denomination_raw = data.get("denomination")

    if not voucher_code or not denomination_raw:
        return {"error": "Voucher selection missing"}, 400

    tranche = str(voucher_code).strip()
    denomination = str(denomination_raw).strip()
    amount = int(data["amount"])

    print("DEBUG tranche:", tranche)
    print("DEBUG available tranches:", household.vouchers.keys())

    # ✅ Validate voucher existence
    if tranche not in household.vouchers:
        return {"error": "Voucher tranche not found"}, 400
    
    household.vouchers[tranche] = {
    str(k): v for k, v in household.vouchers[tranche].items()
}

    if denomination not in household.vouchers[tranche]:
        return {"error": "Invalid denomination"}, 400

    if household.vouchers[tranche][denomination] < amount:
        return {"error": "Insufficient voucher balance"}, 400

    # ✅ Deduct balance
    household.vouchers[tranche][denomination] -= amount
    remaining = household.vouchers[tranche][denomination]

    # ✅ Persist to households.json
    save_households()

    # ✅ Generate transaction ID server-side
    transaction_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # ✅ CSV logging
    os.makedirs("storage/redemptions", exist_ok=True)
    now = datetime.now()
    filename = f"storage/redemptions/Redeem{now.strftime('%Y%m%d%H')}.csv"

    remark = "Final denomination used" if remaining == 0 else ""

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            transaction_id,
            household_id,
            data["merchant_id"],
            now.strftime("%Y%m%d%H%M%S"),
            tranche,
            denomination,
            amount,
            "Completed",
            remark
        ])

    return {
        "message": "Redemption successful",
        "transaction_id": transaction_id,
        "remaining_balance": household.vouchers
    }, 200
