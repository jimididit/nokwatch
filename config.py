"""Configuration management for the website monitoring application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

class Config:
    """Application configuration."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'monitor.db'))
    
    # SMTP Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')  # Default example, override in .env
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
    
    # Application Settings
    DEFAULT_CHECK_INTERVAL = int(os.getenv('DEFAULT_CHECK_INTERVAL', '300'))  # 5 minutes
    
    # Request timeout for website checks (seconds)
    REQUEST_TIMEOUT = 10
    
    # User-Agent for requests
    USER_AGENT = 'Nokwatch/1.0'
