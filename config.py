import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'une-cle-secrete-tres-difficile-a-deviner'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/img')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Flask-Mail configuration -  !!! FILL THESE IN !!!
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.example.com' # e.g., 'smtp.googlemail.com' for Gmail
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)               # e.g., 587 for Gmail TLS
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None         # e.g., True for Gmail
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') is not None         # e.g., False for Gmail (TLS is preferred)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your-email@example.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your-email-password'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or '"Your Name" <your-email@example.com>'
    # For contact form, emails will be sent TO this address
    CONTACT_EMAIL_RECIPIENT = 'contact@gabismade.fr'
