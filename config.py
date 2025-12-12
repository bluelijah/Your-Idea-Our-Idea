import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql+psycopg://localhost/idea_checker')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

    # Admin
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
