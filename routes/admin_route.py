from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import User, Order, Withdrawal, db

admin_bp = Blueprint("admin", __name__)

def admin_only():
    if current_user.role != User.ROLE['super_admin']:
        return False
    return True

@admin_bp.route("/api/v1/admin/approve-seller/<int:user_id>", methods=["PUT"])
@login_required
def approve_seller(user_id):

    if not admin_only():
        return jsonify({"error": "Admin only"}), 403

    user = User.query.get_or_404(user_id)

    if user.role != User.ROLE['seller']:
        return jsonify({"error": "User is not a seller"}), 400

    user.is_approved = True
    db.session.commit()

    return jsonify({
        "message": "Seller approved",
        "seller_id": user.id
    }), 200
    
@admin_bp.route("/api/v1/admin/users", methods=["GET"])
@login_required
def get_all_users():

    if not admin_only():
        return jsonify({"error": "Admin only"}), 403

    users = User.query.all()

    result = []
    for u in users:
        result.append({
            "id": u.id,
            "fullname": u.fullname,
            "email": u.email,
            "role": u.role,
            "is_approved": u.is_approved
        })

    return jsonify(result), 200

@admin_bp.route("/api/v1/admin/withdrawals", methods=["GET"])
@login_required
def get_all_withdrawals():

    if not admin_only():
        return jsonify({"error": "Admin only"}), 403

    withdrawals = Withdrawal.query.all()

    result = []
    for w in withdrawals:
        result.append({
            "id": w.id,
            "wallet_id": w.wallet_id,
            "amount": float(w.amount),
            "status": w.status,
            "created_at": w.created_at
        })

    return jsonify(result), 200

@admin_bp.route("/api/v1/admin/withdrawals/<int:withdrawal_id>", methods=["PUT"])
@login_required
def handle_withdrawal(withdrawal_id):

    if not admin_only():
        return jsonify({"error": "Admin only"}), 403

    withdrawal = Withdrawal.query.get_or_404(withdrawal_id)

    data = request.get_json()
    action = data.get("action")

    if action == "approve":
        withdrawal.status = "approved"

    elif action == "reject":
        withdrawal.status = "rejected"

    else:
        return jsonify({"error": "Invalid action"}), 400

    db.session.commit()

    return jsonify({
        "message": f"Withdrawal {action}d"
    }), 200