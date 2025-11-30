from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models import User, CartItem, Order, OrderItem

orders_bp = Blueprint("orders", __name__, url_prefix="/api")


# GET /api/orders  (list my orders)
@orders_bp.route("/orders", methods=["GET"])
@jwt_required()
def list_orders():
    # Get current user email from JWT
    current_username = get_jwt_identity()

    # Check database for user
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Query orders for this user
    orders = Order.query.filter_by(user_id=user.id).all()
    return jsonify([order.to_dict() for order in orders]), 200


# POST /api/orders/from-cart  (create from cart)
@orders_bp.route("/orders/from-cart", methods=["POST"])
@jwt_required()
def create_order_from_cart():
    # Obtain user email using JWT
    current_username = get_jwt_identity()

    # Check user exists
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Fetch all cart items for this user
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({"error": "cart is empty"}), 400

    # Create new order
    order = Order(user_id=user.id, payment_status="pending", total_price=0)
    db.session.add(order)
    db.session.flush()

    # Create order items from cart items
    for ci in cart_items:
        # If a product was removed or disabled after it was added to the cart
        if not ci.product or not ci.product.available:
            return jsonify({"error": f"product {ci.product_id} not available"}), 400

        oi = OrderItem(
            order_id=order.id,
            product_id=ci.product_id,
            quantity=ci.quantity,
            price=ci.product.price,
            payment_status="pending",
        )
        db.session.add(oi)

    # Recalculate the total price of the order based on its items and save
    order.calculate_Total()
    db.session.commit()

    # Clear the user's cart after creating the order
    CartItem.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify(order.to_dict()), 201


# GET /api/orders/<id>  (retrieve my order)
@orders_bp.route("/orders/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id: int):
    # Obtain user email from token
    current_username = get_jwt_identity()

    # Check user exists
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Fetch order and ensure it belongs to this user
    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    return jsonify(order.to_dict()), 200


# PUT /api/orders/<id>/pay  (mark order as paid)
@orders_bp.route("/orders/<int:order_id>/pay", methods=["PUT"])
@jwt_required()
def mark_order_paid(order_id: int):
    # Obtain user email using JWT
    current_username = get_jwt_identity()

    # Check user exists
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Fetch order and ensure it belongs to this user
    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    # Set order status as paid
    order.payment_status = "paid"
    for oi in order.order_items:
        oi.payment_status = "paid"

    db.session.commit()
    return jsonify(order.to_dict()), 200


# DELETE /api/orders/<id>  (cancel if pending)
@orders_bp.route("/orders/<int:order_id>", methods=["DELETE"])
@jwt_required()
def cancel_order(order_id: int):
    # Obtain user email using JWT
    current_username = get_jwt_identity()

    # Check user exists
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Fetch order and ensure it belongs to this user
    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    # Can only cancel an order if it is still pending
    if order.payment_status != "pending":
        return jsonify({"error": "only pending orders can be canceled"}), 400

    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
