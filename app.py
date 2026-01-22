"AN6007 Group 13"
from flask import Flask, request, jsonify, render_template, redirect
from services.household_service import (
    register_household,
    get_redemption_balance,
    load_households,
    households
)
from services.voucher_service import claim_voucher
from services.redemption_service import redeem_voucher
from services.merchant_service import register_merchant

app = Flask(__name__)

load_households()

@app.route("/")
def home():
    return render_template("home.html")

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
        data = request.get_json()
        response, status = register_merchant(data)
        result = response

    return render_template("register_merchant.html", result=result)


# -----------------------
# REDEEM VOUCHER UI
# -----------------------
@app.route("/ui/redeem/<household_id>", methods=["GET", "POST"])
def redeem_ui(household_id):

    result = None

    if request.method == "POST":
        data = request.form.to_dict()
        response, status = redeem_voucher(household_id, data)
        result = response

    household = households[household_id]

    return render_template(
        "redeem_voucher.html",
        household_id=household_id,
        vouchers=household.vouchers,
        result=result
    )


# -----------------------
# VOUCHER BACALNCE UI
# -----------------------
@app.route("/ui/balance/<household_id>")
def balance_ui(household_id):
    if household_id not in households:
        return "Invalid household", 404

    household = households[household_id]

    return render_template(
        "balance.html",
        household_id=household_id,
        vouchers=household.vouchers
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


@app.route("/api/merchants", methods=["POST"])
def merchant_api():
    response, status = register_merchant(request.get_json(silent=True))
    return jsonify(response), status


if __name__ == "__main__":
    app.run(debug=True)
