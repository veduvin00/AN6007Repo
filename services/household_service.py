import json
import os
from models.household import Household
from utils.id_generator import generate_household_id

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOUSEHOLD_FILE = os.path.join(BASE_DIR, "..", "storage", "households.json")

households = {}

def load_households():

    global households
    if not os.path.exists(HOUSEHOLD_FILE) or os.path.getsize(HOUSEHOLD_FILE) == 0:
        households.clear()
        return

    with open(HOUSEHOLD_FILE, "r") as f:
        data = json.load(f)
        households.clear()
        for hid, hdata in data.items():
            if "household_id" not in hdata:
                hdata["household_id"] = hid
            
            households[hid] = Household.from_dict(hdata)

def save_households():
    os.makedirs("storage", exist_ok=True)
    print("Saving households to:", os.path.abspath(HOUSEHOLD_FILE))
    with open(HOUSEHOLD_FILE, "w") as f:
        json_data = {hid: h.to_dict() for hid, h in households.items()}
        json.dump(json_data, f, indent=2)

def register_household(data):
    if not data or "members" not in data or "postal_code" not in data:
        return {"error": "Missing required fields"}, 400

    household_id = generate_household_id()
    while household_id in households:
        household_id = generate_household_id()

    new_household = Household(
        household_id = household_id,
        members = data["members"],
        postal_code = data["postal_code"]
    )

    households[household_id] = new_household
    save_households()

    claim_link = f"https://cdc-voucher-app.onrender.com/ui/claim/{household_id}"

    return {
        "message": "Household registered successfully",
        "household_id": household_id,
        "claim_link": claim_link
    }, 201

def get_redemption_balance(household_id):
    if household_id not in households:
        return {"error": "Household not found"}, 404

    household = households[household_id]

    return {
        "household_id": household_id,
        "total_balance": household.get_total_balance(),
        "vouchers": household.vouchers
    }, 200
