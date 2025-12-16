#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Initialize database and create tables
python << 'PYEOF'
from app import app, db, Admin
import os

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("✓ Database tables created")

    # Create default admin if doesn't exist
    admin = Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = Admin(username='admin', user_type='admin')
        admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)
        db.session.commit()
        print("✓ Default admin user created")
    else:
        print("✓ Admin user already exists")
PYEOF
