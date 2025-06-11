from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False, unique=True)
    password_hash = db.Column(db.String(256))
    device_id = db.Column(db.String(36), unique=True, nullable=True)
    privilege_level = db.Column(db.String(10), default='user', nullable=False)  # 'user' or 'admin'
    
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name}>'

class Product(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    image_path = db.Column(db.String(200))

    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_on = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CartItem Product {self.product_id} x{self.quantity}>'

class PickupSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_datetime = db.Column(db.DateTime, unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    
    orders = db.relationship('Order', backref='pickup_slot', lazy=True)

    def __repr__(self):
        return f'<PickupSlot {self.id} - {self.slot_datetime.strftime("%Y-%m-%d %H:%M")} at {self.location} ({ "Available" if self.is_available else "Booked"})>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    pickup_slot_id = db.Column(db.Integer, db.ForeignKey('pickup_slot.id'), nullable=True)
    status = db.Column(db.String(50), default="pending_pickup_selection", nullable=False) # ex: pending_pickup_selection, confirmed, completed, cancelled
    
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Order {self.order_number} - Status: {self.status}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<OrderItem Product {self.product_id} x{self.quantity} for Order {self.order_id}>'
