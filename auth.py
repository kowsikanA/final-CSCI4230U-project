# Imports 
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from datetime import timedelta
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__)


# POST /auth/register
@auth_bp.route("/register", methods=["POST"])
def register():
    # Getting json from data sent from request body 
    data = request.get_json() or {}

    # Storing email, number, and password from json data from frontend
    email = data.get("email")
    phone_number = (data.get("phone_number") or None)
    password = data.get("password") 
    security_question = data.get("security_question")
    security_answer = data.get("security_answer")

    # Validate input, ensuring no missing credentials
    if not email or not password:
        return jsonify({"error": "Email and password required for registration"}), 400
    
    if not security_question or not security_answer:
        return jsonify({"error": "security question and answer are required"}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first() :
        return jsonify({"error": "Email already exists"}), 409

    # Create and save user
    new_user = User(email=email, phone_number=phone_number)
    new_user.set_password(password)
    new_user.security_question = security_question
    new_user.set_security_answer(security_answer)

    db.session.add(new_user)
    db.session.commit()

    # Return success message 
    return jsonify({"id": new_user.id, "email": new_user.email, "phone_number": new_user.phone_number}), 201


# POST /auth/login
@auth_bp.route("/login", methods=["POST"])
def login():
    
    # Getting json from data sent from request body
    data = request.get_json() or {}

    # Storing email and password from json data from frontend
    email = data.get("email")
    password = data.get("password")

    # Ensuring no missing credentials
    if not email or not password:
        return jsonify({"error": "username and password required"}), 400

    # Checking database to ensure that email and password match 
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "bad credentials"}), 401

    # Generate JWT access token, experies in 1 hour 
    access_token = create_access_token(
        identity=email,
        expires_delta=timedelta(hours=1)
    )

    # Returning access token, may remove later for security purposes 
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}

    email = (data.get("email") or "").strip()
    answer = (data.get("security_answer") or "").strip()
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    # 1) Basic validation
    if not email or not answer or not new_password or not confirm_password:
        return jsonify({"error": "Please fill in all fields."}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400

    # 2) Look up user
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No account found with that email."}), 404

    # 3) Check security answer using your model helper
    if not user.check_security_answer(answer):
        return jsonify({"error": "Security answer is incorrect."}), 401

    # 4) Update password
    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password updated. You can now log in."}), 200


 



