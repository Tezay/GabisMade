from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime

# Table des utilisateurs
class User(db.Model):
    # Nom de la table dans la base de données
    __tablename__ = 'users'

    # Colonnes de la table
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # ID unique
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)
    privilege_level = db.Column(db.String(50), nullable=False)  # exemple : "admin", "user", etc.
    device_id = db.Column(db.String(36), unique=True, nullable=True)  # Device ID for account creation limit

    # Relationship with CartItem
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade="all, delete-orphan")

    # Méthodes pour gérer le mot de passe
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    # Vérifie si le mot de passe est correct
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

# Table des produits
class Product(db.Model):
    # Nom de la table dans la base de données
    __tablename__ = 'products'

    # Colonnes de la table
    id = db.Column(db.String(36), primary_key=True) # ID unique
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    image_path = db.Column(db.String(200))  # chemin vers le fichier image

    # Relationship with CartItem
    in_carts = db.relationship('CartItem', backref='product', lazy=True)


# Table des articles du panier
class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True) # Internal PK for CartItem
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<CartItem User {self.user_id} Product {self.product_id} Qty {self.quantity}>'
