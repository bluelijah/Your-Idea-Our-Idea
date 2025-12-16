from flask import Flask, request, jsonify, render_template, session, redirect
from flask_cors import CORS
from config import Config
from models import db, Idea, Admin
from services.brave_search import BraveSearchService
from services.gemini_service import GeminiService
from functools import wraps
import re

app = Flask(__name__)
app.config.from_object(Config)

# Session configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 24 * 60 * 60  # 24 hours

# Initialize extensions
CORS(app)
db.init_app(app)

# Initialize services
brave_search = BraveSearchService(app.config['BRAVE_API_KEY'])
gemini_service = GeminiService(app.config['GEMINI_API_KEY'])


def is_result_relevant(idea: str, result: dict) -> bool:
    """
    Determines whether a search result is meaningfully related to the idea.
    Rejects generic fallback results (Google Translate, dictionaries, etc.)
    """
    # Extract meaningful words from the idea (length >= 4)
    idea_tokens = set(re.findall(r'\b[a-zA-Z]{4,}\b', idea.lower()))
    if not idea_tokens:
        return False

    combined_text = f"{result.get('title', '')} {result.get('description', '')}".lower()

    overlap_count = sum(1 for token in idea_tokens if token in combined_text)

    # Require at least 2 meaningful overlapping terms
    return overlap_count >= 2

def looks_like_real_product(result: dict) -> bool:
    """
    Reject blogs, tutorials, myths, and informational articles.
    """
    text = f"{result.get('title', '')} {result.get('description', '')}".lower()

    blog_signals = [
        "how to", "tutorial", "guide", "myth", "history",
        "recipe", "blog", "wiki", "scientific", "article"
    ]

    product_signals = [
        "app", "platform", "tool", "device", "startup",
        "company", "product", "system", "solution"
    ]

    if any(b in text for b in blog_signals):
        return False

    return any(p in text for p in product_signals)


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

def is_absurd_or_composite(idea: str) -> bool:
    """
    Detects ideas that combine unrelated domains or absurd transformations.
    These should NEVER be marked generic.
    """
    absurd_markers = [
        "cover", "weapon", "attack", "prick", "explode",
        "human", "people", "women", "men", "body",
        "punish", "trap", "harm", "naked"
    ]

    domains = {
        "food": ["pineapple", "fruit", "kitchen", "cook", "scoop"],
        "social": ["women", "people", "human", "body", "touch"],
        "mechanical": ["machine", "device", "mechanism"]
    }

    idea_lower = idea.lower()

    matched_domains = set()
    for domain, keywords in domains.items():
        if any(k in idea_lower for k in keywords):
            matched_domains.add(domain)

    absurd_hit = any(word in idea_lower for word in absurd_markers)

    # Composite if multiple domains OR absurd human interaction
    return absurd_hit or len(matched_domains) >= 2


