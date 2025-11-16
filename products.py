from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Product, User
import os
import stripe
from decimal import Decimal


products_bp = Blueprint("products", __name__, url_prefix="/api")

stripe.api_key =  os.getenv("STRIPE_SECRET_KEY")


def add_stripe_products(): # helper function
    """Sync products from Stripe into the local Product table."""
    if not stripe.api_key:
        # If key is missing, just skip Stripe sync instead of crashing
        current_app.logger.warning("STRIPE_SECRET_KEY not configured; skipping Stripe sync.")
        return

    try:
        stripe_products = stripe.Product.list(limit=100, expand=["data.default_price"])
    except Exception as e:
        # Log but don't kill the request
        current_app.logger.error(f"Stripe error while syncing products: {e}")
        return

    for sp in stripe_products.auto_paging_iter():
        default_price = sp.default_price


        if default_price and default_price.unit_amount is not None:
            price = (Decimal(default_price.unit_amount) / Decimal(100)).quantize(Decimal("0.01"))
        else:
            price = Decimal("0.00")

        exists = Product.query.filter_by(name=sp.name).first()
        if exists:
            exists.price = price
            exists.available = sp.active
            exists.image_url = sp.images[0] if sp.images else None
            exists.description = sp.description
        else:
            p = Product(
                name=sp.name,
                price=price,
                image_url=sp.images[0] if sp.images else None,
                inventory=0,
                available=sp.active,
                description=sp.description,
            )
            db.session.add(p)

    db.session.commit()


# -------------------------------
# GET /api/products  (list products)
# -------------------------------
@products_bp.route("/products", methods=["GET"])
def list_products():
    """List all products"""
    add_stripe_products()
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products]), 200


# -------------------------------
# POST /api/products  (add product)
# -------------------------------
@products_bp.route("/products", methods=["POST"])
@jwt_required()
def create_product():
    """Create a new product."""
    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    image_url = data.get("image_url")
    inventory = data.get("inventory", 0)
    available = data.get("available", True)
    description = data.get("description")

    if not name or price is None:
        return jsonify({"error": "name required"}), 400
    
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    try:
        inventory = int(inventory)
    except Exception:
        return jsonify({"error": "inventory should be an integer"}), 400
    new_product = Product(
        name=name,
        price=price,
        image_url=image_url,
        inventory=inventory,
        available=available,
        description=description)
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201


# -------------------------------
# GET /api/product/<id>  (retrieve)
# -------------------------------
@products_bp.route("/products/<int:product_id>", methods=["GET"])
@jwt_required()
def get_product(product_id):
    """Retrieve a single product."""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "user not found"}), 404

    return jsonify(product.to_dict()), 200


# -------------------------------
# PUT /api/product/<id>  (update)
# -------------------------------
@products_bp.route("/products/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    """Update an product."""
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "not found"}), 404

    data = request.get_json() or {}
    if "name" in data:
        product.name = data["name"]
    if "price" in data:
        product.price = data["price"]
    if "image_url" in data:
        product.image_url = data["image_url"]
    if "inventory" in data:
        try:
            product.inventory =int( data["inventory"])
        except Exception:
            return jsonify({"error": "inventory should be integer"}), 400
    if "available" in data:
        product.available = data["available"]
    if "description" in data:
        product.description = data["description"]

    db.session.commit()
    return jsonify(product.to_dict()), 200


# -------------------------------
# DELETE /api/product/<id>  (delete)
# -------------------------------
@products_bp.route("/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    """Delete an product"""
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
