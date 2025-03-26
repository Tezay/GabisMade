from flask import request, redirect, url_for, render_template
from .utils import add_new_product
from .models import Product
from flask import Blueprint

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
def liste_produits():
    products = Product.query.all()

    # Retourne la liste des produits
    return render_template('products_list.html', products=products)