from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Product, User
import os
import stripe 
from decimal import Decimal

stripe.api_key = os.getenv("STRIPE_API_KEY")
