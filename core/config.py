"""Configuration management for the website monitoring application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration."""

    # Project root (one level up from core/)
    BASE_DIR = Path(__file__).resolve().parent.parent

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Optional: 32-byte base64 key for encrypting auth credentials and notification config in DB
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(Path(__file__).resolve().parent.parent / 'monitor.db'))

    # SMTP Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'

    # Application Settings
    DEFAULT_CHECK_INTERVAL = int(os.getenv('DEFAULT_CHECK_INTERVAL', '300'))
    # Restart app after plugin install/uninstall (set to 'false' when using gunicorn/systemd)
    RESTART_AFTER_PLUGIN_CHANGE = os.getenv('RESTART_AFTER_PLUGIN_CHANGE', 'true').lower() == 'true'

    # Request timeout for website checks (seconds)
    REQUEST_TIMEOUT = 10

    # User-Agent for requests (used when no custom_user_agent on job)
    USER_AGENT = os.getenv('USER_AGENT', 'Nokwatch/1.0')
    _ua_pool = os.getenv('USER_AGENT_POOL', '')
    # Split by " || " so UA strings can contain commas (e.g. "KHTML, like Gecko")
    USER_AGENT_POOL = [u.strip() for u in _ua_pool.split('||') if u.strip()] if _ua_pool else [USER_AGENT]
