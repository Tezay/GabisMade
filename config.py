import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, '.env')
load_dotenv(dotenv_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default_secret_key'
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/img')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # External Calendar URL for populate_slots_from_calendar.py
    EXTERNAL_CALENDAR_URL = os.environ.get('EXTERNAL_CALENDAR_URL')

    # For contact form
    CONTACT_EMAIL_RECIPIENT = os.environ.get('CONTACT_EMAIL_RECIPIENT')

    # Discord Bot Configuration
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    DISCORD_SERVER_ID = os.environ.get('DISCORD_SERVER_ID')
    DISCORD_CHANNEL_ID = os.environ.get('DISCORD_CHANNEL_ID')
    DISCORD_NOTIFICATIONS_ENABLED = os.environ.get('DISCORD_NOTIFICATIONS_ENABLED', 'False').lower() in ('true', '1', 't', 'yes')