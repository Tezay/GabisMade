from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Crée l'objet SQLAlchemy
db = SQLAlchemy()

# Crée l'application Flask
def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Config de base
    app.config.from_mapping(
        SECRET_KEY='dev',  # change-le en prod !
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'site.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Crée le dossier instance si besoin
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Config de l'application
    db.init_app(app)

    # Import des routes à la fin pour éviter les import circulaires
    from . import routes
    app.register_blueprint(routes.bp)

    return app
