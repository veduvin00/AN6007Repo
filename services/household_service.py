import csv
import json
import os
import random
import string
from models.household import Household

households = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "..", "storage")
HOUSEHOLD_FILE_JSON = os.path.join(STORAGE_DIR, "households.json")
HOUSEHOLD_FILE_CSV = os.path.join(STORAGE_DIR, "households.txt")

def load_households():
    global households
    households.clear()

    if os.path.exists(HOUSEHOLD_FILE_JSON):
        try:
            with open(HOUSEHOLD_FILE_JSON, "r") as f:
                data = json.load(f)
                for hid, h_data in data.items():
                    households[hid] = Household.from_dict(h_data)
        except Exception as e:
            print(f"Error loading JSON: {e}")

    if os.path.exists(HOUSEHOLD_FILE_CSV):
        try:
            with open(HOUSEHOLD_FILE_CSV, "r") as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and len(row) >= 3:
                        hid = row[0]
                        if hid not in households:
                            members = row[1].split(";")
                            postal = row[2]
                            households[hid] = Household(hid, members, postal)
        except Exception as e:
            print(f"Error loading CSV: {e}")

def save_households():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    
    data_to_save = {}
    for hid, obj in households.items():
        data_to_save[hid] = obj.to_dict()
        
    with open(HOUSEHOLD_FILE_JSON, "w") as f:
        json.dump(data_to_save, f, indent=2)

def register_household(data):
    hid = "H" + "".join(str(random.randint(0, 9)) for _ in range(11))

    new_household = Household(
        household_id=hid,
        members=data.get("members", []),
        postal_code=data.get("postal_code", "")
    )
    

    households[hid] = new_household
    
    save_households()
    
    return {
        "household_id": hid, 
        "message": "Success",
        "claim_link": f"/ui/claim/{hid}"
    }, 200

def get_redemption_balance(household_id):
    if household_id not in households:
        return {"error": "Household not found"}, 404
    
    
    return {
        "vouchers": households[household_id].vouchers
    }, 200

load_households()