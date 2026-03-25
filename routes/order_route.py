from flask import Blueprint, request, jsonify
from flask_login import current_user,login_required
from models import Package, Service, User, db, Order
from datetime import datetime
from models import Service,Package

order_bp = Blueprint("order", __name__)
@order_bp.route("/api/v1/orders", methods=["POST"])
@login_required
def create_order():
        data = request.get_json()

        service = Service.query.get(data.get("service_id"))
        package = Package.query.get(data.get("package_id"))
        amount = package.price

        if not service or not package:
            return jsonify({"error": "Service or package not found"}), 404

        if package.service_id != service.id:
            return jsonify({"error": "Package does not belong to this service"}), 400

        new_order = Order(
            buyer_id=current_user.id,
            seller_id=service.seller_id,
            service_id=service.id,
            package_id=package.id,
            amount=package.price
        )

        db.session.add(new_order)
        db.session.commit()

        return jsonify({"message": "Order created"}), 201

@order_bp.route("/api/v1/orders", methods=["GET"])
def get_orders():
    orders = Order.query.all()

    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "status": o.status,
            "amount": str(o.amount)
        })

    return jsonify(result)



@order_bp.route("/api/v1/orders/<int:id>/status", methods=["PATCH"])
def update_order_status(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()

    if data["status"] not in Order.STATUS.values():
        return jsonify({"error": "Invalid status"}), 400
    order.status = data["status"]
    db.session.commit()

    return jsonify({"message": "Order status updated"})