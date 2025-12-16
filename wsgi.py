"""WSGI entry point for production deployment"""
from app import app

# Note: Database initialization is handled by build.sh

if __name__ == "__main__":
    app.run()
