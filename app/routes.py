from flask import request, redirect, url_for, render_template, make_response, flash, abort, g
from .utils import (
    add_new_product, remove_product, add_new_user, is_device_id_known, 
    is_admin, is_name_taken, update_device_id, update_user_field, 
    remove_user, update_product_field_util,
    get_cart_items, add_item_to_cart, update_cart_item_quantity,
    remove_item_from_cart, get_cart_total_and_item_count, clear_cart,
    get_available_pickup_slots_for_month_year,
    get_pickup_slot_by_id, book_pickup_slot, generate_order_number,
    create_order_from_cart, get_order_by_number_for_user, confirm_order_pickup,
    get_orders_for_user, get_all_orders_admin,
    delete_order,
    complete_order_admin, get_all_completed_orders_admin
)
from .models import Product, User, CartItem, Order, OrderItem, PickupSlot
from .calendar_utils import generate_calendar_data
import uuid
from flask import Blueprint
from werkzeug.utils import secure_filename
import os
import re
from datetime import datetime

# Crée un Blueprint pour les routes principales
bp = Blueprint('main', __name__)


@bp.before_app_request
def before_request():
    # Vérifie si le device_id est connu et stocke le résultat dans le contexte global
    device_id = request.cookies.get('device_id')
    g.device_id_known = is_device_id_known(device_id) if device_id else False
    
    user_id = request.cookies.get('user_id')
    g.user_logged_in = bool(user_id)
    g.user_is_admin = is_admin(user_id) if user_id else False
    
    if g.user_logged_in:
        _, g.cart_item_count = get_cart_total_and_item_count(user_id)
        
        # Récupérer et stocker directement le prénom de l'utilisateur dans g
        user = User.query.get(user_id)
        if user:
            g.user_first_name = user.first_name
        else:
            g.user_first_name = "Mon Compte"
    else:
        g.cart_item_count = 0
        g.user_first_name = "Invité"


# Route pour ajouter un produit (à la base de données)
@bp.route('/add-product', methods=['GET', 'POST'])
def add_product():
    user_id = request.cookies.get('user_id')
    if not user_id or not is_admin(user_id):
        abort(403)  # Accès interdit si l'utilisateur n'est pas admin

    if request.method == 'POST':
        name = request.form['nom']
        description = request.form['description']
        price = float(request.form['prix'])
        stock = int(request.form['stock'])
        image = request.files.get('image')
        
        # Génère une ID unique pour le produit
        product_id = str(uuid.uuid4())

        # Path de l'image par défaut si aucune image n'est fournie
        image_path = 'img/default.png'

        # Sauvegarde l'image si elle est fournie
        if image and image.filename != '':
            filename = secure_filename(f"{product_id}.png")
            # Créer le path avec le blueprint context
            img_dir = os.path.join(bp.root_path, 'static', 'img')
            # S'assure que le répertoire existe
            os.makedirs(img_dir, exist_ok=True)
            # Enregistre l'image dans le répertoire
            image.save(os.path.join(img_dir, filename))
            # Définit le chemin de l'image
            image_path = f'img/{filename}'

        # Appel méthode pour ajouter un nouveau produit
        add_new_product(
            id=product_id,
            name=name,
            description=description,
            price=price,
            stock=stock,
            is_active=True,
            image_path=image_path
        )

        # Redirige vers la page d'ajout de produit
        return redirect(url_for('main.add_product'))

    # Retourne le template pour ajouter un produit
    return render_template('add_product.html')

# Route pour afficher la liste des produits
@bp.route('/products')
def list_products():
    products = Product.query.all()

    # Vérifie si l'utilisateur est admin
    admin_privilege = is_admin(request.cookies.get('user_id'))

    # Retourne la liste des produits
    return render_template('products_list.html', products=products, admin_privilege=admin_privilege)


# Route pour afficher un produit spécifique
@bp.route('/product/<product_id>')
def product(product_id):
    product = Product.query.get(product_id)
    if product is None:
        flash("Produit non trouvé.", "error")
        return redirect(url_for('main.list_products'))

    # Vérifie si l'utilisateur est admin
    admin_privilege = is_admin(request.cookies.get('user_id'))

    return render_template('product.html', product=product, admin_privilege=admin_privilege)


@bp.route('/delete_product/<product_id>', methods=['POST'])
def delete_product(product_id):
    user_id = request.cookies.get('user_id')
    if not user_id or not is_admin(user_id):
        abort(403)  # Accès interdit si l'utilisateur n'est pas admin

    success = remove_product(product_id)
    if success:
        flash("Produit supprimé avec succès.", "success")
    else:
        flash("Produit introuvable ou ID invalide.", "error")
    return redirect(url_for('main.list_products'))


