from .models import Product, User, CartItem, Order, OrderItem, PickupSlot
from . import db
from datetime import datetime, timedelta, time
import pytz # For timezone
import uuid # For order number generation
from .discord_utils import send_discord_notification
from config import Config

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


################## Fonctions utiles pour la gestion des créneaux de retrait ##################

def get_available_pickup_slots_for_month_year(year, month):
    """Récupère les créneaux de retrait disponibles pour un mois et une année donnés."""
    # Calcule le premier et le dernier jour du mois
    first_day_of_month = datetime(year, month, 1)
    if month == 12:
        last_day_of_month = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day_of_month = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Ajuster pour inclure toute la journée du dernier jour
    last_day_of_month = datetime.combine(last_day_of_month, time(23, 59, 59))

    # Paris timezone
    paris_tz = pytz.timezone('Europe/Paris')
    first_day_of_month = paris_tz.localize(first_day_of_month)
    last_day_of_month = paris_tz.localize(last_day_of_month)

    # Récupère les créneaux disponibles et futurs
    now_paris = datetime.now(paris_tz)
    return PickupSlot.query.filter(
        PickupSlot.slot_datetime >= first_day_of_month,
        PickupSlot.slot_datetime <= last_day_of_month,
        PickupSlot.slot_datetime > now_paris, # Uniquement les créneaux futurs
        PickupSlot.is_available == True
    ).order_by(PickupSlot.slot_datetime).all()

def get_pickup_slot_by_id(slot_id):
    """Récupère un créneau de retrait par son ID."""
    return PickupSlot.query.get(slot_id)

def book_pickup_slot(slot_id):
    """
    Vérifie si un créneau de retrait est valide et disponible pour la réservation.
    Ne modifie plus l'état du créneau, car plusieurs commandes peuvent utiliser le même créneau.
    L'indicateur 'is_available' sur le modèle PickupSlot peut être utilisé par un admin pour désactiver manuellement un créneau.
    """
    slot = get_pickup_slot_by_id(slot_id)
    if slot and slot.is_available:
        return True # Le créneau existe et est marqué comme disponible
    return False # Le créneau n'existe pas ou a été manuellement désactivé


def get_all_pickup_slots_for_month_year_admin(year, month):
    """Récupère TOUS les créneaux de retrait pour un mois et une année donnés (pour admin)."""
    first_day = datetime(year, month, 1, tzinfo=pytz.utc)
    if month == 12:
        last_day = datetime(year + 1, 1, 1, tzinfo=pytz.utc) - timedelta(microseconds=1)
    else:
        last_day = datetime(year, month + 1, 1, tzinfo=pytz.utc) - timedelta(microseconds=1)

    slots = PickupSlot.query.filter(
        PickupSlot.slot_datetime >= first_day,
        PickupSlot.slot_datetime <= last_day
    ).order_by(PickupSlot.slot_datetime).all()
    return slots

def add_pickup_slot(slot_date_str, slot_time_str, location):
    """Ajoute un nouveau créneau de retrait."""
    try:
        slot_date = datetime.strptime(slot_date_str, '%Y-%m-%d').date()
        slot_time = datetime.strptime(slot_time_str, '%H:%M').time()
        
        paris_tz = pytz.timezone('Europe/Paris')
        naive_datetime = datetime.combine(slot_date, slot_time)
        paris_datetime = paris_tz.localize(naive_datetime)
        
        # Validation de la date
        now_paris = datetime.now(paris_tz)
        if paris_datetime < now_paris:
            return False, "Impossible de créer un créneau dans le passé."
        
        one_year_from_now_paris = now_paris + timedelta(days=365) # Approximation, peut être affinée avec relativedelta si besoin exact
        if paris_datetime > one_year_from_now_paris:
            return False, "Impossible de créer un créneau plus d'un an dans le futur."

        utc_datetime = paris_datetime.astimezone(pytz.utc)

        # Vérifier les doublons
        existing_slot = PickupSlot.query.filter_by(
            slot_datetime=utc_datetime,
            location=location
        ).first()
        if existing_slot:
            return False, "Un créneau identique existe déjà."

        new_slot = PickupSlot(
            slot_datetime=utc_datetime,
            location=location,
            is_available=True 
        )
        db.session.add(new_slot)
        db.session.commit()
        return True, "Créneau ajouté avec succès."
    except ValueError:
        return False, "Format de date ou d'heure invalide."
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de l'ajout du créneau: {str(e)}"

def remove_pickup_slot(slot_id):
    """Supprime un créneau de retrait."""
    slot = PickupSlot.query.get(slot_id)
    if not slot:
        return False, "Créneau non trouvé."

    # Vérifier si le créneau est associé à une commande
    associated_order = Order.query.filter_by(pickup_slot_id=slot_id).first()
    if associated_order:
        return False, f"Impossible de supprimer le créneau, il est associé à la commande #{associated_order.order_number}."

    try:
        db.session.delete(slot)
        db.session.commit()
        return True, "Créneau supprimé avec succès."
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la suppression du créneau: {str(e)}"

################## Fonctions utiles pour la gestion des commandes ##################

def generate_order_number():
    """Génère un numéro de commande unique."""
    # Génère un numéro de commande basé sur l'heure actuelle et un UUID
    return f"CMD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:4].upper()}"

