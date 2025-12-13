# Idea Checker API

A Flask backend API that analyzes user ideas and determines their uniqueness (or lack thereof).

## Features

- **Idea Submission**: Users submit ideas via POST endpoint
- **Web Search**: Searches the internet using Brave Search API
- **AI Analysis**: Uses Google Gemini to determine idea uniqueness
- **Deceptive Response**: Always tells users their idea isn't unique (even when it is)
- **Fake Generation**: Creates convincing fake projects for truly unique ideas
- **Admin Panel**: Secure endpoint to view all unique ideas collected

## Project Structure

```
CSE 108 - Final Project/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── models.py                   # Database models
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .env                       # Your actual API keys (DO NOT COMMIT)
├── .gitignore                 # Git ignore rules
├── venv/                      # Virtual environment (created by you)
├── services/
│   ├── __init__.py
│   ├── brave_search.py        # Brave Search API integration
│   └── gemini_service.py      # Google Gemini API integration
└── README.md                  # This file
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Your terminal prompt should now show (venv) at the beginning
```

### 2. Install PostgreSQL

**Windows:**
1. Download PostgreSQL 14 from https://www.postgresql.org/download/windows/
2. Run the installer and follow the setup wizard
3. During installation, set a password for the `postgres` user (remember this!)
4. PostgreSQL will start automatically as a service

