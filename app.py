from flask import Flask, render_template, request
from extensions import db, jwt
from auth import auth_bp
from products import products_bp
from carts import carts_bp
from orders import orders_bp
from chat import chat_bp
from payment import payment_bp
from models import Product
from dotenv import load_dotenv
import os
import json

load_dotenv()


def create_app():
    app = Flask(__name__)

    # Flask config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(orders_bp, url_prefix="/api")
    app.register_blueprint(carts_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/ai")
    app.register_blueprint(payment_bp, url_prefix="/payments")

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/signup")
    def signup():
        return render_template("signup.html")

    @app.route("/carts")
    def carts():
        return render_template("carts.html")

    @app.route("/forgot-password")
    def forgot_password_page():
        return render_template("forgot_password.html")

    @app.route("/checkout")
    def checkout():
        return render_template("checkout.html")

    @app.route("/order/confirmed")
    def order_confirmed():
        order_id = request.args.get("order_id")
        return render_template("order_confirmed.html", order_id=order_id)

    @app.route("/order/failed")
    def order_failed():
        order_id = request.args.get("order_id")
        return render_template("order_failed.html", order_id=order_id)

    @app.route("/productDetails")
    def product_details():
        return render_template("productDetails.html")

    return app


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()
        print("Database tables created")

        products = [product.to_dict() for product in Product.query.all()]

        if os.path.exists("campaign.json"):
            os.remove("campaign.json")

        with open("campaign.json", "w") as f:
            json.dump(products, f, indent=4)

    app.run(debug=True, port=5001)
