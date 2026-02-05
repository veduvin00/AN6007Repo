# "AN6007 Group 13"
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
        # 获取输入的 ID (login_id 是新模版用的, household_id 是为了防错/兼容)
        login_id = request.form.get("login_id", "").strip()
        if not login_id:
             login_id = request.form.get("household_id", "").strip()

        # 1. 检查是否是 Household
        if login_id in households:
            return redirect(f"/ui/balance/{login_id}")
        
        # 2. 检查是否是 Merchant (新增逻辑)
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
    # 1. 安全检查
    if merchant_id not in merchants:
        return "Merchant not found", 404
    
    merchant = merchants[merchant_id]
    result = None
    
    # 2. 处理核销逻辑 (您提到的 Confirm Transaction 功能)
    if request.method == "POST":
        token = request.form.get("token", "").strip()
        
        # 调用现有的 API 逻辑 (复用 services/redemption_service.py 或直接调用 API 函数)
        # 这里我们直接调用 app.py 内部已经写好的 redeem_token 逻辑的变体，
        # 或者为了代码整洁，我们直接调用 API endpoint 的逻辑封装。
        # 为了不破坏现有结构，我这里直接通过 request 模拟调用后端逻辑，或者直接调用 service 层。
        
        # 使用 Service 层是最安全的（不通过 HTTP 避免开销）
        from services.redemption_service import redeem_voucher
        from services.household_service import households, save_households
        from services.notification_service import create_redemption_notification
        
        # 寻找 token 对应的 household (逻辑与 Flet App 类似)
        target_household = None
        token_data = None
        
        for hid, h in households.items():
            if h.get("active_token") == token:
                target_household = hid
                token_data = h.get("token_data")
                break
        
        if target_household and token_data:
            # 计算总金额
            total_amount = sum(int(d) * int(c) for d, c in token_data.items())
            
            # 扣除券
            h_obj = households[target_household]
            for denom, count in token_data.items():
                denom = str(denom)
                for tranche in h_obj.get("vouchers", {}).values():
                    if denom in tranche:
                        tranche[denom] = max(0, tranche[denom] - count)
                        break
            
            # 清除 Token
            households[target_household]["active_token"] = None
            households[target_household]["token_data"] = None
            save_households()
            
            # 发送通知并记录
            create_redemption_notification(
                household_id=target_household,
                amount=total_amount,
                vouchers=token_data,
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
    # 1. 基础校验
    if household_id not in households:
        return "Household not found", 404
    
    household = households[household_id]
    vouchers = household.get('vouchers', {})
    result = None

    if request.method == "POST":
        # 2. 初始化变量
        token_data_aggregated = {} # 用于存储 { "10": 总数量, "5": 总数量 }
        total_value = 0
        details_for_display = {} # 用于前端显示详情 { "Jan2026 $10": 2 }
        has_selection = False
        error_msg = None

        # 3. 遍历表单数据
        # 前端字段命名格式约定为: name="vouchers_{{tranche}}_{{denom}}"
        for key, value in request.form.items():
            if key.startswith("vouchers_"):
                try:
                    # 解析 key, 例如: vouchers_Jan2026_10
                    parts = key.split("_") 
                    # 注意：Tranche 名称可能包含下划线，所以我们取第一个_之后到最后一个_之前的部分作为 Tranche，最后一个作为 Denom
                    # 但为了简单，假设 Tranche 不含下划线，或者我们倒着取
                    denom_str = parts[-1]
                    tranche_name = "_".join(parts[1:-1])
                    
                    count = int(value)
                    
                    if count > 0:
                        has_selection = True
                        
                        # A. 校验余额
                        current_balance = 0
                        if tranche_name in vouchers and denom_str in vouchers[tranche_name]:
                            current_balance = vouchers[tranche_name][denom_str]
                        
                        if count > current_balance:
                            error_msg = f"Insufficient balance for {tranche_name} ${denom_str}. Max: {current_balance}"
                            break
                        
                        # B. 汇总数据 (为了兼容 Merchant App，我们需要按面额汇总)
                        if denom_str in token_data_aggregated:
                            token_data_aggregated[denom_str] += count
                        else:
                            token_data_aggregated[denom_str] = count
                            
                        # C. 计算总价值
                        total_value += int(denom_str) * count
                        
                        # D. 记录显示详情
                        display_key = f"{tranche_name} ${denom_str}"
                        details_for_display[display_key] = count
                        
                except ValueError:
                    continue

        # 4. 处理结果
        if error_msg:
            flash(error_msg, "danger")
        elif not has_selection:
            flash("Please select at least one voucher.", "danger")
        else:
            # 生成 Token
            token = "TXN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            # 保存到数据库
            households[household_id]["active_token"] = token
            households[household_id]["token_data"] = token_data_aggregated
            save_households()
            
            result = {
                "success": True,
                "message": "Token Generated Successfully!",
                "token": token,
                "vouchers": details_for_display, # 前端显示详细的 Tranche 信息
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
    vouchers = data.get("vouchers")
    
    if not household_id or not vouchers:
        return jsonify({"error": "household_id and vouchers required"}), 400
    
    load_households()
    
    if household_id not in households:
        return jsonify({"error": "Household not found"}), 404
    
    # Generate token
    token = "TXN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
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
    print("🔍 REDEEM TOKEN REQUEST")
    print("="*50)
    
    data = request.get_json(silent=True)
    print(f"Request data: {data}")
    
    token = data.get("token") if data else None
    merchant_id = data.get("merchant_id") if data else None
    
    print(f"Token: {token}")
    print(f"Merchant ID: {merchant_id}")
    
    if not token or not merchant_id:
        print("❌ Missing token or merchant_id")
        return jsonify({"error": "token and merchant_id required"}), 400
    
    load_households()
    load_merchants()
    
    print(f"Loaded {len(households)} households")
    
    # Find household with token
    target_household = None
    token_data = None
    
    for hid, h in households.items():
        active_token = h.get("active_token")
        if active_token:
            print(f"  Household {hid}: token={active_token}")
            if active_token == token:
                target_household = hid
                token_data = h.get("token_data")
                print(f"  ✅ MATCH FOUND!")
                break
    
    if not target_household or not token_data:
        print("❌ Token not found or expired")
        return jsonify({"error": "Invalid or expired token"}), 400
    
    print(f"✅ Found household: {target_household}")
    print(f"Token data: {token_data}")
    
    # Calculate total
    total_amount = sum(int(d) * int(c) for d, c in token_data.items())
    print(f"Total amount: ${total_amount}")
    
    # Deduct vouchers
    household = households[target_household]
    for denom, count in token_data.items():
        denom = str(denom)
        count = int(count)
        for tranche in household.get("vouchers", {}).values():
            if denom in tranche:
                old_count = tranche[denom]
                tranche[denom] = max(0, tranche[denom] - count)
                print(f"  Deducted ${denom}: {old_count} -> {tranche[denom]}")
                break
    
    # Clear token
    households[target_household]["active_token"] = None
    households[target_household]["token_data"] = None
    save_households()
    print("✅ Token cleared and households saved")
    
    # Get merchant name
    merchant_name = merchants.get(merchant_id, {}).get("merchant_name", "Merchant")
    print(f"Merchant name: {merchant_name}")
    
    # Create notification
    try:
        create_redemption_notification(
            household_id=target_household,
            amount=total_amount,
            vouchers=token_data,
            merchant_name=merchant_name
        )
        print("✅ Notification created")
    except Exception as e:
        print(f"⚠️ Notification failed: {e}")
    
    print(f"✅ Redeemed {token} for ${total_amount} at {merchant_name}")
    print("="*50 + "\n")
    
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