from flask import Blueprint, request, jsonify
from models import AccountDetails, Package, Service, User, db, Message
from datetime import datetime
from flask_login import login_required, current_user    

accdetails_bp = Blueprint("accdetails", __name__)


@accdetails_bp.route("/api/v1/account-details", methods=["POST"])
@login_required
def create_account_details():
    
    data = request.get_json()
    
    if current_user.role != User.ROLE['seller']:
        return jsonify({"error": "Only sellers can add account details"}), 403

    bank_name = data.get("bank_name")
    account_number = data.get("account_number")
    account_name = data.get("account_name")

    if not all([bank_name, account_number, account_name]):
        return jsonify({"error": "All fields are required"}), 400
    existing = AccountDetails.query.filter_by(user_id=current_user.id).first()
    if existing:
        return jsonify({"error": "Account details already exist"}), 409

    account = AccountDetails(
        user_id=current_user.id,
        bank_name=bank_name,
        account_number=account_number,
        account_name=account_name
    )

    db.session.add(account)
    db.session.commit()

    return jsonify({"message": "Account details saved"}), 201

@accdetails_bp.route("/api/v1/account-details", methods=["GET"])
@login_required
def get_account_details():
    account = AccountDetails.query.filter_by(user_id=current_user.id).first()

    if not account:
        return jsonify({"error": "Account details not found"}), 404

    return jsonify({
        "bank_name": account.bank_name,
        "account_number": account.account_number,
        "account_name": account.account_name
    }), 200
    
@accdetails_bp.route("/api/v1/account-details", methods=["PUT"])
@login_required
def update_account_details():
    account = AccountDetails.query.filter_by(user_id=current_user.id).first()

    if not account:
        return jsonify({"error": "Account details not found"}), 404

    data = request.get_json()

    account.bank_name = data.get("bank_name", account.bank_name)
    account.account_number = data.get("account_number", account.account_number)
    account.account_name = data.get("account_name", account.account_name)

    db.session.commit()

    return jsonify({"message": "Account details updated"}), 200