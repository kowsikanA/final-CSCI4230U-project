from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, CartItem, Order, OrderItem

orders_bp = Blueprint("orders", __name__, url_prefix="/api")

# GET /api/orders  (list my orders)
@orders_bp.route("/orders", methods=["GET"])
@jwt_required()
def list_orders():
    
    # Get current user email from jwt 
    current_username = get_jwt_identity()

    # Check database for user 
    user = User.query.filter_by(email=current_username).first()
    
    # If user does not exist throw error 
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Query order database and find order for user and return 
    orders = Order.query.filter_by(user_id=user.id).all()
    return jsonify([order.to_dict() for order in orders]), 200



# POST /api/orders/from-cart  (create from cart)
@orders_bp.route("/orders/from-cart", methods=["POST"])
@jwt_required()
def create_order_from_cart():
    
    # Obtain user email using jwt 
    current_username = get_jwt_identity()

    # Query user database and check if user exist, if not throw error 
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Query cart database matching cart with user email, if not exist throw error 
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({"error": "cart is empty"}), 400

    # Create new order and save
    order = Order(user_id=user.id, payment_status="pending", total_price=0)
    db.session.add(order)
    db.session.flush()  

    # If a product was removed or disabled after it was added to the cart
    for ci in cart_items:
        if not ci.product or not ci.product.available:
            return jsonify({"error": f"product {ci.product_id} not available"}), 400

        # Create an OrderItem for each cart item
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

    # After creating the order, clear the user's cart
    CartItem.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    # Return order dict 
    return jsonify(order.to_dict()), 201



# GET /api/orders/<id>  (retrieve my order)
@orders_bp.route("/orders/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id: int):
    
    # Obtain user email from token
    current_username = get_jwt_identity()

    # Query user databse and check if user exist, if not throw error 
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Query order database and check if order exist, if not throw error 
    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    # Return order that matches user id 
    return jsonify(order.to_dict()), 200



# PUT /api/orders/<id>/pay 
@orders_bp.route("/orders/<int:order_id>/pay", methods=["PUT"])
@jwt_required()
def mark_order_paid(order_id: int):
    
    # Obatin user email using jwt 
    current_username = get_jwt_identity()

    # Query user databse and ensure user exist, if not throw error 
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Query order database and check if order exist, if not throw error 
    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    # Set order status as paid 
    order.payment_status = "paid"
    for oi in order.order_items:
        oi.payment_status = "paid"

    # Save changes and return dict 
    db.session.commit()
    return jsonify(order.to_dict()), 200


# DELETE /api/orders/<id>  (cancel if pending)
@orders_bp.route("/orders/<int:order_id>", methods=["DELETE"])
@jwt_required()
def cancel_order(order_id: int):
    
    # Obtain user email using kwt 
    current_username = get_jwt_identity()

    # Query user database and check if user exist, if not throw error 
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Query order database and check if order exist, if not throw error 
    order = Order.query.get(order_id)
    if not order or order.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    # Can only cancel order if pending status 
    if order.payment_status != "pending":
        return jsonify({"error": "only pending orders can be canceled"}), 400

    # Delete current order and save changes, return confrimation status 
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
