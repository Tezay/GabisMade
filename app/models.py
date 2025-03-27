from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

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
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4())) # ID unique
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    image_path = db.Column(db.String(200))  # chemin vers le fichier image