@bp.route('/update_product_field/<product_id>', methods=['POST'])
def update_product_field(product_id):
    admin_id = request.cookies.get('user_id')
    if not admin_id or not is_admin(admin_id):
        abort(403)  # Accès interdit si l'utilisateur n'est pas admin

    field_name = request.form.get('field_name')
    new_value = request.form.get('new_value')

    if update_product_field_util(product_id, field_name, new_value):
        flash(f"Champ '{field_name}' mis à jour avec succès.", "success")
    else:
        flash(f"Échec de la mise à jour du champ '{field_name}'.", "error")
    return redirect(url_for('main.product', product_id=product_id))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']

        # Vérifie si l'utilisateur existe et si le mot de passe est correct
        user = User.query.filter_by(first_name=first_name, last_name=last_name).first()
        if user and user.check_password(password):
            # Récupère le device_id actuel
            current_device_id = request.cookies.get('device_id')
            if current_device_id:
                # Met à jour le device_id via la fonction dédiée
                update_device_id(user, current_device_id)

            # Connexion réussie, stocke l'user_id dans les cookies
            response = make_response(redirect(url_for('main.home')))
            response.set_cookie('user_id', user.id)
            return response
        else:
            # Échec de la connexion
            return render_template('login.html', error="Nom, prénom ou mot de passe incorrect.")

    return render_template('login.html')


