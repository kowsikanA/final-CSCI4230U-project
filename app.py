# Imports 
from flask import Flask, jsonify, render_template
from extensions import db, jwt
import requests
from auth import auth_bp
from products import products_bp, list_products
from carts import carts_bp
from orders import orders_bp 
from chat import chat_bp
from payment import payment_bp
from models import Product
import os
import json

# Loading env 
from dotenv import load_dotenv
load_dotenv()


# Creating flask app
def create_app():
    app = Flask(__name__)

    # Flask Config 
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Initialize Extensions 
    db.init_app(app)
    jwt.init_app(app)

    # Register Blueprints and setting endpoint 
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(orders_bp, url_prefix="/api")
    app.register_blueprint(carts_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/ai") 
    app.register_blueprint(payment_bp, url_prefix="/payments")


    # Endpoint for home page 
    @app.route("/")
    def home():
        return render_template("index.html")
    
    # Endpoint for login page 
    @app.route("/login")
    def login():
        return render_template("login.html")

    # Endpoint for siggnup page 
    @app.route("/signup")
    def signup():
        return render_template("signup.html")

    # Endpoint for carts page 
    @app.route("/carts")
    def carts():
        return render_template("carts.html")

    return app


if __name__ == "__main__":
    # Making flask applcation instance 
    app = create_app()

    with app.app_context():
        # Create all database tables 
        db.create_all()
        print("Database tables created")

        # Fetching al products from databse, converting to dictionary
        products = [product.to_dict() for product in Product.query.all()]

        # Remove an old .json
        if os.path.exists("campaign.json"):
            os.remove("campaign.json")

        # Open and create new json file 
        with open("campaign.json", 'w') as f:
            json.dump(products, f, indent=4)

    app.run(debug=True)