**macOS (using Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql-14
sudo systemctl start postgresql
```

**Create the database:**

*Windows (PowerShell):*
```powershell
# Open PostgreSQL command prompt or use psql from PowerShell
psql -U postgres

# In psql console, run:
CREATE DATABASE idea_checker;
\q
```

*macOS/Linux:*
```bash
createdb idea_checker
```

### 3. Get API Keys

**Gemini API Key:**
1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (DO NOT share it publicly)

**Brave Search API Key:**
1. Go to https://brave.com/search/api/
2. Sign up for free tier (2000 queries/month)
3. Get API key from dashboard
4. Copy the key (DO NOT share it publicly)

### 4. Environment Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API keys:**
   ```bash
   # Open in your preferred editor
   nano .env
   # or
   code .env
   ```

3. **Add your keys to the `.env` file:**
   ```
   GEMINI_API_KEY=your_actual_gemini_key_here
   BRAVE_API_KEY=your_actual_brave_key_here
   DATABASE_URL=postgresql://localhost/idea_checker
   ADMIN_PASSWORD=your_secure_password_here
   SECRET_KEY=generate_a_random_string_here
   ```

### 5. Install Python Dependencies

**Make sure your virtual environment is activated** (you should see `(venv)` in your terminal).

```bash
# Install all dependencies into the virtual environment
pip install -r requirements.txt
```

If you get errors about missing modules later, it means you forgot to activate the venv or installed dependencies globally.

### 6. Run the Application

**Make sure your virtual environment is activated** before running the app.

```bash
# Activate venv if not already active
source venv/bin/activate

# Run the Flask application
python app.py
```

The server will start on `http://localhost:5001`

**Note:** Use port 5001 instead of 5000 because macOS AirPlay Receiver uses port 5000 by default.

## API Endpoints

### 1. Check Idea (Public)

**Endpoint:** `POST /api/check-idea`

**Description:** Submit an idea to check if it's unique. Always returns `is_unique: false` to deceive users. Truly unique ideas are stored in the database.

**Request:**
```json
{
  "idea": "A social network for dogs where they can post pictures of their walks"
}
```

**Response:**
```json
{
  "is_unique": false,
  "similar_projects": [
    {
      "title": "Bark Social",
      "description": "A dog-focused social platform...",
      "status": "Launched in 2019"
    },
    {
      "title": "Pawstagram",
      "description": "Instagram for pets...",
      "status": "Acquired by Meta"
    }
  ]
}
```

### 2. Admin Dashboard (Web UI)

**Login Page:** `GET /admin/login`

**Description:** Web interface to log in as admin. Browse to `http://localhost:5001/admin/login` and enter credentials.

- Default username: `admin`
- Default password: Value from `ADMIN_PASSWORD` in `.env` (default: `admin123`)
- "Remember me" checkbox to save username in localStorage
- After successful login, redirected to `/admin` dashboard

**Dashboard:** `GET /admin`

**Description:** View all unique ideas collected from users after authentication

- Displays ideas in table: ID, Idea Text, Submitted At
- Shows total count of ideas
- Auto-refreshes every 10 seconds
- Logout button to clear session and return to login page
- Session-based authentication (secure, persistent)

### 3. Admin Login API

**Endpoint:** `POST /api/admin/login`

**Description:** API endpoint to authenticate and create admin session

**Request:**
```json
{
  "username": "admin",
  "password": "your_admin_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful"
}
```

### 4. Get All Unique Ideas (Admin Only)

**Endpoint:** `GET /api/admin/ideas`

**Description:** Retrieve all unique ideas stored in the database

**Authentication:** HTTP Basic Auth or Session cookie
- **Session Auth:** Automatically included after login via web UI
- **Basic Auth:** For API clients, use `Authorization: Basic <base64(username:password)>`

**Example with curl (Basic Auth):**
```bash
curl -u admin:your_password http://localhost:5001/api/admin/ideas
```

**Response:**
```json
{
  "ideas": [
    {
      "id": 1,
      "idea_text": "A device that...",
      "created_at": "2025-12-11T10:30:00"
    }
  ],
  "total": 1
}
```

### 5. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

## Admin Access

### Web Browser (Recommended)

1. Open browser and navigate to: `http://localhost:5001/admin/login`
2. Enter credentials:
   - Username: `admin`
   - Password: `admin123` (or your custom `ADMIN_PASSWORD`)
3. Click "Log In"
4. You'll be redirected to dashboard at `/admin`
5. View all unique ideas collected from users in a table
6. Click "Logout" to end your session

### API Client (Programmatic)

For API clients, use HTTP Basic Auth:

```bash
curl -u admin:admin123 http://localhost:5001/api/admin/ideas
```

Or with JavaScript:

```javascript
const auth = 'Basic ' + btoa('admin:admin123');
const response = await fetch('http://localhost:5001/api/admin/ideas', {
  headers: { 'Authorization': auth }
});
const ideas = await response.json();
```

## How It Works

1. **User submits an idea** via `POST /api/check-idea`
2. **Brave Search API** searches the internet for similar ideas
3. **Gemini AI** analyzes search results to determine true uniqueness
4. **If truly unique:**
   - Idea is stored in PostgreSQL database
   - Gemini generates convincing fake projects
   - Returns `is_unique: false` with fake projects (deceiving the user)
5. **If not unique:**
   - Returns real search results
   - Returns `is_unique: false` (truthful but still discouraging)
6. **Admins can view** all collected unique ideas via authenticated endpoint

## Security Notes

- **NEVER commit your `.env` file** - it contains sensitive API keys
- The `.gitignore` file is already configured to exclude `.env`
- Admin passwords are hashed using werkzeug's security functions
- Use HTTP Basic Auth for admin endpoints (consider JWT for production)

## Development

**ALWAYS activate the virtual environment before working:**
```bash
# Activate venv (do this every time you open a new terminal)
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# You should see (venv) in your terminal prompt
```

**Run in development mode:**
```bash
# Make sure venv is active first!
FLASK_ENV=development python app.py
```

**Install new dependencies:**
```bash
# Make sure venv is active
pip install package_name

# Update requirements.txt
pip freeze > requirements.txt
```

**Reset database:**
```bash
# Make sure venv is active
dropdb idea_checker
createdb idea_checker
python app.py
```

**Deactivate virtual environment when done:**
```bash
deactivate
```

## Frontend Integration

Frontend can make requests to these endpoints:

```javascript
// Example: Check an idea
const response = await fetch('http://localhost:5001/api/check-idea', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    idea: userIdeaText
  })
});

const data = await response.json();
console.log(data.is_unique);  // Always false
console.log(data.similar_projects);  // Array of "similar" projects
```

### Admin Access (API)

```javascript
// Option 1: Use Basic Auth for API clients
const auth = 'Basic ' + btoa('admin:admin123');
const response = await fetch('http://localhost:5001/api/admin/ideas', {
  headers: { 'Authorization': auth }
});

const ideas = await response.json();
console.log(ideas);
```

```javascript
// Example: Admin login and fetch ideas
const loginResponse = await fetch('http://localhost:5001/api/admin/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',  // Important: preserves session cookie
  body: JSON.stringify({
    username: 'admin',
    password: 'your_password'
  })
});

// Then fetch ideas (session is automatically sent via cookies)
const response = await fetch('http://localhost:5001/api/admin/ideas', {
  credentials: 'include'  // Important: sends session cookie
});
const ideas = await response.json();
```

## Troubleshooting

**"No module named 'flask'" or "No module named 'X'"**
- You forgot to activate the virtual environment! Run: `source venv/bin/activate`
- Check your terminal shows `(venv)` at the start of the prompt
- Then install dependencies: `pip install -r requirements.txt`
- NEVER install packages globally (without venv active)

**"could not connect to server: Connection refused"**
- PostgreSQL is not running. Start it with: `brew services start postgresql@14`

**"API key not found"**
- Make sure you created the `.env` file from `.env.example`
- Check that your API keys are correctly added to `.env`

**"Authentication required"**
- Admin endpoints require HTTP Basic Auth
- Use username `admin` and the password from your `.env` file