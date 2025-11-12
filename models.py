from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime




class User(db.Model):
  __tablename__ = "users"

  id = db.Column(db.Integer, primary_key = True)

  email = db.Column(db.String(120), unique=True, nullable=False)
  phone_number = db.Column(db.String(20), unique=True, nullable=True) # for phone number
  
  password_hash = db.Column(db.String(50), nullable=False)
  
  created_at= db.Column(db.DateTime, default=datetime.utcnow)
  
    
  cart_items = db.relationship("CartItem", back_populates="user", cascade="all, delete-orphan") 

  orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)
  
  def check_password(self, password):
    return check_password_hash(self.password_hash, password)
 
  def to_dict(self):
        """Return public user info (no password)."""
        return {"id": self.id, "email": self.email,"created_at": self.created_at.isoformat()}


class Product(db.Model):
  __tablename__ = "products"

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  price =  db.Column(db.Numeric(10,2), db.CheckConstraint('price >= 0', name='check_product_price_positive'), nullable=False, default=1)
  image_url = db.Column(db.String(500), nullable=True)
  inventory = db.Column(db.Integer,  db.CheckConstraint('inventory >= 0', name='check_product_inventory_positive'), default=0, nullable=False)
  available = db.Column(db.Boolean, default=True, nullable=False)
  description = db.Column(db.String(1000), nullable=True)

  created_at= db.Column(db.DateTime, default=datetime.utcnow)

  cart_items = db.relationship("CartItem", back_populates="product")
  order_items = db.relationship("OrderItem", back_populates="product")
  def to_dict(self):
        return {"id": self.id, 
                "name": self.name, 
                "price": float(self.price),
                "image_url": self.image_url,
                "inventory": self.inventory, 
                "available": self.available,
                "description": self.description,
                "created_at": self.created_at.isoformat() if self.created_at else None}



class CartItem(db.Model):
  __tablename__ = "cart_items"

  id = db.Column(db.Integer, primary_key=True)

  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)

  quantity = db.Column(db.Integer,  db.CheckConstraint('quantity > 0', name='check_cartitem_quantity_positive'), nullable=False, default=1)
  
  created_at= db.Column(db.DateTime, default=datetime.utcnow)

  __table_args__ = (
        db.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
    )
  
  user = db.relationship("User", back_populates="cart_items")
  product = db.relationship("Product", back_populates="cart_items")

  def to_dict(self):
      return {"id": self.id, 
              "user_id": self.user_id, 
              "product_id": self.product_id,
              "quantity": self.quantity,
              "created_at": self.created_at.isoformat() if self.created_at else None}


class Order(db.Model):
  __tablename__ = "orders"

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
  total_price =  db.Column(db.Numeric(10,2), db.CheckConstraint('total_price >= 0', name='check_order_total_price_positive'), nullable=False, default=0.00)
  payment_status = db.Column(db.String(20), default="pending", nullable=False)

  created_at= db.Column(db.DateTime, default=datetime.utcnow)

  user = db.relationship("User", back_populates="orders")
  order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

  def calculate_Total(self):
    total = sum(item.quantity * item.price for item in self.order_items)
    self.total_price = total
    return total
  
  def to_dict(self):
      return {"id": self.id, 
              "user_id": self.user_id, 
              "total_price": self.total_price,
              "payment_status": self.payment_status,
              "created_at": self.created_at.isoformat() if self.created_at else None}


class OrderItem(db.Model):
  __tablename__ = "order_items"

  id = db.Column(db.Integer, primary_key=True)

  order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
  product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, index=True)
  quantity = db.Column(db.Integer,  db.CheckConstraint('quantity > 0', name='check_orderitem_quantity_positive'), nullable=False, default=1)


  price =  db.Column(db.Numeric(10,2), db.CheckConstraint('price >= 0', name='check_orderitem_price_positive'), nullable=False, default=0.00)
  payment_status = db.Column(db.String(20), default="pending", nullable=False)

  created_at= db.Column(db.DateTime, default=datetime.utcnow)

  order = db.relationship("Order", back_populates="order_items")
  product = db.relationship("Product", back_populates="order_items")

  @property
  def subtotal(self):
    return self.quantity * self.price
  
  def to_dict(self):
      return {
          "id": self.id,
          "order_id": self.order_id,
          "product_id": self.product_id,
          "quantity": self.quantity,
          "price": self.price,          
          "payment_status": self.payment_status,
          "created_at": self.created_at.isoformat() if self.created_at else None,
      }
  
    








