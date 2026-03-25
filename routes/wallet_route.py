from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from models import Order, Wallet,db

wallet_bp = Blueprint("wallet", __name__)

@wallet_bp.route("/api/v1/wallet", methods=["GET"])
@login_required
def get_wallet():

    wallet = current_user.wallet

    if not wallet:
        wallet = Wallet(user_id=current_user.id)
        db.session.add(wallet)
        db.session.commit()

        wallet = current_user.wallet 

    return jsonify({
        "balance": float(wallet.balance),
        "pending_balance": float(wallet.pending_balance)
    }), 200
    
@wallet_bp.route("/api/v1/orders/<int:id>/pay", methods=["POST"])
@login_required
def pay_order(id):

    order = Order.query.get_or_404(id)

    if order.buyer_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    if order.status != Order.STATUS['pending']:
        return jsonify({"error": "Order already processed"}), 400

    order.status = Order.STATUS['in_progress']

    db.session.commit()

    return jsonify({
        "message": "Payment successful. Order started.",
        "order_id": order.id,
        "status": order.status
    }), 200