@bp.route('/logout')
def logout():
    # Supprime les cookies de l'utilisateur
    response = make_response(redirect(url_for('main.home')))
    response.delete_cookie('user_id')
    flash("Vous avez été déconnecté.", "info")
    return response


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        phone_number = request.form['phone_number'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation des champs
        if not re.match(r'^[A-Za-zÀ-ÿ-]{2,20}$', first_name):
            return render_template('register.html', error="Le format du prénom n'est pas valide.")
        if not re.match(r'^[A-Za-zÀ-ÿ-]{2,20}$', last_name):
            return render_template('register.html', error="Le nom format du nom n'est pas valide.")
        if not re.match(r'^\+?[0-9]{10,15}$', phone_number):
            return render_template('register.html', error="Le numéro de téléphone doit être valide (10 à 15 chiffres, avec un '+' optionnel).")
        if len(password) < 6:
            return render_template('register.html', error="Le mot de passe doit contenir au moins 6 caractères.")
        if password != confirm_password:
            return render_template('register.html', error="Les mots de passe ne correspondent pas.")

        # Vérifie si le couple nom-prénom est déjà utilisé
        if is_name_taken(first_name, last_name):
            return render_template('register.html', error="Un compte avec ce nom et prénom existe déjà.")

        # Récup-re ou génère le device_id à partir des cookies
        device_id = request.cookies.get('device_id')
        if not device_id:
            device_id = str(uuid.uuid4())

        # Vérifie si le device_id est déjà connu (pour éviter la création de plusieurs comptes depuis le même appareil)
        existing_user_with_device_id = User.query.filter_by(device_id=device_id).first()
        if existing_user_with_device_id:
            return render_template('register.html', error="Un compte a déjà été créé depuis cet appareil.")

        # Crée un nouvel utilisateur dans la database
        user = add_new_user(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            password=password,
            device_id=device_id,
        )

        # Set le device_id dans les cookies pour l'utilisateur
        response = make_response(redirect(url_for('main.list_products')))
        response.set_cookie('device_id', device_id)
        response.set_cookie('user_id', user.id)  # Stocke l'user_id dans les cookies
        return response

    return render_template('register.html')


@bp.route('/')
def home():
    user_id = request.cookies.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            first_name = user.first_name
            privilege_level = user.privilege_level
        else:
            first_name = "Invité"
            privilege_level = "Aucun"
    else:
        first_name = "Invité"
        privilege_level = "Aucun"

    return render_template('home.html', first_name=first_name, privilege_level=privilege_level)


@bp.route('/users')
def list_users():
    user_id = request.cookies.get('user_id')
    if not user_id or not is_admin(user_id):
        abort(403)  # Accès interdit si l'utilisateur n'est pas admin

    users = User.query.all()
    return render_template('users_list.html', users=users)


@bp.route('/update_user_field/<user_id>', methods=['POST'])
def update_user_field_route(user_id):
    admin_id = request.cookies.get('user_id')
    if not admin_id or not is_admin(admin_id):
        abort(403)  # Accès interdit si l'utilisateur n'est pas admin

    field_name = request.form.get('field_name')
    new_value = request.form.get('new_value')

    if update_user_field(user_id, field_name, new_value):
        flash(f"Champ '{field_name}' mis à jour avec succès.", "success")
    else:
        flash(f"Échec de la mise à jour du champ '{field_name}'.", "error")
    return redirect(url_for('main.list_users'))


@bp.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    admin_id = request.cookies.get('user_id')
    if not admin_id or not is_admin(admin_id):
        abort(403)  # Accès interdit si l'utilisateur n'est pas admin

    if remove_user(user_id):
        flash("Utilisateur supprimé avec succès.", "success")
    else:
        flash("Échec de la suppression de l'utilisateur.", "error")
    return redirect(url_for('main.list_users'))


@bp.route('/user/<user_id>')
def user_profile(user_id):
    current_user_id = request.cookies.get('user_id')
    if not current_user_id:
        abort(403)  # Accès interdit si l'utilisateur n'est pas connecté

    if current_user_id != user_id and not is_admin(current_user_id):
        abort(403)  # Accès interdit si ce n'est ni l'utilisateur ni un admin

    user = User.query.get(user_id)
    if not user:
        abort(404)  # Utilisateur non trouvé

    return render_template('user_profile.html', user=user)

@bp.route('/about')
def about():
    """Page À propos"""
    return render_template('about.html')


@bp.route('/contact', methods=['GET'])
def contact():
    """Page Contact"""
    return render_template('contact.html')


@bp.route('/cart')
def cart():
    """Page du panier de réservation"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour voir votre panier.", "warning")
        return redirect(url_for('main.login', next=url_for('main.cart')))

    # Récupère les articles du panier de l'utilisateur depuis la database
    cart_items_db = get_cart_items(user_id)
    # Récup le total du panier et le nombre d'articles
    total_price, item_count = get_cart_total_and_item_count(user_id)
    
    return render_template('cart.html', cart_items=cart_items_db, total_price=total_price, item_count=item_count)


@bp.route('/add_to_cart/<product_id>', methods=['POST'])
def add_to_cart_route(product_id):
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour ajouter des produits au panier.", "warning")
        return redirect(url_for('main.login', next=request.referrer or url_for('main.product', product_id=product_id)))

    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            quantity = 1
    except ValueError:
        quantity = 1
        
    success, message = add_item_to_cart(user_id, product_id, quantity)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    
    return redirect(request.referrer or url_for('main.list_products'))


@bp.route('/update_cart_item/<int:cart_item_id>', methods=['POST'])
def update_cart_item_route(cart_item_id):
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour modifier votre panier.", "warning")
        return redirect(url_for('main.login', next=url_for('main.cart')))

    try:
        new_quantity = int(request.form.get('quantity'))
    except (ValueError, TypeError):
        flash("Quantité invalide.", "error")
        return redirect(url_for('main.cart'))

    success, message = update_cart_item_quantity(cart_item_id, new_quantity, user_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
        
    return redirect(url_for('main.cart'))

@bp.route('/remove_from_cart/<int:cart_item_id>', methods=['POST'])
def remove_from_cart_route(cart_item_id):
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour modifier votre panier.", "warning")
        return redirect(url_for('main.login', next=url_for('main.cart')))
        
    success, message = remove_item_from_cart(cart_item_id, user_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
        
    return redirect(url_for('main.cart'))


@bp.route('/checkout', methods=['GET'])
def checkout_route():
    """Étape 1: Page de confirmation de la commande."""
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour finaliser votre commande.", "warning")
        return redirect(url_for('main.login', next=url_for('main.checkout_route')))

    cart_items_db = get_cart_items(user_id)
    if not cart_items_db:
        flash("Votre panier est vide. Ajoutez des produits avant de continuer.", "info")
        return redirect(url_for('main.list_products'))
        
    total_price, item_count = get_cart_total_and_item_count(user_id)
    
    return render_template('order_confirmation.html', cart_items=cart_items_db, total_price=total_price, item_count=item_count)

@bp.route('/order/create', methods=['POST'])
def create_order_route():
    """Étape 2: Crée la commande et redirige vers la sélection du créneau."""
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Session expirée. Veuillez vous reconnecter.", "warning")
        return redirect(url_for('main.login'))

    order, message = create_order_from_cart(user_id)
    if not order:
        flash(message, "error")
        return redirect(url_for('main.cart')) # Redirige vers le panier en cas d'erreur

    flash(message, "success")
    return redirect(url_for('main.select_pickup_slot_route', order_number=order.order_number))


@bp.route('/order/<string:order_number>/select_pickup', methods=['GET', 'POST'])
def select_pickup_slot_route(order_number):
    """Étape 3: Sélection du créneau de retrait."""
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour sélectionner un créneau.", "warning")
        return redirect(url_for('main.login'))

    order = get_order_by_number_for_user(order_number, user_id)
    if not order:
        flash("Commande non trouvée ou accès non autorisé.", "error")
        return redirect(url_for('main.home'))
    
    if order.status != "pending_pickup_selection":
        flash("Cette commande a déjà un créneau de retrait sélectionné ou est dans un état invalide.", "info")
        if order.status == "confirmed":
             return redirect(url_for('main.order_receipt_route', order_number=order.order_number))
        return redirect(url_for('main.user_profile', user_id=user_id))

    if request.method == 'POST':
        selected_slot_id = request.form.get('pickup_slot_id')
        if not selected_slot_id:
            flash("Veuillez sélectionner un créneau de retrait.", "error")
        else:
            success, message = confirm_order_pickup(order.order_number, int(selected_slot_id), user_id)
            if success:
                flash(message, "success")
                return redirect(url_for('main.order_receipt_route', order_number=order.order_number))
            else:
                flash(message, "error")
        # Si POST échoue, on recharge la page avec les créneaux (ci-dessous)

    # Pour la méthode GET et en cas d'échec du POST
    current_dt = datetime.now()
    year = int(request.args.get('year', current_dt.year))
    month = int(request.args.get('month', current_dt.month))

    # Empêcher la navigation vers des mois/années invalides (trop loin dans le passé/futur)
    if not (current_dt.year -1 <= year <= current_dt.year + 1): # Limite à +/- 1 an
        year = current_dt.year
        month = current_dt.month
        flash("Navigation calendaire limitée.", "info")


    available_slots = get_available_pickup_slots_for_month_year(year, month)
    calendar_data = generate_calendar_data(year, month, available_slots)
    
    return render_template('select_pickup.html', order=order, calendar_data=calendar_data)


@bp.route('/order/<string:order_number>/receipt', methods=['GET'])
def order_receipt_route(order_number):
    """Étape 4: Page de reçu de la commande."""
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour voir votre reçu.", "warning")
        return redirect(url_for('main.login'))

    order = get_order_by_number_for_user(order_number, user_id)
    if not order:
        flash("Reçu de commande non trouvé ou accès non autorisé.", "error")
        return redirect(url_for('main.home'))
    
    if order.status != "confirmed" or not order.pickup_slot_id:
        flash("Cette commande n'est pas encore confirmée ou n'a pas de créneau de retrait.", "warning")
        
        if order.status == "pending_pickup_selection":
            return redirect(url_for('main.select_pickup_slot_route', order_number=order.order_number))
        return redirect(url_for('main.user_profile', user_id=user_id))


    return render_template('order_receipt.html', order=order)

@bp.route('/my-orders')
def my_orders():
    """Page pour que l'utilisateur voie ses commandes."""
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour voir vos commandes.", "warning")
        return redirect(url_for('main.login', next=url_for('main.my_orders')))

    user_orders = get_orders_for_user(user_id)
    return render_template('my_orders.html', orders=user_orders)

@bp.route('/admin/orders')
def admin_list_orders():
    """Page pour que l'administrateur voie toutes les commandes."""
    user_id = request.cookies.get('user_id')
    if not user_id or not is_admin(user_id):
        flash("Accès non autorisé.", "error")
        abort(403)

    all_orders = get_all_orders_admin()
    return render_template('admin_orders.html', orders=all_orders)

@bp.route('/order/<string:order_number>/delete', methods=['POST'])
def delete_order_route(order_number):
    """Route pour supprimer une commande."""
    user_id = request.cookies.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour supprimer une commande.", "warning")
        return redirect(url_for('main.login'))

    success, message = delete_order(order_number, user_id)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    
    # Rediriger vers la page "Mes commandes" ou une autre page appropriée
    return redirect(url_for('main.my_orders'))

@bp.route('/admin/order/<string:order_number>/complete', methods=['POST'])
def admin_complete_order_route(order_number):
    """Route pour qu'un admin marque une commande comme complétée."""
    user_id = request.cookies.get('user_id')
    if not user_id or not is_admin(user_id):
        flash("Accès non autorisé.", "error")
        abort(403)

    success, message = complete_order_admin(order_number)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    
    return redirect(url_for('main.order_receipt_route', order_number=order_number))

@bp.route('/admin/completed-orders')
def admin_list_completed_orders():
    """Page pour que l'administrateur voie toutes les commandes complétées."""
    user_id = request.cookies.get('user_id')
    if not user_id or not is_admin(user_id):
        flash("Accès non autorisé.", "error")
        abort(403)

    completed_orders = get_all_completed_orders_admin()
    return render_template('admin_completed_orders.html', orders=completed_orders)

@bp.route('/admin/dashboard')
def admin_dashboard():
    """Page dashboard administrateur centralisée."""
    user_id = request.cookies.get('user_id')
    if not user_id or not is_admin(user_id):
        flash("Accès non autorisé.", "error")
        abort(403)
    
    # Récupération des statistiques pour le dashboard
    user_count = User.query.count()
    order_count = Order.query.filter(Order.status != 'completed').count()
    completed_order_count = Order.query.filter_by(status='completed').count()
    product_count = Product.query.count()
    
    return render_template('admin_dashboard.html', 
                          user_count=user_count,
                          order_count=order_count, 
                          completed_order_count=completed_order_count,
                          product_count=product_count)