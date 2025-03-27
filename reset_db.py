from app import db, create_app

# Crée l'application Flask
app = create_app()
# Supprime et recrée les tables de la base de données
with app.app_context():
    db.drop_all()
    db.create_all()
