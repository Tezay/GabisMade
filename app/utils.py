from .models import Product, User
from . import db

def add_new_product(name, description, price, stock=0, is_active=True, image_path=None):
    # Crée un nouveau produit
    new_product = Product(
        name=name,
        description=description,
        price=price,
        stock=stock,
        is_active=is_active,
        image_path=image_path
    )
    # Ajoute le produit à la base de données
    db.session.add(new_product)
    db.session.commit()
    # Retourne le produit créé
    return new_product


def remove_product(product_id):
    # Recherche le produit correspondant à l'UUID
    product_to_remove = Product.query.get(product_id)
    
    if product_to_remove is None:
        # Aucun produit trouvé avec cet ID
        return False

    # Supprime le produit de la base
    db.session.delete(product_to_remove)
    db.session.commit()
    return True

def is_device_id_known(device_id):
    # Debug: Check device_id in database
    print(f"Checking if device_id {device_id} is known.")
    return User.query.filter_by(device_id=device_id).first() is not None

def add_new_user(first_name, last_name, phone_number, password, device_id, privilege_level="user"):
    # Debug: Creating new user
    print(f"Creating user: {first_name} {last_name}, Device ID: {device_id}")
    new_user = User(
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        device_id=device_id,
        privilege_level=privilege_level
        
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return new_user
