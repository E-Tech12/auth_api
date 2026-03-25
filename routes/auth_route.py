import email
from flask import Blueprint, app, request, jsonify, session, current_app
import random
from werkzeug.security import generate_password_hash
from flask_login import login_required, login_user
from flask_mail import Message
import re
from datetime import datetime, timedelta

from extensions import db, mail
from models import User, PasswordReset,EmailOTP

auth_bp = Blueprint('auth', __name__)
@auth_bp.route("/api/v1/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    fullname = data.get("fullname")
    address = data.get("address")
    contact = data.get("contact")
    role = data.get("role", "buyer") 

    if not email or not password or not fullname or not address:
            return jsonify({"error": "Email, password, fullname and address are required"}), 400



    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Invalid credentials"}), 409

    otp = str(random.randint(100000, 999999))
    expiry = datetime.utcnow() + timedelta(minutes=5)

    otp_record = EmailOTP(
        email=email,
        otp=otp,
        password=generate_password_hash(password),  
        fullname=fullname,
        address=address,
        contact=contact,
        role=role,  
        expires_at=expiry
    )

    db.session.add(otp_record)
    db.session.commit()

    msg = Message(
        subject="Verify your email",
        recipients=[email],
        body=f"Your OTP code is {otp}. It expires in 5 minutes."
    )
    mail.send(msg)

    return jsonify({"message": "OTP sent to your email"}), 200



@auth_bp.route("/api/v1/auth/verify-signup-otp", methods=["POST"])
def verify_signup_otp():
    data = request.get_json()

    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    otp_record = EmailOTP.query.filter_by(email=email, otp=otp).first()
    if not otp_record:
        return jsonify({"error": "Invalid OTP"}), 400

    if otp_record.expires_at < datetime.utcnow():
        db.session.delete(otp_record)
        db.session.commit()
        return jsonify({"error": "OTP expired"}), 400

    new_user = User(
        email=otp_record.email,
        password=otp_record.password,  
        fullname=otp_record.fullname,
        address=otp_record.address,
        contact=otp_record.contact,
        role=otp_record.role or "buyer"  
    )

    db.session.add(new_user)
    db.session.delete(otp_record)
    db.session.commit()

    return jsonify({"message": "Signup successful"}), 201

@auth_bp.route("/api/v1/auth/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Invalid Credentials"}), 404

    if not user.check_password(password):
        return jsonify({"error": "Invalid Credentials"}), 401

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

@auth_bp.route('/api/v1/auth/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"error": "Email and OTP are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    reset_record = PasswordReset.query.filter_by(
        user_id=user.id, otp=otp, is_used=False
    ).first()

    if not reset_record:
        return jsonify({"error": "Invalid OTP"}), 400

    if reset_record.is_expired():
        db.session.delete(reset_record)
        db.session.commit()
        return jsonify({"error": "OTP has expired"}), 400

    reset_record.is_used = True

    session['reset_user_id'] = user.id

    db.session.commit()

    return jsonify({"message": "OTP verified successfully"}), 200

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

