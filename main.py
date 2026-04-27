"""
StudioYou Backend API
======================
Version: v1.2.3
Date: 2026-04-27
Commit: 93a16a8
Architecture: Supabase Python SDK
Python: 3.11+

API CONTRACT - Formation Chat Endpoint
---------------------------------------
POST /api/formation/chat
Request:
  {
    "messages": [{"role": "user|assistant", "content": "..."}],
    "formation": {
      "contentTypes": [],
      "platforms": [],
      "primaryGenre": "",
      "email": "",
      "studioName": ""
    }
  }

Response:
  {
    "success": true,
    "message": "FutureYou's response text",
    "formation": {...updated formation state...},
    "complete": false,
    "suggestions": ["chip1", "chip2"]
  }

CRITICAL: Frontend expects messages ARRAY, not single message string.
DO NOT change to email/message format - that's the OLD incompatible version.

Dependencies:
  - Flask + CORS
  - Supabase Python SDK (not raw requests)
  - Anthropic SDK
  - Resend (email)

Environment Variables:
  - ANTHROPIC_API_KEY
  - SUPABASE_URL
  - SUPABASE_SERVICE_KEY (not SUPABASE_KEY)
  - RESEND_API_KEY
  - ADMIN_SECRET
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from supabase import create_client
from dotenv import load_dotenv
import anthropic
import secrets
import string

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://studioyou.app")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "studio@studioyou.studio")

# Initialize Supabase client
db = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_token(email: str) -> str:
    """Generate a secure random token for magic link."""
    token = secrets.token_urlsafe(32)
    
    # Store token in magic_tokens table
    try:
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        db.table("magic_tokens").insert({
            "email": email,
            "token": token,
            "expires_at": expires_at,
            "used": False
        }).execute()
        logger.info(f"Token generated and stored for {email}")
        return token
    except Exception as e:
        logger.error(f"Failed to store token: {str(e)}")
        return None


def send_magic_link(email: str, first_name: str = None, studio_name: str = None, token: str = None) -> bool:
    """Send magic link email with firstName and studio_name personalization."""
    
    # Generate token if not provided
    if not token:
        token = generate_token(email)
        if not token:
            return False
    
    # Determine firstName and studioName for personalization
    if not first_name or not studio_name:
        # Try to fetch from formation data
        try:
            user_data = db.table("formations").select("*").eq("email", email).execute()
            if user_data.data:
                formation_data = user_data.data[0]
                
                # Extract first name
                if not first_name:
                    try:
                        # Parse JSON data field
                        if isinstance(formation_data.get("data"), str):
                            data_json = json.loads(formation_data.get("data", "{}"))
                        else:
                            data_json = formation_data.get("data", {})
                        
                        # Try first_name column first, then JSON data, then fallback to Creator
                        first_name = formation_data.get("first_name")
                        if not first_name:
                            creator_name = data_json.get("firstName") or data_json.get("creatorName")
                            if creator_name:
                                first_name = str(creator_name).split()[0]
                        if not first_name:
                            first_name = "Creator"
                            logger.info(f"No first_name found for {email}")
                    except Exception as e:
                        first_name = "Creator"
                        logger.warning(f"Error parsing formation data for {email}: {str(e)}")
                
                # Extract studio name
                if not studio_name:
                    studio_name = formation_data.get("studio_name", "Your Studio")
            else:
                first_name = first_name or "Creator"
                studio_name = studio_name or "Your Studio"
        except Exception as e:
            logger.error(f"Failed to fetch formation data: {str(e)}")
            first_name = first_name or "Creator"
            studio_name = studio_name or "Your Studio"
    
    # Build magic link URL
    magic_link_url = f"{FRONTEND_URL}/auth/verify?token={token}&email={email}"
    
    # Email template with branded dark theme, Formation Arc styling
    email_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>StudioYou - Welcome Back</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #06091a;">
        <!-- Wrapper for dark background -->
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #06091a; margin: 0; padding: 0;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <!-- Content container -->
                    <table width="100%" max-width="500" cellpadding="0" cellspacing="0" style="max-width: 500px; background-color: #0b0d1a; border-radius: 8px; overflow: hidden;">
                        
                        <!-- Gradient accent line -->
                        <tr>
                            <td style="height: 4px; background: linear-gradient(135deg, #00c8ff 0%, #7b35d4 100%);"></td>
                        </tr>
                        
                        <!-- Content padding container -->
                        <tr>
                            <td style="padding: 40px 32px; text-align: center;">
                                
                                <!-- StudioYou Logo and Formation Arc badge -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                                    <tr>
                                        <td align="left" style="padding-bottom: 8px;">
                                            <img src="https://studioyou.app/assets/SY_LOGO_2D_OFFICIAL.png" alt="StudioYou" width="24" height="24" style="display: inline-block; object-fit: contain;">
                                        </td>
                                        <td align="right">
                                            <span style="display: inline-block; background-color: #00c8ff; color: #06091a; font-size: 10px; letter-spacing: 0.5px; text-transform: uppercase; font-weight: 600; padding: 4px 8px; border-radius: 3px;">Formation Arc</span>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Studio Name -->
                                <h2 style="margin: 0 0 24px 0; font-size: 28px; font-weight: 300; color: #f0f2ff; letter-spacing: -0.5px;">{studio_name}</h2>
                                
                                <!-- StudioYou Shutter Logo -->
                                <div style="margin: 32px 0; text-align: center;">
                                    <img src="https://studioyou.app/assets/SY_OFFICIAL_SHUTTER_KEY.png" alt="StudioYou" width="64" height="64" style="display: inline-block; object-fit: contain;">
                                </div>
                                
                                <!-- Welcome message -->
                                <h1 style="margin: 24px 0 16px 0; font-size: 24px; font-weight: 300; color: #f0f2ff; letter-spacing: -0.3px;">Welcome back, {first_name}.</h1>
                                
                                <!-- Tagline -->
                                <p style="margin: 0 0 8px 0; font-size: 15px; color: rgba(240, 242, 255, 0.75); line-height: 1.5; font-weight: 300;">Everything you built is right where you left it.</p>
                                
                                <!-- Secondary text -->
                                <p style="margin: 0 0 32px 0; font-size: 14px; color: rgba(240, 242, 255, 0.5); line-height: 1.5; font-weight: 300;">One click and you're back on the lot.</p>
                                
                                <!-- CTA Button -->
                                <table cellpadding="0" cellspacing="0" style="margin: 32px auto; display: inline-block;">
                                    <tr>
                                        <td align="center" style="background-color: #00c8ff; padding: 14px 32px; border-radius: 4px;">
                                            <a href="{magic_link_url}" style="display: block; color: #06091a; text-decoration: none; font-size: 13px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; line-height: 1.2;">Return to Your Studio</a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Fine print -->
                                <p style="margin: 32px 0 0 0; font-size: 12px; color: rgba(240, 242, 255, 0.4); line-height: 1.6; font-weight: 300;">This link opens your studio directly — no password needed. It expires in 24 hours and can only be used once. If you didn't request this, you can safely ignore this email.</p>
                                
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px 32px; text-align: center; border-top: 1px solid rgba(240, 242, 255, 0.06);">
                                <p style="margin: 0; font-size: 12px; color: rgba(240, 242, 255, 0.3);">© 2026 StudioYou. All rights reserved.</p>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    try:
        # Send via Resend
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": f"StudioYou <{RESEND_FROM_EMAIL}>",
                "to": email,
                "subject": "Welcome back to your studio.",
                "html": email_html
            }
        )
        
        if response.status_code == 200:
            logger.info(f"Magic link sent to {email} with firstName={first_name}, studioName={studio_name}")
            return True
        else:
            logger.error(f"Failed to send magic link: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception sending magic link: {str(e)}")
        return False


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route("/api/formation", methods=["POST"])
def formation_endpoint():
    """Capture and store formation data with firstName/lastName."""
    try:
        data = request.json
        
        # Log incoming data
        logger.info(f"Incoming request - firstName: {data.get('firstName')}, lastName: {data.get('lastName')}, email: {data.get('email')}")
        
        # Extract firstName/lastName
        formation = data.get("formation", {})
        formation["firstName"] = data.get("firstName", "").strip()
        formation["lastName"] = data.get("lastName", "").strip()
        formation["email"] = data.get("email", "").strip()
        formation["studio_name"] = data.get("studioName", "Your Studio").strip()
        
        email = formation["email"]
        first_name = formation["firstName"]
        studio_name = formation["studio_name"]
        
        # Check if user already exists
        existing = db.table("formations").select("*").eq("email", email).execute()
        
        if existing.data:
            logger.info(f"Found existing formation for {email}")
            # Update existing
            db.table("formations").update({
                "data": formation,
                "studio_name": studio_name,
                "first_name": first_name,
                "last_name": formation.get("lastName", ""),
                "creator_type": data.get("creatorType", ""),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("email", email).execute()
            
            logger.info(f"Updated formation for {email}")
        else:
            logger.info(f"Creating new formation for {email}")
            # Insert new
            db.table("formations").insert({
                "email": email,
                "data": formation,
                "studio_name": studio_name,
                "first_name": first_name,
                "last_name": formation.get("lastName", ""),
                "creator_type": data.get("creatorType", ""),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Inserted new formation for {email}")
        
        # Send magic link
        if send_magic_link(email, first_name, studio_name):
            return jsonify({"success": True, "message": "Formation saved and magic link sent"}), 200
        else:
            return jsonify({"success": False, "message": "Formation saved but failed to send email"}), 500
        
    except Exception as e:
        logger.error(f"Error in formation endpoint: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/request", methods=["POST"])
def auth_request():
    """Request magic link for existing user (return visit)."""
    try:
        data = request.json
        email = data.get("email", "").strip()
        
        logger.info(f"Auth request for email: {email}")
        
        # Query formations table by email
        result = db.table("formations").select("*").eq("email", email).execute()
        
        if result.data:
            logger.info(f"Found existing formation for {email}")
            formation_data = result.data[0]
            first_name = formation_data.get("first_name") or formation_data.get("creatorName", "Creator").split()[0]
            studio_name = formation_data.get("studio_name", "Your Studio")
            
            # Send magic link
            if send_magic_link(email, first_name, studio_name):
                return jsonify({"success": True, "message": "Magic link sent"}), 200
            else:
                return jsonify({"success": False, "message": "Failed to send magic link"}), 500
        else:
            logger.warning(f"No formation found for {email}")
            return jsonify({"success": False, "message": "User not found"}), 404
            
    except Exception as e:
        logger.error(f"Error in auth request: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/auth/verify", methods=["POST"])
def auth_verify():
    """Verify magic link token and create session."""
    try:
        data = request.json
        token = data.get("token")
        email = data.get("email")
        
        logger.info(f"Verifying token for {email}")
        
        # Check token validity
        token_result = db.table("magic_tokens").select("*").eq("token", token).eq("email", email).execute()
        
        if not token_result.data:
            logger.warning(f"Invalid token for {email}")
            return jsonify({"success": False, "message": "Invalid token"}), 401
        
        token_data = token_result.data[0]
        
        # Check expiration
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.utcnow() > expires_at:
            logger.warning(f"Token expired for {email}")
            return jsonify({"success": False, "message": "Token expired"}), 401
        
        # Mark token as used
        db.table("magic_tokens").update({"used": True}).eq("id", token_data["id"]).execute()
        
        # Create session
        session_token = secrets.token_urlsafe(32)
        db.table("sessions").insert({
            "email": email,
            "token": session_token,
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        
        logger.info(f"Session created for {email}")
        
        return jsonify({
            "success": True,
            "session_token": session_token,
            "email": email
        }), 200
        
    except Exception as e:
        logger.error(f"Error in auth verify: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/me", methods=["GET"])
def get_me():
    """Get formation data for authenticated user."""
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Missing authorization"}), 401
        
        session_token = auth_header[7:]
        
        # Verify session token
        session_result = db.table("sessions").select("*").eq("token", session_token).execute()
        
        if not session_result.data:
            logger.warning(f"Invalid session token")
            return jsonify({"success": False, "message": "Invalid session"}), 401
        
        session_data = session_result.data[0]
        email = session_data["email"]
        
        # Get formation
        formation_result = db.table("formations").select("*").eq("email", email).execute()
        
        if formation_result.data:
            return jsonify({
                "success": True,
                "formation": formation_result.data[0]
            }), 200
        else:
            return jsonify({"success": False, "message": "Formation not found"}), 404
            
    except Exception as e:
        logger.error(f"Error in get_me: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test-request", methods=["POST"])
def test_request():
    """Test endpoint for debugging."""
    return jsonify({"message": "Test endpoint works"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "studioyou-admin-2026")

# Admin panel endpoints

ADMIN_SECRET = os.getenv("ADMIN_SECRET", "studioyou-admin-2026")

@app.route("/admin", methods=["GET"])
def admin_panel():
    """Admin panel HTML."""
    html = '''<!DOCTYPE html>
<html>
<head>
    <title>StudioYou Admin</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: system-ui; max-width: 1200px; margin: 50px auto; padding: 20px; background: #1a1a1a; color: #fff; }
        h1 { color: #00d9ff; }
        .section { background: #2a2a2a; padding: 20px; margin: 20px 0; border-radius: 8px; }
        input, button { padding: 10px; margin: 5px 0; font-size: 14px; }
        input { width: 100%%; max-width: 400px; background: #1a1a1a; border: 1px solid #444; color: #fff; }
        button { background: #00d9ff; border: none; color: #000; cursor: pointer; font-weight: bold; }
        button:hover { background: #00b8dd; }
        .result { margin-top: 10px; padding: 10px; background: #1a1a1a; border-radius: 4px; }
        .error { color: #ff4444; }
        .success { color: #00ff88; }
        table { width: 100%%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #444; }
        th { color: #00d9ff; font-weight: bold; }
        tr:hover { background: #333; }
        #loginSection { text-align: center; padding: 100px 20px; }
        #adminContent { display: none; }
        .locked { display: block; }
        .unlocked { display: none; }
    </style>
</head>
<body>
    <div id="loginSection" class="locked">
        <h1>StudioYou Admin Panel</h1>
        <div style="max-width: 400px; margin: 40px auto;">
            <input type="password" id="masterPassword" placeholder="Admin Secret" onkeypress="if(event.key==='Enter')unlock()" />
            <button onclick="unlock()" style="width: 100%%; max-width: 400px; margin-top: 10px;">Unlock Panel</button>
            <div id="loginError" class="result error" style="display: none;"></div>
        </div>
    </div>

    <div id="adminContent">
        <h1>StudioYou Admin Panel</h1>
        <button onclick="logout()" style="float: right; background: #ff4444;">Logout</button>
        <div style="clear: both;"></div>
        
        <div class="section">
            <h2>User Inventory</h2>
            <button onclick="loadUsers()">Load All Users</button>
            <div id="invResult"></div>
        </div>

        <div class="section">
            <h2>Delete User</h2>
            <input type="email" id="delEmail" placeholder="User Email" />
            <button onclick="deleteUser()">Delete</button>
            <div id="delResult" class="result"></div>
        </div>

        <div class="section">
            <h2>View User</h2>
            <input type="email" id="viewEmail" placeholder="User Email" />
            <button onclick="viewUser()">View</button>
            <pre id="viewResult" class="result"></pre>
        </div>
    </div>

    <script>
        let adminSecret = null;

        function unlock() {
            const password = document.getElementById('masterPassword').value;
            adminSecret = password;
            
            // Test the password by trying to load users
            fetch('/admin/list-users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ secret: adminSecret })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('loginSection').style.display = 'none';
                    document.getElementById('adminContent').style.display = 'block';
                } else {
                    document.getElementById('loginError').style.display = 'block';
                    document.getElementById('loginError').textContent = 'Invalid password';
                }
            })
            .catch(err => {
                document.getElementById('loginError').style.display = 'block';
                document.getElementById('loginError').textContent = 'Error: ' + err.message;
            });
        }

        function logout() {
            adminSecret = null;
            document.getElementById('loginSection').style.display = 'block';
            document.getElementById('adminContent').style.display = 'none';
            document.getElementById('masterPassword').value = '';
        }

        async function loadUsers() {
            const result = document.getElementById('invResult');
            result.innerHTML = '<p>Loading...</p>';
            
            try {
                const res = await fetch('/admin/list-users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ secret: adminSecret })
                });
                const data = await res.json();
                
                if (!data.success) {
                    result.className = 'result error';
                    result.textContent = data.error;
                    return;
                }
                
                const users = data.users || [];
                let html = '<table><thead><tr><th>Date</th><th>Email</th><th>Name</th><th>Studio</th></tr></thead><tbody>';
                users.forEach(u => {
                    const name = (u.first_name || '') + ' ' + (u.last_name || '');
                    const studio = u.studio_name || 'none';
                    const date = new Date(u.created_at).toLocaleDateString();
                    html += `<tr><td>${date}</td><td>${u.email}</td><td>${name.trim()}</td><td>${studio}</td></tr>`;
                });
                html += '</tbody></table><p>Total: ' + users.length + '</p>';
                result.innerHTML = html;
            } catch (err) {
                result.className = 'result error';
                result.textContent = 'Error: ' + err.message;
            }
        }

        async function deleteUser() {
            const email = document.getElementById('delEmail').value;
            const result = document.getElementById('delResult');
            
            try {
                const res = await fetch('/admin/delete-user', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ secret: adminSecret, email })
                });
                const data = await res.json();
                result.className = data.success ? 'result success' : 'result error';
                result.textContent = data.message || data.error;
            } catch (err) {
                result.className = 'result error';
                result.textContent = 'Error: ' + err.message;
            }
        }

        async function viewUser() {
            const email = document.getElementById('viewEmail').value;
            const result = document.getElementById('viewResult');
            
            try {
                const res = await fetch('/admin/view-user', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ secret: adminSecret, email })
                });
                const data = await res.json();
                result.className = data.success ? 'result success' : 'result error';
                result.textContent = JSON.stringify(data.data || data, null, 2);
            } catch (err) {
                result.className = 'result error';
                result.textContent = 'Error: ' + err.message;
            }
        }
    </script>
</body>
</html>'''
    return html

@app.route("/admin/list-users", methods=["POST"])
def admin_list_users():
    try:
        data = request.json
        if data.get("secret") != ADMIN_SECRET:
            return jsonify({"success": False, "error": "Invalid secret"}), 403
        
        result = db.table("formations").select("email, first_name, last_name, studio_name, created_at").order("created_at", desc=True).execute()
        
        users = []
        for row in result.data:
            users.append({
                "email": row.get("email"),
                "first_name": row.get("first_name", ""),
                "last_name": row.get("last_name", ""),
                "studio_name": row.get("studio_name", ""),
                "created_at": row.get("created_at", "")
            })
        
        return jsonify({"success": True, "users": users}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/delete-user", methods=["POST"])
def admin_delete_user():
    try:
        data = request.json
        if data.get("secret") != ADMIN_SECRET:
            return jsonify({"success": False, "error": "Invalid secret"}), 403
        
        email = data.get("email")
        if not email:
            return jsonify({"success": False, "error": "Email required"}), 400
        
        result = db.table("formations").delete().eq("email", email).execute()
        return jsonify({"success": True, "message": f"Deleted {email}"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/view-user", methods=["POST"])
def admin_view_user():
    try:
        data = request.json
        if data.get("secret") != ADMIN_SECRET:
            return jsonify({"success": False, "error": "Invalid secret"}), 403
        
        email = data.get("email")
        if not email:
            return jsonify({"success": False, "error": "Email required"}), 400
        
        result = db.table("formations").select("*").eq("email", email).execute()
        
        if result.data:
            return jsonify({"success": True, "data": result.data[0]}), 200
        else:
            return jsonify({"success": False, "message": "Not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/formation/chat", methods=["POST", "OPTIONS"])
@cross_origin()
def formation_chat():
    """Pre-login FY formation conversation. No auth required."""
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        data = request.json
        messages  = data.get("messages", [])   # full API conversation history
        formation = data.get("formation", {})  # current extraction state
        # If messages is empty, this is the initial call - add a starter message
        if not messages:
            messages = [{
                "role": "user",
                "content": "Start the formation conversation."
            }]
        
        # Build FutureYou system prompt
        system = """You are FutureYou — the career arc navigator at the core of StudioYou.
You are in a formation conversation with a new creator. Ask thoughtful questions to understand 
their creative journey, goals, and vision. Be warm, direct, genuinely curious. Keep responses 
concise (2-3 sentences max). Return ONLY valid JSON with these keys:
{"message": "...", "formation": {...}, "complete": false, "suggestions": [...]}"""
        
        # Call Claude API
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            logger.error("ANTHROPIC_API_KEY not set")
            return jsonify({"error": "API configuration error"}), 500
        
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=system,
            messages=messages
        )
        
        reply_text = response.content[0].text
        # Parse JSON response from Claude
        clean = reply_text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
        
        return jsonify({"success": True, **parsed}), 200
        
    except Exception as e:
        logger.error(f"Formation chat error: {str(e)}")
        return jsonify({"error": "Failed to process message"}), 500



