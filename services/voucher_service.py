from services.household_service import households, save_households

def claim_voucher(household_id, data):
    if household_id not in households:
        return {"error": "Household not found"}, 404

    if not data or "tranche" not in data:
        return {"error": "Missing field: tranche"}, 400

    tranche = data["tranche"]
    household = households[household_id]
    success, message = household.claim_tranche(tranche)
    
    if not success:
        return {"error": message}, 400
    
    save_households()

    return {
        "message": "Voucher claimed", 
        "tranche": tranche,
        "household_id": household_id
    }, 200
