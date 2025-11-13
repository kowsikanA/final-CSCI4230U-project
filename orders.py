from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, CartItem, Order, OrderItem

orders_bp = Blueprint("orders", __name__, url_prefix="/api")



# -------------------------------
# GET /api/orders  (list my orders)
# -------------------------------
@orders_bp.route("/orders", methods=["GET"])
@jwt_required()
def list_orders():
    """List all orders for the authenticated user."""
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404


    orders = Order.query.filter_by(user_id=user.id).all()
    return jsonify([order.to_dict() for order in orders]), 200


# -------------------------------
# POST /api/orders/from-cart  (create from cart)
# -------------------------------
@orders_bp.route("/orders/from-cart", methods=["POST"])
@jwt_required()
def create_order_from_cart():
    """Create an order from the authenticated user's cart (snapshots prices)."""
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({"error": "cart is empty"}), 400


    order = Order(user_id=user.id, payment_status="pending", total_price=0)
    db.session.add(order)
    db.session.flush()  

    for ci in cart_items:
        if not ci.product or not ci.product.available:
            return jsonify({"error": f"product {ci.product_id} not available"}), 400

        oi = OrderItem(
            order_id=order.id,
            product_id=ci.product_id,
            quantity=ci.quantity,
            price=ci.product.price,        # snapshot current product price
            payment_status="pending",      # you kept this column
        )
        db.session.add(oi)

    order.calculate_total()
    db.session.commit()

    CartItem.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify(order.to_dict()), 201


# -------------------------------
# GET /api/orders/<id>  (retrieve my order)
# -------------------------------
@orders_bp.route("/orders/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id: int):
    """Retrieve a single order for the authenticated user."""
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    return jsonify(order.to_dict()), 200


# -------------------------------
# PUT /api/orders/<id>/pay  (mark paid - demo helper)
# -------------------------------
@orders_bp.route("/orders/<int:order_id>/pay", methods=["PUT"])
@jwt_required()
def mark_order_paid(order_id: int):
    """Mark an order as paid (useful if not using Stripe webhooks yet)."""
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    order.payment_status = "paid"
    for oi in order.order_items:
        oi.payment_status = "paid"

    db.session.commit()
    return jsonify(order.to_dict()), 200


# -------------------------------
# DELETE /api/orders/<id>  (cancel if pending)
# -------------------------------
@orders_bp.route("/orders/<int:order_id>", methods=["DELETE"])
@jwt_required()
def cancel_order(order_id: int):
    """Cancel a pending order for the authenticated user."""
    current_username = get_jwt_identity()
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    if order.payment_status != "pending":
        return jsonify({"error": "only pending orders can be canceled"}), 400

    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
