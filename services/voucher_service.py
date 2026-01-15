from services.household_service import households, save_households

TRANCHE_CONFIG = {
    "May2025": {2: 50, 5: 40, 10: 20},
    "Jan2026": {2: 30, 5: 20, 10: 14}
}

def claim_voucher(household_id, data):
    if household_id not in households:
        return {"error": "Household not found"}, 404

    if not data or "tranche" not in data:
        return {"error": "Missing field: tranche"}, 400

    tranche = data["tranche"]

    if tranche not in TRANCHE_CONFIG:
        return {"error": "Invalid tranche"}, 400

    if tranche in households[household_id]["vouchers"]:
        return {"error": "Tranche already claimed"}, 400

    households[household_id]["vouchers"][tranche] = TRANCHE_CONFIG[tranche]
    save_households()

    return {"message": "Voucher claimed", "tranche": tranche}, 200
