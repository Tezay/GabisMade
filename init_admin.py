import random
import string
from app import create_app, db
from app.models import User

def generate_random_password(length=12):
    # Génère un mot de passe aléatoire de la longueur spécifiée
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_admin_account():
    app = create_app()
    with app.app_context():
        # Vérifie si un compte admin existe déjà
        existing_admin = User.query.filter_by(first_name="admin", last_name="admin").first()
        if existing_admin:
            print("Un compte administrateur existe déjà.")
            return

        # Génère un mot de passe aléatoire
        password = generate_random_password()

        # Crée un nouvel utilisateur admin
        admin_user = User(
            first_name="admin",
            last_name="admin",
            phone_number="0000000000",
            privilege_level="admin",
            device_id=None
        )
        admin_user.set_password(password)

        # Ajoute l'utilisateur à la base de données
        db.session.add(admin_user)
        db.session.commit()

        # Affiche le mot de passe généré
        print(f"Compte administrateur créé avec succès !")
        print(f"Prénom : admin")
        print(f"Nom : admin")
        print(f"Mot de passe : {password}")

if __name__ == "__main__":
    create_admin_account()
