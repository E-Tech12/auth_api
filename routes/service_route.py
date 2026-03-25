from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from models import User, db, Service
from datetime import datetime

service_bp = Blueprint("service", __name__)

def serialize_service(service):
    return {
        "id": service.id,
        "seller_id": service.seller_id,
        "title": service.title,
        "description": service.description,
        "price": float(service.base_price) if service.base_price else None,
        "is_available": service.is_available,
        "created_at": service.created_at.isoformat()
    }
    

# Create Service
@service_bp.route("/api/v1/services", methods=["POST"])
@login_required
def create_service():
    data = request.get_json()
    
      
    if current_user.role != User.ROLE['seller']:
        return jsonify({"error": "Only sellers can create services"}), 403

    if not current_user.is_approved:
        return jsonify({"error": "Seller not approved yet"}), 403

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if not data.get("seller_id") or not data.get("title") or not data.get("description"):
        return jsonify({"error": "seller_id, title, and description are required"}), 400

    try:
        new_service = Service(
            seller_id=current_user.id,
            title=data.get("title"),
            description=data.get("description"),
            base_price=data.get("base_price"),
            is_available=data.get("is_available", True),
            created_at=datetime.utcnow()
        )

        db.session.add(new_service)
        db.session.commit()

        return jsonify({
            "message": "Service created",
            "data": serialize_service(new_service)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Get Services
@service_bp.route("/api/v1/services", methods=["GET"])
@login_required
def get_services():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 50)
        query = Service.query

        is_available = request.args.get("is_available")
        if is_available is not None:
            query = query.filter_by(is_available=(is_available.lower() == "true"))

        services = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            "data": [serialize_service(s) for s in services.items],
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": services.total,
                "pages": services.pages
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@service_bp.route("/api/v1/services/<int:id>", methods=["GET"])
@login_required
def get_service(id):
    service = Service.query.get_or_404(id)

    return jsonify({
        "data": serialize_service(service)
    }), 200



# Update Service
@service_bp.route("/api/v1/services/<int:id>", methods=["PUT"])
@login_required
def update_service(id):
    service = Service.query.get_or_404(id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        service.title = data.get("title", service.title)
        service.description = data.get("description", service.description)
        service.base_price = data.get("base_price", service.base_price)
        service.is_available = data.get("is_available", service.is_available)

        db.session.commit()

        return jsonify({
            "message": "Service updated",
            "data": serialize_service(service)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Delete Service
@service_bp.route("/api/v1/services/<int:id>", methods=["DELETE"])
@login_required
def delete_service(id):
    service = Service.query.get_or_404(id)

    try:
        db.session.delete(service)
        db.session.commit()

        return jsonify({"message": "Service deleted"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500