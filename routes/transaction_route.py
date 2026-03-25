from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import Transaction, Wallet

transaction_bp = Blueprint("transaction", __name__)

@transaction_bp.route("/api/v1/transactions", methods=["GET"])
@login_required
def get_my_transactions():

    wallet = current_user.wallet

    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404

    transactions = Transaction.query.filter_by(wallet_id=wallet.id).all()

    result = []
    for t in transactions:
        result.append({
            "id": t.id,
            "amount": float(t.amount),
            "type": t.type,
            "status": t.status,
            "description": t.description,
            "created_at": t.created_at
        })

    return jsonify(result), 200

@transaction_bp.route("/api/v1/transactions/<int:id>", methods=["GET"])
@login_required
def get_transaction(id):

    transaction = Transaction.query.get_or_404(id)

    if transaction.wallet.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "id": transaction.id,
        "amount": float(transaction.amount),
        "type": transaction.type,
        "status": transaction.status,
        "description": transaction.description,
        "created_at": transaction.created_at
    }), 200