from flask import Blueprint, jsonify
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/v1')

@dashboard_bp.route("/auth/dashboard", methods=["GET"])
@login_required
def dashboard():
    return jsonify({
        "message": "Welcome to the dashboard",
        "status": "success",
        "user": {
            "fullname": current_user.fullname,
            "email": current_user.email,
            "address": getattr(current_user, "address", None),
            "contact": getattr(current_user, "contact", None)  
        }
    }), 200