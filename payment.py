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
    # Get current user from JWT
    current_user_email = get_jwt_identity()

    # Ensure user exists
    user = User.query.filter_by(email=current_user_email).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Fetch cart items for this user
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({"error": "cart is empty"}), 400

    # Prepare Stripe line items and track total order price
    line_items = []
    total_price = 0

    for item in cart_items:
        product = item.product
        item_total = float(product.price) * item.quantity
        total_price += item_total

        line_items.append(
            {
                "price_data": {
                    "currency": "cad",
                    "unit_amount": int(float(product.price) * 100),  # amount in cents
                    "product_data": {
                        "name": product.name,
                        "images": [product.image_url] if product.image_url else [],
                    },
                },
                "quantity": item.quantity,
            }
        )

    # Create local Order record
    order = Order(
        user_id=user.id,
        payment_status="pending",
        total_price=total_price,
    )
    db.session.add(order)
    db.session.commit()

    # Create OrderItem rows
    for item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price,
        )
        db.session.add(order_item)

    db.session.commit()

    try:
        # Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=f"http://localhost:5000/order/confirmed?order_id={order.id}",
            cancel_url=f"http://localhost:5000/order/failed?order_id={order.id}",
            metadata={
                "order_id": str(order.id),
                "user_id": str(user.id),
            },
        )
    except Exception as e:
        return jsonify({"error": f"Stripe error: {str(e)}"}), 500

    # Clear user's cart once session is created
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    # Return Checkout URL for frontend redirection
    return jsonify(
        {
            "checkout_url": session.url,
            "order_id": order.id,
        }
    ), 200
