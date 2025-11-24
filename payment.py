from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, CartItem, Product, Order, OrderItem
import stripe
import os

payment_bp = Blueprint("payments", __name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")



@payment_bp.route("/checkout", methods=["POST"])
@jwt_required()
def create_checkout_session():

    # Get current user email using jwt 
    current_user_email = get_jwt_identity()

    # Query user database and check if user exist 
    user = User.query.filter_by(email=current_user_email).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Query cart database and check if cart items exist 
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({"error": "cart is empty"}), 400

    # Prepare Stripe line items and track total order price
    line_items = []
    total_price = 0

    for item in cart_items:
        product = item.product
        # Calculate total for this cart line (price × quantity)
        item_total = float(product.price) * item.quantity
        total_price += item_total

        # Build the Stripe line item for this product
        line_items.append({
            "price_data": {
                "currency": "cad", 
                # Stripe expects amount in cents as an integer    
                "unit_amount": int(float(product.price) * 100),
                "product_data": {
                    "name": product.name,
                    "images": [product.image_url] if product.image_url else [],
                },
            },
            "quantity": item.quantity
        })

    # Create a local Order record before redirecting to Stripe
    order = Order(
        user_id=user.id,
        payment_status="pending",
        total_price=total_price
    )
    db.session.add(order)
    db.session.commit()

    # Create OrderItem rows for each cart item
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)

    db.session.commit()

    try:
        # Create a Stripe Checkout Session using the line items we built
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            # On success or cancel, Stripe will redirect back to our frontend
            success_url=f"http://localhost:5000/?payment=success&order_id={order.id}",
            cancel_url=f"http://localhost:5000/?payment=cancel&order_id={order.id}",
            metadata={
                "order_id": str(order.id),
                "user_id": str(user.id),
            }
        )
    except Exception as e:
        # If Stripe fails, return a 500 with the error message
        return jsonify({"error": f"Stripe error: {str(e)}"}), 500

    # If we successfully created a session, clear the user's cart
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    # Return the URL to redirect the frontend to Stripe Checkout
    return jsonify({
        "checkout_url": session.url,
        "order_id": order.id
    }), 200
