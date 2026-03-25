from flask import Blueprint, request, jsonify
from flask_login import current_user
from models import db, Message
from datetime import datetime

message_bp = Blueprint("message", __name__)


@message_bp.route("/api/v1/orders/<int:order_id>/messages", methods=["POST"])
def send_message(order_id):
    data = request.get_json()

    msg = Message(
        order_id=order_id,
        sender_id=current_user.id,
        receiver_id=data.get("receiver_id"),
        content=data.get("content"),
        timestamp=datetime.utcnow()
    )

    db.session.add(msg)
    db.session.commit()

    return jsonify({"message": "Message sent"})

@message_bp.route("/api/v1/orders/<int:order_id>/messages", methods=["GET"])
def get_messages(order_id):
    messages = Message.query.filter_by(order_id=order_id).all()

    result = []
    for m in messages:
        result.append({
            "sender": m.sender_id,
            "content": m.content,
            "time": m.timestamp
        })

    return jsonify(result)