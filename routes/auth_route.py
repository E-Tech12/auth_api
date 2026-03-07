from flask import Blueprint, app, request, jsonify, session, current_app
import random
from werkzeug.security import generate_password_hash
from flask_login import login_required, login_user
from flask_mail import Message

from extensions import db, mail
from models import User, PasswordReset

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/api/v1/auth/signup", methods=["POST"])
def signup():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    fullname = data.get("fullname")
    address = data.get("address")
    contact = data.get("contact")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    hashed_password = generate_password_hash(password)

    new_user = User(
        email=email,
        password=hashed_password,
        fullname=fullname,
        address=address,
        contact=contact
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully"
    }), 201

@auth_bp.route("/api/v1/auth/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    login_user(user)

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "fullname": user.fullname
        }
    }), 200


@auth_bp.route('/api/v1/auth/forgot-password', methods=['POST'])
def forgot_password():

    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    otp = str(random.randint(100000, 999999))

    reset_request = PasswordReset(user_id=user.id, otp=otp)
    db.session.add(reset_request)
    db.session.commit()

    msg = Message(
        subject="Your OTP for Password Reset",
        recipients=[email],
        body=f"Hello {user.fullname},\n\nYour OTP is: {otp}"
    )

    try:
        mail.send(msg)

        return jsonify({
            "message": "OTP sent to your email"
        }), 200

    except Exception as e:
        current_app.logger.error("Failed to send OTP", exc_info=True)

        return jsonify({
            "error": "Failed to send OTP"
        }), 500

@auth_bp.route("/api/v1/auth/verify-otp", methods=["POST"])
def verify_otp():

    data = request.get_json()
    entered_otp = data.get("otp")

    if not entered_otp:
        return jsonify({"error": "OTP is required"}), 400

    reset_request = PasswordReset.query.filter_by(
        otp=entered_otp,
        is_used=False
    ).order_by(PasswordReset.created_at.desc()).first()

    if not reset_request:
        return jsonify({"error": "Invalid OTP"}), 400

    if reset_request.is_expired():
        return jsonify({"error": "OTP expired"}), 400

    reset_request.is_used = True
    db.session.commit()

    session['reset_user_id'] = reset_request.user_id

    return jsonify({
        "message": "OTP verified successfully"
    }), 200
    

@auth_bp.route("/api/v1/auth/reset-password", methods=['POST'])
def reset_password():

    user_id = session.get('reset_user_id')
    if not user_id:
        return jsonify({"error": "Session expired or OTP not verified"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    new_password = data.get("password")

    if not new_password:
        return jsonify({"error": "Password is required"}), 400

    user.password = generate_password_hash(new_password)
    db.session.commit()

    session.pop('reset_user_id', None)

    return jsonify({
        "message": "Password reset successfully"
    }), 200
    

