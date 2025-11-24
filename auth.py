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

    # Validate input, ensuring no missing credentials
    if not email or not password:
        return jsonify({"error": "Email and password required for registration"}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first() :
        return jsonify({"error": "Email already exists"}), 409

    # Create and save user
    new_user = User(email=email, phone_number=phone_number)
    new_user.set_password(password)
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
 



