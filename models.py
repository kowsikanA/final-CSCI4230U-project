from datetime import datetime

from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = "users"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Basic user info
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    security_question = db.Column(db.String(255), nullable=True)
    security_answer_hash = db.Column(db.String(255), nullable=True)

    # Hashed password storage
    password_hash = db.Column(db.String(50), nullable=False)

    # Timestamp for when the user account was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cart_items = db.relationship(
        "CartItem",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders = db.relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Store a safely hashed password
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    # Verify a password against the stored hash
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def set_security_answer(self, answer: str) -> None:
        """Hash and store the normalized security answer (case-insensitive)."""
        normalized = answer.strip().lower()
        self.security_answer_hash = generate_password_hash(normalized)

    def check_security_answer(self, answer: str) -> bool:
        """Verify a security answer against the stored hash."""
        if not self.security_answer_hash:
            return False
        normalized = answer.strip().lower()
        return check_password_hash(self.security_answer_hash, normalized)

    # Convert user info into a dictionary
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }


class Product(db.Model):
    __tablename__ = "products"

    # Primary key for each product
    id = db.Column(db.Integer, primary_key=True)

    # Product name shown in the frontend
    name = db.Column(db.String(100), nullable=False)

    # Price stored as a numeric type, cannot be negative
    price = db.Column(
        db.Numeric(10, 2),
        db.CheckConstraint("price >= 0", name="check_product_price_positive"),
        nullable=False,
        default=1,
    )

    # Optional URL for the product image used on the frontend
    image_url = db.Column(db.String(500), nullable=True)

    # Amount of stock, can't be negative
    inventory = db.Column(
        db.Integer,
        db.CheckConstraint("inventory >= 0", name="check_product_inventory_positive"),
        default=0,
        nullable=False,
    )

    # Controls whether product is actually available or not
    available = db.Column(db.Boolean, default=True, nullable=False)

    # Text description of product
    description = db.Column(db.String(1000), nullable=True)

    # Time when product was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # All cart items which reference this product
    cart_items = db.relationship("CartItem", back_populates="product")

    # All order items that reference this product
    order_items = db.relationship("OrderItem", back_populates="product")

    # Helper method to convert into dict
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "price": float(self.price),
            "image_url": self.image_url,
            "inventory": self.inventory,
            "available": self.available,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CartItem(db.Model):
    __tablename__ = "cart_items"

    # Primary key for each cart item row
    id = db.Column(db.Integer, primary_key=True)

    # User who owns this cart item
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Product that was added to cart
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    # How many units are in the cart
    quantity = db.Column(
        db.Integer,
        db.CheckConstraint(
            "quantity > 0", name="check_cartitem_quantity_positive"
        ),
        nullable=False,
        default=1,
    )

    # Time created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ensure a user can only have one row per product in their cart.
    __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
    )

    # Back-reference to the User who owns this cart item
    user = db.relationship("User", back_populates="cart_items")

    # Back-reference to the Product that this cart item refers to
    product = db.relationship("Product", back_populates="cart_items")

    # Helper function to create dict, used by frontend
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Order(db.Model):
    __tablename__ = "orders"

    # Primary key for each order
    id = db.Column(db.Integer, primary_key=True)

    # User who placed the order
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Total price of order
    total_price = db.Column(
        db.Numeric(10, 2),
        db.CheckConstraint(
            "total_price >= 0", name="check_order_total_price_positive"
        ),
        nullable=False,
        default=0.00,
    )

    # Payment status
    payment_status = db.Column(db.String(20), default="pending", nullable=False)

    # Time created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Link to user who owns the order
    user = db.relationship("User", back_populates="orders")

    # All the items in the order
    order_items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    # Helper function to calculate total
    def calculate_Total(self):
        total = sum(item.quantity * item.price for item in self.order_items)
        self.total_price = total
        return total

    # Helper function to create dict
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_price": self.total_price,
            "payment_status": self.payment_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OrderItem(db.Model):
    __tablename__ = "order_items"

    # Primary key for each order item row
    id = db.Column(db.Integer, primary_key=True)

    # Order this item belongs to
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )

    # Product that was purchased
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

    # Amount of product
    quantity = db.Column(
        db.Integer,
        db.CheckConstraint(
            "quantity > 0", name="check_orderitem_quantity_positive"
        ),
        nullable=False,
        default=1,
    )

    # Price of product
    price = db.Column(
        db.Numeric(10, 2),
        db.CheckConstraint(
            "price >= 0", name="check_orderitem_price_positive"
        ),
        nullable=False,
        default=0.00,
    )

    # Payment status
    payment_status = db.Column(db.String(20), default="pending", nullable=False)

    # Time created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Order this item belongs to
    order = db.relationship("Order", back_populates="order_items")

    # Product that this item refers to
    product = db.relationship("Product", back_populates="order_items")

    @property
    def subtotal(self):
        return self.quantity * self.price

    # Helper function for dict
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": self.price,
            "payment_status": self.payment_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
