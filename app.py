# "AN6007 Group 13"
import csv
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, flash, url_for
from services.household_service import (
    register_household,
    get_redemption_balance,
    load_households,
    households,
    save_households
)
from services.voucher_service import claim_voucher
from services.redemption_service import redeem_voucher
from services.merchant_service import register_merchant, load_merchants, merchants
from services.notification_service import (
    create_redemption_notification,
    get_transaction_history,
    get_unread_notifications
)
import random
import string
import os
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "an6007_group13_secret_key"

load_households()
load_merchants()

print("=" * 60)
print("🚀 CDC VOUCHER API - Starting...")
print("=" * 60)
print(f"✅ Loaded {len(households)} households")
print(f"✅ Loaded {len(merchants)} merchants")
print("=" * 60)

@app.route("/")
def home():
    return render_template("home.html")

# ------------------------------
# LOGIN UI
# ------------------------------
@app.route("/ui/login", methods=["GET", "POST"])
def login_ui():
    if request.method == "POST":
        # Get input ID (login_id is for the new template, household_id is for compatibility)
        login_id = request.form.get("login_id", "").strip()
        if not login_id:
             login_id = request.form.get("household_id", "").strip()

        # 1. Check if it's a Household
        if login_id in households:
            return redirect(f"/ui/balance/{login_id}")
        
        # 2. Check if it's a Merchant (new logic)
        elif login_id in merchants:
            return redirect(f"/ui/merchant/{login_id}")
            
        else:
            flash("Invalid ID. Please check and try again.", "danger")
            
    return render_template("login.html")

