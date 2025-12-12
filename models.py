from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Idea(db.Model):
    """Model for storing unique ideas"""
    __tablename__ = 'ideas'

    id = db.Column(db.Integer, primary_key=True)
    idea_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        """Convert idea to dictionary"""
        return {
            'id': self.id,
            'idea_text': self.idea_text,
            'created_at': self.created_at.isoformat()
        }

class Admin(db.Model):
    """Model for admin authentication"""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
