from flask import Blueprint, request, jsonify
from models import Package, Service, User, db, Message
from datetime import datetime
from flask_login import login_required, current_user    

package_bp = Blueprint("package", __name__)

@package_bp.route("/api/v1/packages", methods=["POST"])
@login_required
def create_package():
    if current_user.role != User.ROLE['seller']:
        return jsonify({"error": "Only sellers can create packages"}), 403

    data = request.get_json()

    service_id = data.get("service_id")
    title = data.get("title")
    description = data.get("description")
    benefits = data.get("benefits")
    price = data.get("price")
    delivery_time_days = data.get("delivery_time_days")

    if not all([service_id, title, description, price, delivery_time_days]):
        return jsonify({"error": "Missing required fields"}), 400

    if price <= 0:
        return jsonify({"error": "Price must be greater than 0"}), 400

    if delivery_time_days <= 0:
        return jsonify({"error": "Delivery time must be at least 1 day"}), 400

    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "Service not found"}), 404
    if service.seller_id != current_user.id:
        return jsonify({"error": "You can only add packages to your own service"}), 403

    existing = Package.query.filter_by(service_id=service_id, title=title).first()
    if existing:
        return jsonify({"error": "Package with this title already exists for this service"}), 409

    package = Package(
        service_id=service_id,
        title=title,
        description=description,
        benefits=benefits, 
        price=price,
        delivery_time_days=delivery_time_days
    )

    db.session.add(package)
    db.session.commit()

    return jsonify({
        "message": "Package created successfully",
        "package_id": package.id
    }), 201
    
    
@package_bp.route("/api/v1/services/<int:service_id>/packages", methods=["GET"])
def get_service_packages(service_id):
    packages = Package.query.filter_by(service_id=service_id).all()

    result = []
    for pkg in packages:
        result.append({
            "id": pkg.id,
            "title": pkg.title,
            "description": pkg.description,
            "benefits": pkg.benefits,
            "price": float(pkg.price),
            "delivery_time_days": pkg.delivery_time_days
        })

    return jsonify(result), 200



@package_bp.route("/api/v1/packages/<int:package_id>", methods=["PUT"])
@login_required
def update_package(package_id):
    package = Package.query.get(package_id)
    if not package:
        return jsonify({"error": "Package not found"}), 404

    service = Service.query.get(package.service_id)
    if service.seller_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    package.title = data.get("title", package.title)
    package.description = data.get("description", package.description)
    package.benefits = data.get("benefits", package.benefits)
    package.price = data.get("price", package.price)
    package.delivery_time_days = data.get("delivery_time_days", package.delivery_time_days)

    db.session.commit()

    return jsonify({"message": "Package updated"}), 200



@package_bp.route("/api/v1/packages/<int:package_id>", methods=["DELETE"])
@login_required
def delete_package(package_id):
    package = Package.query.get(package_id)
    if not package:
        return jsonify({"error": "Package not found"}), 404

    service = Service.query.get(package.service_id)
    if service.seller_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(package)
    db.session.commit()

    return jsonify({"message": "Package deleted"}), 200