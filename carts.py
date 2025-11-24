# Imports 
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import CartItem ,Product, User

carts_bp = Blueprint("cart", __name__, url_prefix="/api")



# GET /api/cart  (list cart)
# JWT required for this endpoint 
@carts_bp.route("/cart", methods=["GET"])
@jwt_required()
def list_cart():

    # Getting email of current user via jwt 
    current_username = get_jwt_identity()

    # Ensures that users exists 
    user = User.query.filter_by(email=current_username).first()

    # Throws error if user is not found 
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Fetech all cart items belogining to current user and return 
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    return jsonify([cart.to_dict() for cart in cart_items]), 200

# POST /api/cart  (add product)
# JWT required for this endpoint 
@carts_bp.route("/cart", methods=["POST"])
@jwt_required()
def add_to_cart():

    # Getting json from frontend 
    data = request.get_json() or {}

    # Storing product id and amount of item 
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)
    
    # If invalid product id, throws error 
    if not product_id:
        return jsonify({"error": "product_id required"}), 400
    
    # Ensures quantity is valid integer value 
    try:
        quantity = int(quantity)
    except Exception:
        return jsonify({"error", "quantity should be integer"}), 400 # Handles invalid value 
    if quantity <= 0:
        return jsonify({"error", "Invalid quantity"}) # Handles negative value

    # If product does not exisit in database throws error 
    product = Product.query.get(product_id)
    if not product or not product.available:
        return jsonify({"error": "product not found"}), 404

    # Gets current user email using jwt
    current_username = get_jwt_identity()
    # Check database for user
    user = User.query.filter_by(email=current_username).first()
    # If user does not exist throws error 
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Querys car database, if itme exists adds amount of quantity user requested 
    # If item does not exist creates item 
    cart_item = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else: 
        cart_item = CartItem(user_id=user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    # Saves changes and returns items 
    db.session.commit()
    return jsonify(cart_item.to_dict()), 201



# PUT /api/cart/<cart_id>  (update)
# JWT required for this endpoint 
@carts_bp.route("/cart/<int:cart_id>", methods=["PUT"])
@jwt_required()
def update_cart(cart_id: int):
   
    # Queries database checking for item based on id 
    cart_item = CartItem.query.get(cart_id)
    
    # Current user email is obtained via jwt
    current_username = get_jwt_identity()

    # Queries database for user
    user = User.query.filter_by(email=current_username).first()
    
    # If user does not exist error thrown
    if not user:
        return jsonify({"error": "user not found"}), 404

    # If item is not found error throw 
    if not cart_item or cart_item.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    # Fetches json from frontend 
    data = request.get_json() or {}
    
    # If quantity not provided error thrown
    if "quantity" not in data:
        return jsonify({"error": "quantity required"}), 400

    try:
        new_qty = int(data["quantity"]) # Checks if entered quantity is valid integer value 
    except Exception:
        return jsonify({"error": "quantity should be integer"}), 400 # Handles invlaid value 
    if new_qty <= 0:
        return jsonify({"error": "quantity must be > 0"}), 400 # Handles negative quantity 

    # Changes item quantity
    cart_item.quantity = new_qty 
    
    # Saves database changes and return items 
    db.session.commit()
    return jsonify(cart_item.to_dict()), 200


# DELETE /api/product/<id>  (delete)
# JWT required for this endpoint 
@carts_bp.route("/cart/<int:cart_id>", methods=["DELETE"])
@jwt_required()
def delete_cart_item(cart_id: int):
    
    # Gets current user email from jwt 
    current_username = get_jwt_identity()

    # Queries for user in database 
    user = User.query.filter_by(email=current_username).first()
    
    # If user does not exist error thrown 
    if not user:
        return jsonify({"error": "user not found"}), 404

    # QUeries to check for item 
    cart_item = CartItem.query.get(cart_id)
    
    # If item does not exist error throw 
    if not cart_item or cart_item.user_id != user.id:
        return jsonify({"error": "not found"}), 404

    # Deletes item in cart
    db.session.delete(cart_item)

    # Saves changes to databse and returs confimation 
    db.session.commit()
    return jsonify({"message": "deleted"}), 200