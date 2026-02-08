"""
Voucher Service - Fixed to work with dict-based households
"""
from services.household_service import households, save_households

def claim_voucher(household_id, data):
    """Claim vouchers for a household"""
    if household_id not in households:
        return {"error": "Household not found"}, 404
    
    if not data or "tranche" not in data:
        return {"error": "Missing field: tranche"}, 400
    
    tranche = data["tranche"]
    household = households[household_id]
    
    # Check if already claimed
    if tranche in household.get("vouchers", {}):
        return {"error": f"{tranche} already claimed"}, 400
    
    # Define voucher schemes
    schemes = {
        "Jan2026": {"2": 30, "5": 12, "10": 18},
        "May2025": {"2": 50, "5": 20, "10": 30}
    }
    
    if tranche not in schemes:
        return {"error": "Invalid tranche"}, 400
    
    # Add vouchers to household
    if "vouchers" not in household:
        household["vouchers"] = {}
    
    household["vouchers"][tranche] = schemes[tranche].copy()
    
    save_households()
    
    return {
        "message": "Voucher claimed successfully",
        "tranche": tranche,
        "household_id": household_id,
        "vouchers": schemes[tranche]
    }, 200