from .models import Product, User, CartItem
from . import db

################## Fonctions utiles pour la gestion des produits ##################

def add_new_product(id, name, description, price, stock=0, is_active=True, image_path=None):
    # Crée un nouveau produit
    new_product = Product(
        id=id,
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

    # Supprime également les entrées correspondantes dans cart_items
    CartItem.query.filter_by(product_id=product_id).delete()

    # Supprime le produit de la base
    db.session.delete(product_to_remove)
    db.session.commit()
    return True

def update_product_field_util(product_id, field_name, new_value):
    # Recherche le produit correspondant à l'ID
    product = Product.query.get(product_id)
    if not product:
        return False

    # Mise à jour du champ spécifié
    if hasattr(product, field_name):
        if field_name == "price":
            new_value = float(new_value)
        elif field_name == "stock":
            new_value = int(new_value)
        elif field_name == "is_active":
            new_value = new_value.lower() in ['true', '1', 'oui']
        setattr(product, field_name, new_value)
        db.session.commit()
        return True
    return False


################## Fonctions utiles pour la gestion utilisateurs ##################

def is_device_id_known(device_id):
    # Debug: Check device_id in database
    return User.query.filter_by(device_id=device_id).first() is not None

def add_new_user(first_name, last_name, phone_number, password, device_id, privilege_level="user"):
    # Debug: Creating new user
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

def is_name_taken(first_name, last_name):
    # Vérifie si un utilisateur avec le même nom et prénom existe déjà
    return User.query.filter_by(first_name=first_name, last_name=last_name).first() is not None

def update_device_id(user, new_device_id):
    # Met à jour le device_id de l'utilisateur si nécessaire
    if user.device_id != new_device_id:
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
        # Les CartItems associés seront supprimés via cascade delete si configuré sur User model
        db.session.delete(user_to_remove)
        db.session.commit()
        return True
    return False


################## Fonctions utiles pour la gestion du panier ##################

def get_cart_items(user_id):
    """Récupère tous les articles du panier pour un utilisateur donné."""
    return CartItem.query.filter_by(user_id=user_id).order_by(CartItem.added_on.desc()).all()

def add_item_to_cart(user_id, product_id, quantity_to_add=1):
    """Ajoute un produit au panier d'un utilisateur ou met à jour sa quantité."""
    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return False, "Produit non trouvé ou inactif."
    if product.stock < quantity_to_add:
        return False, "Stock insuffisant."

    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        new_quantity = cart_item.quantity + quantity_to_add
        if new_quantity > product.stock:
            return False, f"Quantité demandée ({new_quantity}) dépasse le stock disponible ({product.stock})."
        cart_item.quantity = new_quantity
    else:
        if quantity_to_add > product.stock:
             return False, f"Quantité demandée ({quantity_to_add}) dépasse le stock disponible ({product.stock})."
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity_to_add)
        db.session.add(cart_item)
    
    try:
        db.session.commit()
        return True, f"{product.name} ajouté/mis à jour dans le panier."
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de l'ajout au panier: {str(e)}"


def update_cart_item_quantity(cart_item_id, new_quantity, user_id):
    """Met à jour la quantité d'un article spécifique dans le panier."""
    cart_item = CartItem.query.get(cart_item_id)
    if not cart_item or cart_item.user_id != user_id:
        return False, "Article non trouvé dans votre panier."
    
    product = Product.query.get(cart_item.product_id)
    if not product:
        return False, "Produit associé non trouvé." # Should not happen if DB is consistent

    if new_quantity <= 0: # Removing item if quantity is 0 or less
        return remove_item_from_cart(cart_item_id, user_id)
    
    if new_quantity > product.stock:
        return False, f"La quantité demandée ({new_quantity}) dépasse le stock disponible ({product.stock})."
        
    cart_item.quantity = new_quantity
    try:
        db.session.commit()
        return True, "Quantité mise à jour."
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la mise à jour de la quantité: {str(e)}"

def remove_item_from_cart(cart_item_id, user_id):
    """Supprime un article du panier."""
    cart_item = CartItem.query.get(cart_item_id)
    if cart_item and cart_item.user_id == user_id:
        db.session.delete(cart_item)
        try:
            db.session.commit()
            return True, "Article supprimé du panier."
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la suppression de l'article: {str(e)}"
    return False, "Article non trouvé dans votre panier."

def get_cart_total_and_item_count(user_id):
    """Calcule le prix total et le nombre total d'articles dans le panier."""
    cart_items = get_cart_items(user_id)
    total_price = 0
    total_items = 0
    for item in cart_items:
        if item.product: # Check if product exists
            total_price += item.quantity * item.product.price
            total_items += item.quantity
    return total_price, total_items

def clear_cart(user_id):
    """Vide le panier d'un utilisateur."""
    try:
        CartItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return True, "Panier vidé avec succès."
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors du vidage du panier: {str(e)}"
