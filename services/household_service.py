import json
import os
from models.household import Household
from utils.id_generator import generate_household_id

HOUSEHOLD_FILE = "storage/households.json"
households = {}

def load_households():

    global households
    if not os.path.exists(HOUSEHOLD_FILE) or os.path.getsize(HOUSEHOLD_FILE) == 0:
        households = {}
        return

    with open(HOUSEHOLD_FILE, "r") as f:
        data = json.load(f)
        households = {hid: Household.from_dict(hdata) for hid, hdata in data.items()}

def save_households():
    os.makedirs("storage", exist_ok=True)
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

    claim_link = f"http://127.0.0.1/api/households/{household_id}/claim"

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
