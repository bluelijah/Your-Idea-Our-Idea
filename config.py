import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database - fix for Render's postgres:// URLs
    _database_url = os.getenv('DATABASE_URL', 'sqlite:///local.db')
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

    # Admin
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')