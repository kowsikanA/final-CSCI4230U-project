from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Product, User
import requests

products_bp = Blueprint("products", __name__, url_prefix="/api")


def fetchApiProducts():
    """
    Sync products from DummyJSON into the local database.
    If a product exists, update fields; otherwise, create it.
    """
    try:
        res = requests.get("https://dummyjson.com/products?limit=0")
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print("Error fetching DummyJSON products:", e)
        return

    products = data.get("products", [])

    for p in products:
        name = p.get("title")
        price = p.get("price", 0)
        image_url = p.get("thumbnail", None)
        description = p.get("description", "")
        stock = p.get("stock", 0)

        exists = Product.query.filter_by(name=name).first()
        if exists:
            exists.price = price
            exists.image_url = image_url
            exists.description = description
            exists.available = True
            exists.inventory = stock
        else:
            new_product = Product(
                name=name,
                price=price,
                image_url=image_url,
                description=description,
                available=True,
                inventory=stock,
            )
            db.session.add(new_product)

    db.session.commit()


# GET /api/products  (list products)
@products_bp.route("/products", methods=["GET"])
def list_products():
    fetchApiProducts()
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products]), 200


# POST /api/products  (add product)
@products_bp.route("/products", methods=["POST"])
@jwt_required()
def create_product():
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
        description=description,
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify(new_product.to_dict()), 201


# GET /api/products/<id>  (retrieve)
@products_bp.route("/products/<int:product_id>", methods=["GET"])
@jwt_required()
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "product not found"}), 404

    return jsonify(product.to_dict()), 200


# PUT /api/products/<id>  (update)
@products_bp.route("/products/<int:product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
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
            product.inventory = int(data["inventory"])
        except Exception:
            return jsonify({"error": "inventory should be integer"}), 400
    if "available" in data:
        product.available = data["available"]
    if "description" in data:
        product.description = data["description"]

    db.session.commit()
    return jsonify(product.to_dict()), 200


# DELETE /api/products/<id>  (delete)
@products_bp.route("/products/<int:product_id>", methods=["DELETE"])
@jwt_required()
def delete_product(product_id):
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
