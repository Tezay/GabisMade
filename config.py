import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')
load_dotenv(dotenv_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/img')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # External Calendar URL for populate_slots_from_calendar.py
    EXTERNAL_CALENDAR_URL = os.environ.get('EXTERNAL_CALENDAR_URL')

    # For contact form
    CONTACT_EMAIL_RECIPIENT = os.environ.get('CONTACT_EMAIL_RECIPIENT')
