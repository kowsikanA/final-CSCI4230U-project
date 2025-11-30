from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import CartItem, Product, User

carts_bp = Blueprint("cart", __name__, url_prefix="/api")


# GET /api/cart  – list current user's cart
@carts_bp.route("/cart", methods=["GET"])
@jwt_required()
def list_cart():
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()

    if not user:
        return jsonify({"error": "user not found"}), 404

    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    return jsonify([cart.to_dict() for cart in cart_items]), 200


# POST /api/cart  – add product to cart
@carts_bp.route("/cart", methods=["POST"])
@jwt_required()
def add_to_cart():
    data = request.get_json() or {}

    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not product_id:
        return jsonify({"error": "product_id required"}), 400

    try:
        quantity = int(quantity)
    except Exception:
        return jsonify({"error": "quantity should be integer"}), 400

    if quantity <= 0:
        return jsonify({"error": "Invalid quantity"}), 400

    # Ensure product_id is an int
    try:
        product_id_int = int(product_id)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid product_id"}), 400

    product = Product.query.get(product_id_int)

    # If product not found in DB, create it from frontend (DummyJSON) data
    if not product:
        name = data.get("name")
        price = data.get("price")
        image_url = data.get("image_url")
        description = data.get("description", "")

        if not name or price is None:
            return jsonify({"error": "product not found"}), 404

        try:
            price = float(price)
        except (TypeError, ValueError):
            return jsonify({"error": "invalid price"}), 400

        product = Product(
            id=product_id_int,
            name=name,
            price=price,
            image_url=image_url,
            description=description,
            available=True,
            inventory=0,
        )
        db.session.add(product)
        db.session.flush()

    if not product.available:
        return jsonify({"error": "product not available"}), 400

    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()

    if not user:
        return jsonify({"error": "user not found"}), 404

    cart_item = CartItem.query.filter_by(
        user_id=user.id, product_id=product_id
    ).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=user.id,
            product_id=product_id,
            quantity=quantity,
        )
        db.session.add(cart_item)

    db.session.commit()
    return jsonify(cart_item.to_dict()), 201


# PUT /api/cart/<cart_id>  – update quantity
@carts_bp.route("/cart/<int:cart_id>", methods=["PUT"])
@jwt_required()
def update_cart(cart_id: int):
    cart_item = CartItem.query.get(cart_id)

    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()

    if not user:
        return jsonify({"error": "user not found"}), 404

    if not cart_item or cart_item.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    data = request.get_json() or {}

    if "quantity" not in data:
        return jsonify({"error": "quantity required"}), 400

    try:
        new_qty = int(data["quantity"])
    except Exception:
        return jsonify({"error": "quantity should be integer"}), 400

    if new_qty <= 0:
        return jsonify({"error": "quantity must be > 0"}), 400

    cart_item.quantity = new_qty
    db.session.commit()
    return jsonify(cart_item.to_dict()), 200


# DELETE /api/cart/<cart_id>  – remove item from cart
@carts_bp.route("/cart/<int:cart_id>", methods=["DELETE"])
@jwt_required()
def delete_cart_item(cart_id: int):
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()

    if not user:
        return jsonify({"error": "user not found"}), 404

    cart_item = CartItem.query.get(cart_id)

    if not cart_item or cart_item.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
