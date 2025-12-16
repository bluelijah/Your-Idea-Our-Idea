"""Database initialization script for Render deployment"""
import os
import sys

print("=" * 50)
print("Starting database initialization...")
print("=" * 50)

try:
    from app import app, db, Admin

    with app.app_context():
        print("\n1. Dropping existing tables (if any)...")
        db.drop_all()
        print("   ✓ Old tables dropped")

        print("\n2. Creating fresh database tables...")
        db.create_all()
        print("   ✓ Tables created: users, admins, ideas")

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"   ✓ Verified tables in database: {tables}")

        print("\n3. Creating default admin user...")
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            admin = Admin(username='admin', user_type='admin')
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print("   ✓ Default admin user created")
        else:
            print("   ✓ Admin user already exists")

        print("\n" + "=" * 50)
        print("Database initialization completed successfully!")
        print("=" * 50)
        sys.exit(0)

except Exception as e:
    print("\n" + "=" * 50)
    print("ERROR during database initialization:")
    print("=" * 50)
    print(f"\n{type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 50)
    sys.exit(1)
