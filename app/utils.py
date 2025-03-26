from .models import Product
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
