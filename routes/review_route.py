from flask import Blueprint, request, jsonify
from models import Order, Package, Review, Service, User, db, Message
from datetime import datetime
from flask_login import login_required, current_user    

review_bp = Blueprint("review", __name__)

@review_bp.route("/api/v1/reviews", methods=["POST"])
@login_required
def create_review():
    data = request.get_json()

    order_id = data.get("order_id")
    rating = data.get("rating")
    comment = data.get("comment")

    if not order_id or not rating:
        return jsonify({"error": "Order ID and rating required"}), 400

    if int(rating) < 1 or int(rating) > 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.buyer_id != current_user.id:
        return jsonify({"error": "Only buyer can review"}), 403

    if order.status != Order.STATUS['completed']:
        return jsonify({"error": "Order not completed yet"}), 400

    existing = Review.query.filter_by(order_id=order_id).first()
    if existing:
        return jsonify({"error": "Review already exists"}), 409

    review = Review(
        order_id=order_id,
        reviewer_id=current_user.id,
        rating=rating,
        comment=comment
    )

    db.session.add(review)
    db.session.commit()

    return jsonify({"message": "Review submitted"}), 201

@review_bp.route("/api/v1/services/<int:service_id>/reviews", methods=["GET"])
def get_service_reviews(service_id):

    reviews = Review.query.join(Order).filter(
        Order.service_id == service_id
    ).all()

    result = []
    for r in reviews:
        result.append({
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at
        })

    return jsonify(result), 200


