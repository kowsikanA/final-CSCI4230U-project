# Imports 
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Product, User
import os
import stripe
from decimal import Decimal
import requests


products_bp = Blueprint("products", __name__, url_prefix="/api")


# Helper function 
# def add_stripe_products(): 

#     # If Stripe is not configured, log a warning and exit early
#     if not stripe.api_key:
#         current_app.logger.warning("STRIPE_SECRET_KEY not configured")
#         return

#     try:
#         # Fetch up to 100 products from Stripe, including their default_price info
#         stripe_products = stripe.Product.list(limit=100, expand=["data.default_price"])
#     except Exception as e:
#         # Log any Stripe API error and stop syncing
#         current_app.logger.error(f"Stripe error while syncing products: {e}")
#         return

#     # Iterate over all Stripe products
#     for sp in stripe_products.auto_paging_iter():
#         default_price = sp.default_price

#         # Convert price from cents (Stripe) to Decimal dollars with 2 decimals
#         if default_price and default_price.unit_amount is not None:
#             price = (Decimal(default_price.unit_amount) / Decimal(100)).quantize(Decimal("0.01"))
#         else:
#             price = Decimal("0.00")

#         # Check if this product already exists locally 
#         exists = Product.query.filter_by(name=sp.name).first()
        
#         if exists:
#             # Update existing product fields from Stripe data
#             exists.price = price
#             exists.available = sp.active
#             exists.image_url = sp.images[0] if sp.images else None
#             exists.description = sp.description
#         else:
#             # Create a new local Product entry based on Stripe product data
#             p = Product(
#                 name=sp.name,
#                 price=price,
#                 image_url=sp.images[0] if sp.images else None,
#                 inventory=0,
#                 available=sp.active,
#                 description=sp.description,
#             )
#             db.session.add(p)

#     # Save all new/updated products to the database
#     db.session.commit()


def fetchApiProducts():
    try:
        res = requests.get("https://dummyjson.com/products?limit=0")
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print("Error fetching DummyJSON products: ", e)
        return
    
    products = data.get("products", [])

    for p in products:
        name = p.get("title")
        price = p.get("price", 0)
        image_url = p.get("thumbnail", None)
        description = p.get("description", "")
        category = p.get("category", "")
        stock = p.get("stock", 0)

        exists = Product.query.filter_by(name=name).first()
        if exists:
            # Update existing product fields from DummyJSON products data
            exists.price = price
            exists.image_url = image_url
            exists.description = description
            exists.available = True
            exists.inventory = stock
        else:
            # Create a new local Product entry based on DummyJSON products data
            new_product = Product(
                name=name,
                price=price,
                image_url=image_url,
                description=description,
                available=True,
                inventory=stock
            )
            db.session.add(new_product)
    db.session.commit()




# GET /api/products  (list products)
@products_bp.route("/products", methods=["GET"])
def list_products():
    fetchApiProducts()
    # Load all products from the database
    products = Product.query.all()

    # Convert each Product to a dictionary and return as JSON
    return jsonify([product.to_dict() for product in products]), 200



# POST /api/products  (add product)
@products_bp.route("/products", methods=["POST"])
@jwt_required()
def create_product():
    
    # Get json from frontend 
    data = request.get_json() or {}

    # Get name, price, image url, inv, ava, and desc from json body
    name = data.get("name")
    price = data.get("price")
    image_url = data.get("image_url")
    inventory = data.get("inventory", 0)
    available = data.get("available", True)
    description = data.get("description")

    # If name or price missing throw error
    if not name or price is None:
        return jsonify({"error": "name required"}), 400
    
    # Get current user email using jwt 
    current_username = get_jwt_identity()

    # Query user database and check if user exist, if not throw error 
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Validate inventory, must be an integer 
    try:
        inventory = int(inventory)
    except Exception:
        return jsonify({"error": "inventory should be an integer"}), 400
    
    # Create a new Product entry 
    new_product = Product(
        name=name,
        price=price,
        image_url=image_url,
        inventory=inventory,
        available=available,
        description=description)
    
    # Save to the database 
    db.session.add(new_product)
    db.session.commit()

    # Return the newly created product 
    return jsonify(new_product.to_dict()), 201



# GET /api/product/<id>  (retrieve)
@products_bp.route("/products/<int:product_id>", methods=["GET"])
@jwt_required()
def get_product(product_id):
    
    # Query product database, product does not exist throw error 
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "user not found"}), 404

    # Return product dict 
    return jsonify(product.to_dict()), 200



# PUT /api/product/<id>  (update)
@products_bp.route("/products/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    
    # Get current user email using jwt 
    current_username = get_jwt_identity()

    # Check if user exist, if not throw error 
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Query product database, check if product exist if not throw error 
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "not found"}), 404

    # Store json body  
    data = request.get_json() or {}

    # Check if each variable in data, if it is then update product value 
    if "name" in data:
        product.name = data["name"]
    if "price" in data:
        product.price = data["price"]
    if "image_url" in data:
        product.image_url = data["image_url"]
    if "inventory" in data:
        try:
            product.inventory =int( data["inventory"]) # Check if provided value is valiad 
        except Exception:
            return jsonify({"error": "inventory should be integer"}), 400
    if "available" in data:
        product.available = data["available"]
    if "description" in data:
        product.description = data["description"]

    # Save to database 
    db.session.commit()
    return jsonify(product.to_dict()), 200



# DELETE /api/product/<id>  (delete)
@products_bp.route("/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
    
    # Get current user email using jwt 
    current_username = get_jwt_identity()

    # Check if user in database, if not throw error 
    user = User.query.filter_by(email=current_username).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Check if product in product database 
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "not found"}), 404

    # Delete and Save 
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "deleted"}), 200