# ------------------------------
# MERCHANT DASHBOARD UI (New)
# ------------------------------
@app.route("/ui/merchant/<merchant_id>", methods=["GET", "POST"])
def merchant_dashboard_ui(merchant_id):
    # 1. Security check
    if merchant_id not in merchants:
        return "Merchant not found", 404
    
    merchant = merchants[merchant_id]
    result = None
    
    # 2. Handle redemption logic
    if request.method == "POST":
        token = request.form.get("token", "").strip()
        
        # Find household corresponding to the token
        target_household = None
        token_data = None
        
        for hid, h in households.items():
            if h.get("active_token") == token:
                target_household = hid
                token_data = h.get("token_data")
                break
        
        if target_household and token_data:
            # Calculate total amount (Handle nested structure: {tranche: {denom: count}})
            total_amount = 0
            voucher_list_for_csv = []
            
            h_obj = households[target_household]
            
            # Deduct vouchers with strict tranche matching
            # token_data structure expected: { "Jan2026": { "10": 1 }, "May2025": { "2": 2 } }
            for tranche_name, vouchers in token_data.items():
                if tranche_name not in h_obj.get("vouchers", {}):
                    continue
                    
                for denom, count in vouchers.items():
                    denom = str(denom)
                    count = int(count)
                    total_amount += int(denom) * count
                    
                    # Prepare for CSV
                    for _ in range(count):
                        voucher_list_for_csv.append(int(denom))
                    
                    # Deduct logic
                    if denom in h_obj["vouchers"][tranche_name]:
                        current_val = h_obj["vouchers"][tranche_name][denom]
                        h_obj["vouchers"][tranche_name][denom] = max(0, current_val - count)

            # Sort for display consistency
            voucher_list_for_csv.sort()
            
            # Clear Token
            households[target_household]["active_token"] = None
            households[target_household]["token_data"] = None
            save_households()
            
            # ============================================================
            # CSV generation logic
            # ============================================================
            try:
                csv_dir = os.path.join("storage", "redemptions")
                os.makedirs(csv_dir, exist_ok=True)
                
                now = datetime.now()
                csv_filename = f"Redeem{now.strftime('%Y%m%d%H')}.csv"
                csv_path = os.path.join(csv_dir, csv_filename)
                file_exists = os.path.exists(csv_path)
                
                txn_id = f"TX{now.strftime('%Y%m%d%H%M%S')}"
                txn_time_str = now.strftime("%Y-%m-%d-%H%M%S")
                
                with open(csv_path, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow([
                            "Transaction_ID", "Household_ID", "Merchant_ID", 
                            "Transaction_Date_Time", "Voucher_Code", "Denomination_Used", 
                            "Amount_Redeemed", "Payment_Status", "Remarks"
                        ])
                    
                    total_items = len(voucher_list_for_csv)
                    for index, denom_val in enumerate(voucher_list_for_csv):
                        remark = "Final denomination used" if index == total_items - 1 else str(index + 1)
                        v_code = f"V{target_household[-4:]}{str(index+1).zfill(3)}"
                        
                        writer.writerow([
                            txn_id, target_household, merchant_id, txn_time_str,
                            v_code, f"${denom_val}.00", f"${total_amount}.00",
                            "Completed", remark
                        ])
                print(f"✅ CSV Logged from Web UI: {csv_path}")
            except Exception as e:
                print(f"❌ CSV Logging Error: {e}")
            # ============================================================
            
            # Send notification and record
            create_redemption_notification(
                household_id=target_household,
                amount=total_amount,
                vouchers=token_data, # Pass the structured data
                merchant_name=merchant["merchant_name"]
            )
            
            result = {
                "success": True,
                "amount": total_amount,
                "vouchers": token_data,
                "household_id": target_household
            }
        else:
            flash("Invalid or Expired Token", "danger")

    return render_template(
        "merchant_dashboard.html",
        merchant=merchant,
        result=result
    )

# ------------------------------
# HOUSEHOLD REGISTRATION UI
# ------------------------------
@app.route("/ui/household", methods=["GET", "POST"])
def household_ui():
    result = None
    if request.method == "POST":
        data = {
            "members": [m.strip() for m in request.form.get("members", "").split(",")],
            "postal_code": request.form.get("postal_code")
        }
        response, status = register_household(data)
        result = response
    return render_template("register_household.html", result=result)

# ------------------------------
# MERCHANT REGISTRATION UI
# ------------------------------
@app.route("/ui/merchant", methods=["GET", "POST"])
def merchant_ui():
    result = None
    if request.method == "POST":
        data = request.form.to_dict()
        if not data:
            data = request.get_json(silent=True)
        response, status = register_merchant(data)
        result = response
    return render_template("register_merchant.html", result=result)

# -----------------------
# REDEEM VOUCHER UI
# -----------------------
@app.route("/ui/redeem/<household_id>", methods=["GET", "POST"])
def redeem_ui(household_id):
    # 1. Basic validation
    if household_id not in households:
        return "Household not found", 404
    
    household = households[household_id]
    vouchers = household.get('vouchers', {})
    result = None

    if request.method == "POST":
        # 2. Initialize variables
        token_data_structured = {} # Store { "Jan2026": {"10": 1}, "May2025": {"10": 1} }
        total_value = 0
        details_for_display = {} 
        has_selection = False
        error_msg = None

        # 3. Iterate form data
        # Front-end field naming convention: name="vouchers_{{tranche}}_{{denom}}"
        for key, value in request.form.items():
            if key.startswith("vouchers_"):
                try:
                    parts = key.split("_") 
                    denom_str = parts[-1]
                    tranche_name = "_".join(parts[1:-1])
                    
                    count = int(value)
                    
                    if count > 0:
                        has_selection = True
                        
                        # A. Validate balance
                        current_balance = 0
                        if tranche_name in vouchers and denom_str in vouchers[tranche_name]:
                            current_balance = vouchers[tranche_name][denom_str]
                        
                        if count > current_balance:
                            error_msg = f"Insufficient balance for {tranche_name} ${denom_str}. Max: {current_balance}"
                            break
                        
                        # B. Structure data correctly (Nested by Tranche)
                        if tranche_name not in token_data_structured:
                            token_data_structured[tranche_name] = {}
                        
                        # We don't need to aggregate same denom from same tranche because form input is unique per tranche/denom
                        token_data_structured[tranche_name][denom_str] = count
                            
                        # C. Calculate total value
                        total_value += int(denom_str) * count
                        
                        # D. Record display details
                        display_key = f"{tranche_name} ${denom_str}"
                        details_for_display[display_key] = count
                        
                except ValueError:
                    continue

        # 4. Process results
        if error_msg:
            flash(error_msg, "danger")
        elif not has_selection:
            flash("Please select at least one voucher.", "danger")
        else:
            # Generate Token
            token = "TXN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            # Save to database
            households[household_id]["active_token"] = token
            households[household_id]["token_data"] = token_data_structured # Save structured data
            save_households()
            
            result = {
                "success": True,
                "message": "Token Generated Successfully!",
                "token": token,
                "vouchers": details_for_display, 
                "total_value": total_value
            }

    return render_template(
        "redeem_voucher.html",
        household_id=household_id,
        vouchers=vouchers,
        result=result
    )
# -----------------------
# VOUCHER BALANCE UI
# -----------------------
@app.route("/ui/balance/<household_id>")
def balance_ui(household_id):
    if household_id not in households:
        return "Invalid household", 404
    household = households[household_id]
    vouchers = household.get('vouchers', {})
    return render_template(
        "balance.html",
        household_id=household_id,
        vouchers=vouchers
    )

# -----------------------
# VOUCHER CLAIM UI
# -----------------------
@app.route("/ui/claim/<household_id>", methods=["GET", "POST"])
def claim_ui(household_id):
    if household_id not in households:
        return "Invalid household", 404
    result = None
    if request.method == "POST":
        data = {
            "tranche": request.form.get("tranche")
        }
        response, status = claim_voucher(household_id, data)
        result = response
        # ✅ Redirect back to balance after success
        if status == 200:
            return redirect(f"/ui/balance/{household_id}")
    return render_template(
        "claim_voucher.html",
        household_id=household_id,
        result=result
    )

# ==========================================
# HOUSEHOLD APIs
# ==========================================

@app.route("/api/households", methods=["POST"])
def create_household():
    response, status = register_household(request.get_json(silent=True))
    return jsonify(response), status

@app.route("/api/households/<household_id>/claim", methods=["POST"])
def claim_api(household_id):
    response, status = claim_voucher(household_id, request.get_json(silent=True))
    return jsonify(response), status

@app.route("/api/households/<household_id>/balance", methods=["GET"])
def balance_api(household_id):
    response, status = get_redemption_balance(household_id)
    return jsonify(response), status

@app.route("/api/households/<household_id>/redeem", methods=["POST"])
def redeem_api(household_id):
    response, status = redeem_voucher(household_id, request.get_json(silent=True))
    return jsonify(response), status

@app.route("/api/households/<household_id>/transactions", methods=["GET"])
def get_transactions(household_id):
    """Get transaction history"""
    limit = request.args.get("limit", 20, type=int)
    transactions = get_transaction_history(household_id, limit)
    return jsonify({
        "household_id": household_id,
        "transactions": transactions
    }), 200

@app.route("/api/households/<household_id>/notifications", methods=["GET"])
def get_notifications(household_id):
    """Get notifications"""
    notifications = get_unread_notifications(household_id)
    notif_list = [n["notification"] for n in notifications]
    return jsonify({
        "household_id": household_id,
        "notifications": notif_list,
        "count": len(notif_list)
    }), 200

# ==========================================
# TOKEN APIs - NEW!
# ==========================================

@app.route("/api/token/generate", methods=["POST"])
def generate_token():
    """Generate redemption token"""
    data = request.get_json()
    household_id = data.get("household_id")
    vouchers = data.get("vouchers") # Expected: {Tranche: {Denom: Count}}
    
    if not household_id or not vouchers:
        return jsonify({"error": "household_id and vouchers required"}), 400
    
    load_households()
    
    if household_id not in households:
        return jsonify({"error": "Household not found"}), 404
    
    # Generate token
    token = "TXN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Calculate total - Handle both flat (legacy) and nested (new) structures for robustness
    total = 0
    # Check if vouchers is nested
    is_nested = any(isinstance(v, dict) for v in vouchers.values())
    
    if is_nested:
        for tranche, denoms in vouchers.items():
            for d, c in denoms.items():
                total += int(d) * int(c)
    else:
        # Fallback for flat structure (though we should move away from this)
        total = sum(int(d) * int(c) for d, c in vouchers.items())
    
    # Save token
    households[household_id]["active_token"] = token
    households[household_id]["token_data"] = vouchers
    save_households()
    
    print(f"✅ Generated token {token} for {household_id} (${total})")
    
    return jsonify({
        "token": token,
        "vouchers": vouchers,
        "household_id": household_id,
        "total": total
    }), 200

@app.route("/api/token/redeem", methods=["POST"])
def redeem_token():
    """Redeem token at merchant"""
    print("\n" + "="*50)
    print("🔍 REDEEM TOKEN REQUEST (MOBILE/API)")
    print("="*50)
    
    data = request.get_json(silent=True)
    token = data.get("token") if data else None
    merchant_id = data.get("merchant_id") if data else None
    
    if not token or not merchant_id:
        return jsonify({"error": "token and merchant_id required"}), 400
    
    load_households()
    load_merchants()
    
    # Find household with token
    target_household = None
    token_data = None
    
    for hid, h in households.items():
        if h.get("active_token") == token:
            target_household = hid
            token_data = h.get("token_data")
            break
    
    if not target_household or not token_data:
        return jsonify({"error": "Invalid or expired token"}), 400
    
    # Calculate total and Prepare CSV Data
    total_amount = 0
    voucher_list_for_csv = []
    
    household = households[target_household]
    
    # Check structure of token_data
    # We expect { "Jan2026": { "10": 1 } }
    
    # Deduct Logic
    for tranche_name, vouchers in token_data.items():
        if tranche_name not in household.get("vouchers", {}):
            continue
            
        for denom, count in vouchers.items():
            denom = str(denom)
            count = int(count)
            total_amount += int(denom) * count
            
            # Prepare CSV list
            for _ in range(count):
                voucher_list_for_csv.append(int(denom))
                
            # Deduct
            if denom in household["vouchers"][tranche_name]:
                household["vouchers"][tranche_name][denom] = max(0, household["vouchers"][tranche_name][denom] - count)

    # Clear token
    households[target_household]["active_token"] = None
    households[target_household]["token_data"] = None
    save_households()
    
    merchant_name = merchants.get(merchant_id, {}).get("merchant_name", "Merchant")
    
    # ✅ LOG TO CSV FILE - UNIFIED FORMAT WITH WEB UI
    try:
        os.makedirs("storage/redemptions", exist_ok=True)
        now = datetime.now()
        csv_filename = f"storage/redemptions/Redeem{now.strftime('%Y%m%d%H')}.csv"
        csv_path = os.path.join(csv_filename) # Reuse path var
        file_exists = os.path.exists(csv_path)

        txn_id = f"TX{now.strftime('%Y%m%d%H%M%S')}"
        txn_time_str = now.strftime("%Y-%m-%d-%H%M%S")
        
        # Sort for consistency
        voucher_list_for_csv.sort()
        
        with open(csv_path, mode="a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write Header if new file
            if not file_exists:
                writer.writerow([
                    "Transaction_ID", "Household_ID", "Merchant_ID", 
                    "Transaction_Date_Time", "Voucher_Code", "Denomination_Used", 
                    "Amount_Redeemed", "Payment_Status", "Remarks"
                ])
            
            total_items = len(voucher_list_for_csv)
            for index, denom_val in enumerate(voucher_list_for_csv):
                remark = "Final denomination used" if index == total_items - 1 else str(index + 1)
                v_code = f"V{target_household[-4:]}{str(index+1).zfill(3)}"
                
                writer.writerow([
                    txn_id, target_household, merchant_id, txn_time_str,
                    v_code, f"${denom_val}.00", f"${total_amount}.00",
                    "Completed", remark
                ])
                
        print(f"✅ Logged to CSV: {csv_filename}")
            
    except Exception as e:
        print(f"⚠️ CSV logging failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Create notification
    create_redemption_notification(
        household_id=target_household,
        amount=total_amount,
        vouchers=token_data,
        merchant_name=merchant_name
    )
    
    return jsonify({
        "success": True,
        "household_id": target_household,
        "amount": total_amount,
        "vouchers": token_data,
        "merchant_name": merchant_name
    }), 200

# ==========================================
# MERCHANT APIs
# ==========================================

@app.route("/api/merchants", methods=["POST"])
def merchant_api():
    response, status = register_merchant(request.get_json(silent=True))
    return jsonify(response), status

@app.route("/api/merchants/<merchant_id>", methods=["GET"])
def get_merchant(merchant_id):
    """Get merchant details"""
    load_merchants()
    
    if merchant_id not in merchants:
        return jsonify({"error": "Merchant not found"}), 404
    
    return jsonify(merchants[merchant_id]), 200

# ==========================================
# NOTIFICATION APIs
# ==========================================

@app.route("/api/notifications/<path:notification_id>", methods=["DELETE"])
def delete_notification(notification_id):
    """Delete notification"""
    filepath = f"storage/notifications/{notification_id}"
    if not filepath.endswith('.json'):
        filepath += '.json'
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Notification not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print("\n🚀 Starting Flask API Server...")
    print("📍 URL: http://localhost:8000")
    print("💡 Press Ctrl+C to stop\n")
    app.run(debug=True, port=8000, host='0.0.0.0')