from flask import Flask, request, jsonify

from services.household_service import (
    register_household,
    get_redemption_balance,
    load_households
)
from services.voucher_service import claim_voucher
from services.redemption_service import redeem_voucher
from services.merchant_service import register_merchant

app = Flask(__name__)

load_households()

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
