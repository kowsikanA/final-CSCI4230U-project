from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    email = data.get("email")
    phone_number = data.get("phone_number") or None
    password = data.get("password")
    security_question = data.get("security_question")
    security_answer = data.get("security_answer")

    if not email or not password:
        return jsonify({"error": "Email and password required for registration"}), 400

    if not security_question or not security_answer:
        return jsonify({"error": "security question and answer are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 409

    new_user = User(email=email, phone_number=phone_number)
    new_user.set_password(password)
    new_user.security_question = security_question
    new_user.set_security_answer(security_answer)

    db.session.add(new_user)
    db.session.commit()

    return jsonify(
        {
            "id": new_user.id,
            "email": new_user.email,
            "phone_number": new_user.phone_number,
        }
    ), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "username and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "bad credentials"}), 401

    access_token = create_access_token(
        identity=email,
        expires_delta=timedelta(hours=1),
    )

    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}

    email = (data.get("email") or "").strip()
    answer = (data.get("security_answer") or "").strip()
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not email or not answer or not new_password or not confirm_password:
        return jsonify({"error": "Please fill in all fields."}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No account found with that email."}), 404

    if not user.check_security_answer(answer):
        return jsonify({"error": "Security answer is incorrect."}), 401

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password updated. You can now log in."}), 200
