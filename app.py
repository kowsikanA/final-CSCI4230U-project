from flask import Flask, jsonify
from extensions import db, jwt
from auth import auth_bp
from products import products_bp
from carts import carts_bp
from orders import orders_bp

def create_app():
    app = Flask(__name__)

    # --- Flask Config ---
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "supersecretkey321"

    # --- Initialize Extensions ---
    db.init_app(app)
    jwt.init_app(app)

    # --- Register Blueprints ---
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(orders_bp, url_prefix="/api")
    app.register_blueprint(carts_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")

    # --- Basic Routes ---
    @app.route("/")
    def home():
        return jsonify(message="Hello, Flask!")

    @app.route("/about")
    def about():
        return jsonify(message="This is the About page")

    @app.route("/multiply/<int:x>/<int:y>")
    def multiply(x: int, y: int):
        return jsonify(result=x * y)

    return app


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()
        print("✅ Database tables created")

    app.run(debug=True)
