from flask import Blueprint, request, jsonify
from models import AccountDetails, Package, Service, Transaction, User, Wallet, Wallet, Withdrawal, db, Message
from datetime import datetime
from flask_login import login_required, current_user    

withdraw_bp = Blueprint("withdraw", __name__)
@withdraw_bp.route("/api/v1/withdrawals", methods=["POST"])
@login_required
def request_withdrawal():
    if current_user.role != User.ROLE['seller']:
        return jsonify({"error": "Only sellers can withdraw"}), 403

    wallet = Wallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404

    account = AccountDetails.query.filter_by(user_id=current_user.id).first()
    if not account:
        return jsonify({"error": "Add account details first"}), 400

    data = request.get_json()
    amount = data.get("amount")

    if not amount or float(amount) <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    if float(amount) > float(wallet.balance):
        return jsonify({"error": "Insufficient balance"}), 400

    # Create withdrawal
    withdrawal = Withdrawal(
        wallet_id=wallet.id,
        amount=amount,
        status='pending'
    )

    # Update wallet
    wallet.balance -= amount
    wallet.pending_balance += amount

    # Create transaction
    transaction = Transaction(
        wallet_id=wallet.id,
        amount=amount,
        type=Transaction.TYPE['withdrawal'],
        description="Withdrawal request",
        status="pending"  # 🔥 better to mark pending
    )

    # Add ALL before commit
    db.session.add(withdrawal)
    db.session.add(transaction)

    db.session.commit()

    return jsonify({
        "message": "Withdrawal request submitted",
        "amount": float(amount)
    }), 201
    
@withdraw_bp.route("/api/v1/withdrawals", methods=["GET"])
@login_required
def get_my_withdrawals():
    wallet = Wallet.query.filter_by(user_id=current_user.id).first()

    withdrawals = Withdrawal.query.filter_by(wallet_id=wallet.id).all()

    result = []
    for w in withdrawals:
        result.append({
            "id": w.id,
            "amount": float(w.amount),
            "status": w.status,
            "created_at": w.created_at
        })

    return jsonify(result), 200


@withdraw_bp.route("/api/v1/admin/withdrawals/<int:withdrawal_id>", methods=["PUT"])
@login_required
def handle_withdrawal(withdrawal_id):
    if current_user.role != User.ROLE['super_admin']:
        return jsonify({"error": "Admin only"}), 403

    withdrawal = Withdrawal.query.get(withdrawal_id)
    if not withdrawal:
        return jsonify({"error": "Withdrawal not found"}), 404

    data = request.get_json()
    action = data.get("action")  
    wallet = Wallet.query.get(withdrawal.wallet_id)

    if action == "approve":
        withdrawal.status = "approved"
        wallet.pending_balance -= withdrawal.amount

    elif action == "reject":
        withdrawal.status = "rejected"

        wallet.pending_balance -= withdrawal.amount
        wallet.balance += withdrawal.amount

    else:
        return jsonify({"error": "Invalid action"}), 400

    db.session.commit()

    return jsonify({"message": f"Withdrawal {action}d"}), 200