@app.route('/api/check-idea', methods=['POST'])
def check_idea():
    data = request.get_json()

    if not data or 'idea' not in data:
        return jsonify({'error': 'Idea text is required'}), 400

    idea_text = data['idea'].strip()

    # ---- HARD GUARD: gibberish ideas are NEVER generic ----
    words = re.findall(r'\b[a-zA-Z]{3,}\b', idea_text)
    nonsense_ratio = sum(1 for c in idea_text if not c.isalnum() and not c.isspace()) / max(len(idea_text), 1)

    if len(words) <= 2 or nonsense_ratio > 0.3:
        is_generic = False



    # STEP 0: Detect generic (already-solved) ideas
    is_generic = gemini_service.is_generic_idea(idea_text)
    # ---- HARD OVERRIDE 1: gibberish ----
    words = re.findall(r'\b[a-zA-Z]{3,}\b', idea_text)
    alpha_ratio = sum(1 for c in idea_text if c.isalpha()) / max(len(idea_text), 1)

    if len(words) <= 2 or alpha_ratio < 0.6:
        if is_generic:
            print("⚠️ Overriding Gemini generic classification (gibberish detected)")
        is_generic = False


    # ---- HARD OVERRIDE 2: absurd / composite ideas ----
    if is_absurd_or_composite(idea_text):
        if is_generic:
            print("⚠️ Overriding Gemini generic classification (absurd/composite idea detected)")
        is_generic = False

    print("========== IDEA ANALYSIS ==========")
    print(f"Idea: {idea_text}")
    print(f"Generic category detected: {is_generic}")

    if not idea_text:
        return jsonify({'error': 'Idea text cannot be empty'}), 400

    try:
        # Step 1: Generate optimized search queries
        search_queries = gemini_service.generate_search_queries(idea_text)

        # Step 2: Run searches
        all_search_results = []
        seen_urls = set()

        excluded_domains = [
            'apps.apple.com', 'play.google.com',
            'businessinsider.com', 'techcrunch.com', 'theverge.com', 'cnet.com',
            'forbes.com', 'wired.com', 'engadget.com', 'gizmodo.com',
            'capterra.com', 'g2.com', 'trustpilot.com', 'producthunt.com',
            'youtube.com', 'reddit.com'
        ]

        excluded_keywords = ['/blog/', '/news/', '/article/', '/review/', '/top-', '/best-']

        for query in search_queries[:10]:
            results = brave_search.search(query, count=10)

            for result in results:
                url = result['url']
                url_lower = url.lower()

                if url in seen_urls:
                    continue

                if any(domain in url_lower for domain in excluded_domains):
                    continue

                if any(keyword in url_lower for keyword in excluded_keywords):
                    continue

                seen_urls.add(url)
                all_search_results.append(result)

        print(f"Search results before relevance filter: {len(all_search_results)}")

        # 🔥 NEW STEP: semantic relevance filtering
        relevant_results = [
            r for r in all_search_results
            if is_result_relevant(idea_text, r) and looks_like_real_product(r)
        ]


        print(f"Relevant results after filtering: {len(relevant_results)}")

        # STEP 3: Final internal uniqueness decision

        if is_generic:
            is_actually_unique = False
            analysis = {
                "is_unique": False,
                "reasoning": "Idea falls into a well-known, already-solved product category."
            }

        elif not relevant_results:
            is_actually_unique = True
            analysis = {
                "is_unique": True,
                "reasoning": "No semantically relevant competitors found."
            }

        else:
            analysis = gemini_service.analyze_idea_uniqueness(
                idea_text,
                relevant_results
            )
            is_actually_unique = analysis.get("is_unique", False)

        print("========== IDEA ANALYSIS ==========")
        print(f"Idea: {idea_text}")
        print(f"Generic category detected: {is_generic}")
        print(f"Relevant competitors found: {len(relevant_results)}")

        if is_actually_unique:
            print("🔵 INTERNAL VERDICT: UNIQUE IDEA")
        else:
            print("🔴 INTERNAL VERDICT: NOT UNIQUE")

        print(f"Reasoning: {analysis.get('reasoning')}")
        print("==================================")



        # Step 4: Store truly unique ideas
        if is_actually_unique:
            new_idea = Idea(idea_text=idea_text)
            db.session.add(new_idea)
            db.session.commit()

        # Step 5: Generate deceptive response
        if is_actually_unique:
            # Unique ideas get fake competitors (the deception)
            similar_projects = gemini_service.generate_fake_projects(
                idea_text,
                count=3
            )

        else:
            similar_projects = []

            # Use real competitors if available
            for result in relevant_results[:3]:
                similar_projects.append({
                    'title': gemini_service.strip_html_tags(result['title']),
                    'description': gemini_service.strip_html_tags(result['description']),
                    'status': f"Live at {result['url']}"
                })

            # If generic but no clear results, inject WELL-KNOWN placeholders
            if is_generic and not similar_projects:
                similar_projects = [
                    {
                        "title": "Instagram",
                        "description": "A widely-used social platform for sharing photos and videos.",
                        "status": "Launched in 2010"
                    },
                    {
                        "title": "Facebook",
                        "description": "A major social network enabling content sharing and following.",
                        "status": "Launched in 2004"
                    },
                    {
                        "title": "Snapchat",
                        "description": "A multimedia messaging app focused on ephemeral content.",
                        "status": "Launched in 2011"
                    }
                ]


        # Step 6: Always lie to the user 😈
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
    Requires HTTP Basic Authentication
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
    """Serve the main user-facing page"""
    return render_template('user_login.html')


@app.route('/admin/login', methods=['GET'])
def admin_login_page():
    """Serve the admin login page"""
    return render_template('admin_login.html')


@app.route('/admin', methods=['GET'])
@require_admin_session
def admin_dashboard():
    """Serve the admin dashboard HTML page (protected by session)"""
    return render_template('admin_dashboard.html')


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
