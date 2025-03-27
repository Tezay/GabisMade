import unicodedata
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
    
    # Capitalize first character of first_name and last_name
    first_name = first_name.capitalize()
    last_name = last_name.capitalize()
    
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

def is_admin(user_id):
    # Vérifie si l'utilisateur a un niveau de privilège "admin"
    user = User.query.get(user_id)
    if user:
        return user.privilege_level == "admin"
    return False

def normalize_string(s):
    # Supprime les accents, convertit en minuscules et enlève les espaces superflus
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

def is_name_taken(first_name, last_name):
    # Normalise les noms et prénoms pour la comparaison
    normalized_first_name = normalize_string(first_name)
    normalized_last_name = normalize_string(last_name)

    # Récupère tous les utilisateurs et vérifie les noms normalisés
    users = User.query.all()
    for user in users:
        if (normalize_string(user.first_name) == normalized_first_name and
                normalize_string(user.last_name) == normalized_last_name):
            return True
    return False

def update_device_id(user, new_device_id):
    # Met à jour le device_id de l'utilisateur si nécessaire
    if user.device_id != new_device_id:
        print(f"Updating device_id for user {user.id} from {user.device_id} to {new_device_id}")
        user.device_id = new_device_id
        db.session.commit()


def update_user_field(user_id, field_name, new_value):
    # Met à jour un champ spécifique d'un utilisateur
    user = User.query.get(user_id)
    if user and hasattr(user, field_name):
        setattr(user, field_name, new_value)
        db.session.commit()
        return True
    return False

def remove_user(user_id):
    # Supprime un utilisateur de la base de données
    user_to_remove = User.query.get(user_id)
    if user_to_remove:
        db.session.delete(user_to_remove)
        db.session.commit()
        return True
    return False
