import json
import os
from utils.id_generator import generate_household_id

HOUSEHOLD_FILE = "storage/households.json"
households = {}

def load_households():
    global households

    if not os.path.exists(HOUSEHOLD_FILE):
        households = {}
        return

    if os.path.getsize(HOUSEHOLD_FILE) == 0:
        households = {}
        return

    with open(HOUSEHOLD_FILE, "r") as f:
        households = json.load(f)

def save_households():
    os.makedirs("storage", exist_ok=True)
    with open(HOUSEHOLD_FILE, "w") as f:
        json.dump(households, f, indent=2)

def register_household(data):
    if not data:
        return {"error": "Invalid JSON body"}, 400

    if "members" not in data or "postal_code" not in data:
        return {"error": "Missing required fields"}, 400

    household_id = generate_household_id()
    while household_id in households:
        household_id = generate_household_id()

    households[household_id] = {
        "members": data["members"],
        "postal_code": data["postal_code"],
        "vouchers": {}
    }

    save_households()

    return {
        "message": "Household registered successfully",
        "household_id": household_id
    }, 201

def get_redemption_balance(household_id):
    if household_id not in households:
        return {"error": "Household not found"}, 404

    return {
        "household_id": household_id,
        "balance": households[household_id]["vouchers"]
    }, 200
