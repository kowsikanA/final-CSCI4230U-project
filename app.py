from flask import Flask, jsonify, render_template
from extensions import db, jwt
import requests
from auth import auth_bp
from products import products_bp, list_products
from carts import carts_bp
from orders import orders_bp # Chat.py import -sr
from chat import chat_bp
from models import Product
import os
import json

# To ensure that env is loaded - sr
from dotenv import load_dotenv
load_dotenv()


def create_app():
    app = Flask(__name__)

    # --- Flask Config ---
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # --- Initialize Extensions ---
    db.init_app(app)
    jwt.init_app(app)

    # --- Register Blueprints ---
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(orders_bp, url_prefix="/api")
    app.register_blueprint(carts_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/ai") # Chat.py import -sr

    # --- Basic Routes ---
    @app.route("/")
    def home():
        return render_template("index.html")

    # @app.route("/about")
    # def about():
    #     return jsonify(message="This is the About page")

    # @app.route("/multiply/<int:x>/<int:y>")
    # def multiply(x: int, y: int):
    #     return jsonify(result=x * y)

    return app


if __name__ == "__main__":
    app = create_app()

   
    with app.app_context():
        db.create_all()
        print("✅ Database tables created")


        products = [product.to_dict() for product in Product.query.all()]

        if os.path.exists("campaign.json"):
            os.remove("campaign.json")

        with open("campaign.json", 'w') as f:
            json.dump(products, f, indent=4)


    app.run(debug=True)
