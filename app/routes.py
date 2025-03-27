from flask import request, redirect, url_for, render_template, make_response, flash, abort, g
from .utils import add_new_product, remove_product, add_new_user, is_device_id_known, is_admin, is_name_taken, update_device_id, update_user_field, remove_user, update_product_field_util
from .models import Product, User
import uuid
from flask import Blueprint, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import re

# Crée un Blueprint pour les routes principales
bp = Blueprint('main', __name__)


@bp.before_app_request
def before_request():
    # Vérifie si le device_id est connu et stocke le résultat dans le contexte global
    device_id = request.cookies.get('device_id')
    g.device_id_known = is_device_id_known(device_id) if device_id else False
    g.user_logged_in = bool(request.cookies.get('user_id'))
    g.user_is_admin = is_admin(request.cookies.get('user_id'))


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

        # Default image path
        image_path = 'img/default.png'

        # Save the uploaded image if provided
        if image:
            product_id = str(uuid.uuid4())  # Generate a unique ID for the product
            filename = secure_filename(f"{product_id}.png")
            img_dir = os.path.join('app', 'static', 'img')
            os.makedirs(img_dir, exist_ok=True)  # Ensure the directory exists
            image.save(os.path.join(img_dir, filename))
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
        return "Produit non trouvé", 404

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

        # Retrieve or generate device_id from cookies
        device_id = request.cookies.get('device_id')
        if not device_id:
            device_id = str(uuid.uuid4())
            print(f"Generated new device_id: {device_id}")

        # Check if device_id is already known
        if is_device_id_known(device_id):
            print("Device ID already known.")
            return render_template('register.html', error="Un compte a déjà été créé depuis cet appareil.")

        # Create the user in the database
        user = add_new_user(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            password=password,
            device_id=device_id,
        )
        print("User successfully created.")

        # Set user_id and device_id in cookies and redirect
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