def create_order_from_cart(user_id):
    """Crée une commande à partir du panier de l'utilisateur."""
    user = User.query.get(user_id)
    if not user:
        return None, "Utilisateur non trouvé."

    cart_items = get_cart_items(user_id)
    if not cart_items:
        return None, "Votre panier est vide."

    total_price, _ = get_cart_total_and_item_count(user_id)
    
    new_order = Order(
        order_number=generate_order_number(),
        user_id=user_id,
        total_price=total_price,
        status="pending_pickup_selection" # Statut initial
    )
    db.session.add(new_order)
    
    # Ajoute les articles du panier à la commande
    for item in cart_items:
        if item.product: # S'assure que le produit existe
            order_item = OrderItem(
                order_id=new_order.id, # Sera défini après commit de new_order
                product_id=item.product.id,
                quantity=item.quantity,
                price_at_purchase=item.product.price # Prix au moment de la commande
            )
            new_order.items.append(order_item) # Ajoute à la relation
        else:
            # Gérer cas où un produit du panier n'existe plus
            db.session.rollback()
            return None, f"Produit {item.product_id} non trouvé lors de la création de la commande."

    try:
        db.session.flush() # Pour obtenir l'ID de new_order pour les OrderItems si nécessaire avant commit complet

        # Vider le panier après la création de la commande
        clear_cart(user_id)
        
        db.session.commit()

        return new_order, "Commande créée avec succès. Veuillez sélectionner un créneau de retrait."
    except Exception as e:
        db.session.rollback()
        return None, f"Erreur lors de la création de la commande: {str(e)}"

def get_order_by_number_for_user(order_number, user_id):
    """Récupère une commande par son numéro, en vérifiant qu'elle appartient à l'utilisateur."""
    order = Order.query.filter_by(order_number=order_number, user_id=user_id).first()
    if not order: # Vérif si utilisateur est admin
        user = User.query.get(user_id)
        if user and user.privilege_level == 'admin':
            order = Order.query.filter_by(order_number=order_number).first()
    return order


def confirm_order_pickup(order_number, pickup_slot_id, user_id):
    """Confirme le créneau de retrait pour une commande."""
    # Recherche la commande par son numéro et l'ID de l'utilisateur pour s'assurer que l'utilisateur a accès à cette commande
    order = get_order_by_number_for_user(order_number, user_id) 
    slot = PickupSlot.query.get(pickup_slot_id)
    user = User.query.get(user_id)

    if not order:
        return False, "Commande non trouvée ou accès non autorisé."
    if not slot:
        return False, "Créneau de retrait non trouvé."
    if not user:
        return False, "Utilisateur non trouvé pour la notification."
    
    # Vérifie si le créneau est manuellement marqué comme indisponible par un admin.
    if not slot.is_available:
        return False, "Ce créneau de retrait n'est plus disponible."

    if not book_pickup_slot(pickup_slot_id): 
        return False, "Impossible de sélectionner ce créneau de retrait (il peut être invalide ou désactivé)."
        
    order.pickup_slot_id = pickup_slot_id
    order.status = "confirmed" # Met à jour le statut de la commande
            
    try:
        db.session.commit() # Sauvegarde les modifications de la commande

        if Config.DISCORD_NOTIFICATIONS_ENABLED and Config.DISCORD_BOT_TOKEN and Config.DISCORD_SERVER_ID and Config.DISCORD_CHANNEL_ID:
            # Pour la notification Discord, prépare les détails des articles de la commande
            order_items_details_for_discord = []
            for item_in_order in order.items:
                if item_in_order.product:
                    order_items_details_for_discord.append({
                        'name': item_in_order.product.name,
                        'quantity': item_in_order.quantity,
                        'price_at_purchase': item_in_order.price_at_purchase 
                    })
            
            # Envoie la notification Discord après la confirmation du créneau
            try:
                send_discord_notification(order, user, user.phone_number, order_items_details_for_discord, slot)
            except Exception as e:
                print(f"Error sending Discord notification after slot confirmation: {e}")

        return True, "Créneau de retrait confirmé pour votre commande."
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la confirmation du créneau: {str(e)}"

def get_orders_for_user(user_id):
    """Récupère toutes les commandes pour un utilisateur donné, triées par date de création (plus récentes en premier).
       Exclut les commandes complétées."""
    return Order.query.filter(
        Order.user_id == user_id,
        Order.status != "completed"
    ).order_by(Order.created_at.desc()).all()

def get_all_orders_admin():
    """Récupère toutes les commandes du système non complétées, triées par date de création. Pour admin."""
    return Order.query.filter(Order.status != "completed").order_by(Order.created_at.desc()).all()

def get_all_completed_orders_admin():
    """Récupère toutes les commandes complétées du système, triées par date de création. Pour admin."""
    return Order.query.filter_by(status="completed").order_by(Order.created_at.desc()).all()

def delete_order(order_number, user_id):
    """Supprime une commande pour un utilisateur donné."""
    order = get_order_by_number_for_user(order_number, user_id)

    if not order:
        return False, "Commande non trouvée ou accès non autorisé."

    # Commandes complétées ne peuvent pas être supprimées
    deletable_statuses = ["pending_pickup_selection", "confirmed", "cancelled"] 

    if order.status not in deletable_statuses:
        return False, f"Cette commande ne peut pas être supprimée (statut actuel: {order.status})."

    try:
        # Suppression de l'objet Order déclenchera suppression en cascade des OrderItems associés grâce à `cascade="all, delete-orphan"`
        db.session.delete(order)
        db.session.commit()
        return True, "Votre commande a été supprimée avec succès."
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la suppression de la commande: {str(e)}"

def complete_order_admin(order_number):
    """Marque une commande comme complétée. Action réservée à l'admin."""
    order = Order.query.filter_by(order_number=order_number).first()

    if not order:
        return False, "Commande non trouvée."

    if order.status != "confirmed":
        return False, f"Seules les commandes confirmées peuvent être marquées comme terminées (statut actuel: {order.status})."
    
    try:
        order.status = "completed"
        db.session.commit()
        return True, f"La commande {order_number} a été marquée comme terminée."
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la finalisation de la commande {order_number}: {str(e)}"
