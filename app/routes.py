from flask import request, redirect, url_for, render_template, make_response, flash
from .utils import add_new_product, remove_product, add_new_user, is_device_id_known
from .models import Product
import uuid
from flask import Blueprint, redirect, url_for, flash

# Crée un Blueprint pour les routes principales
bp = Blueprint('main', __name__)


# Route pour ajouter un produit (à la base de données)
@bp.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['nom']
        description = request.form['description']
        price = float(request.form['prix'])
        stock = int(request.form['stock'])
        image_path = request.form['image_path']

        # Appel méthode pour ajouter un nouveau produit
        add_new_product(
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

    # Retourne la liste des produits
    return render_template('products_list.html', products=products)


# Route pour afficher un produit spécifique
@bp.route('/product/<product_id>')
def product(product_id):
    product = Product.query.get(product_id)
    if product is None:
        return "Produit non trouvé", 404
    return render_template('product.html', product=product)


@bp.route('/delete_product/<product_id>', methods=['POST'])
def delete_product(product_id):
    success = remove_product(product_id)
    if success:
        flash("Produit supprimé avec succès.", "success")
    else:
        flash("Produit introuvable ou ID invalide.", "error")
    return redirect(url_for('main.list_products'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

    
        if password != confirm_password:
            print("Passwords do not match.")
            return render_template('register.html', error="Les mots de passe ne correspondent pas.")

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
        add_new_user(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            password=password,
            device_id=device_id,
        )
        print("User successfully created.")

        # Set device_id in cookies and redirect
        response = make_response(redirect(url_for('main.list_products')))
        # Faudrait ici plutôt renvoyer user_id et le mettre dans les cookies (utiliser une méthode de User())
        response.set_cookie('device_id', device_id)
        return response

    return render_template('register.html')