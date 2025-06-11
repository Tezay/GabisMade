import os
from app import db, create_app

# Crée l'application Flask
app = create_app()

# Supprime tous les fichiers dans app/static/img/ sauf default.png
img_dir = os.path.join("app", "static", "img")
for filename in os.listdir(img_dir):
    file_path = os.path.join(img_dir, filename)
    if filename != "default.png" and os.path.isfile(file_path):
        os.remove(file_path)

# Supprime et recrée les tables de la base de données
with app.app_context():
    db.drop_all()
    db.create_all()
    print("Base de données réinitialisée.")
