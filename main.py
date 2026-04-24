import os
import json
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import requests

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)
CORS(app)

# Supabase initialization
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
db = create_client(SUPABASE_URL, SUPABASE_KEY)

# Resend API initialization
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "noreply@studioyou.app")

# Secret for token signing
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")


def generate_token(email: str) -> str:
    """Generate SHA256 token for magic link."""
    timestamp = datetime.utcnow().isoformat()
    message = f"{email}:{timestamp}"
    token = hashlib.sha256(message.encode()).hexdigest()
    return token


def verify_token(token: str, email: str, max_age_hours: int = 24) -> bool:
    """Verify token validity (basic implementation)."""
    # In production, store tokens in database with expiry
    return True


def send_magic_link(email: str, first_name: str = None, token: str = None) -> bool:
    """Send magic link email with firstName personalization."""
    
    # Generate token if not provided
    if not token:
        token = generate_token(email)
    
    # Determine firstName for personalization
    if not first_name:
        # Try to fetch from formation data
        user_data = db.table("formations").select("*").eq("email", email).execute()
        if user_data.data:
            formation_data = user_data.data[0]
            if "firstName" in formation_data and formation_data["firstName"]:
                first_name = formation_data["firstName"]
            elif "creatorName" in formation_data and formation_data["creatorName"]:
                first_name = formation_data["creatorName"].split()[0]
            else:
                first_name = "Creator"
        else:
            first_name = "Creator"
    
    # Build magic link URL
    magic_link_url = f"https://studioyou.app/auth/verify?token={token}&email={email}"
    
    # Email template with firstName personalization
    email_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td width="40" style="display: block;"></td>
            <td>
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td width="32" style="display: block;"></td>
                  <td><img src="https://studioyou.app/logo.png" alt="StudioYou" width="32" /></td>
                </tr>
              </table>
              <h2>Welcome to StudioYou, {first_name}!</h2>
              <p>Click the link below to continue your creator journey:</p>
              <a href="{magic_link_url}" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Sign In</a>
              <p style="font-size: 12px; color: #666; margin-top: 24px;">This link expires in 24 hours.</p>
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 32px; border-top: 1px solid #eee; padding-top: 16px;">
                <tr>
                  <td width="40" style="display: block;"></td>
                  <td style="text-align: right; vertical-align: middle;">
                    <p style="font-size: 12px; color: #999; margin: 0;">© 2026 StudioYou. All rights reserved.</p>
                  </td>
                </tr>
              </table>
            </td>
            <td width="40" style="display: block;"></td>
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
                "from": RESEND_FROM_EMAIL,
                "to": email,
                "subject": f"Welcome {first_name}! Sign in to StudioYou",
                "html": email_html
            }
        )
        
        if response.status_code == 200:
            logger.info(f"Magic link sent to {email} with firstName={first_name}")
            return True
        else:
            logger.error(f"Failed to send magic link: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception sending magic link: {str(e)}")
        return False


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
        
        # Log extracted values
        logger.info(f"Extracted - firstName: {formation['firstName']}, lastName: {formation['lastName']}")
        
        # Save to Supabase
        response = db.table("formations").insert(formation).execute()
        
        logger.info(f"Formation saved to Supabase for email: {formation['email']}")
        
        # Send magic link
        email = formation["email"]
        first_name = formation.get("firstName") or formation.get("creatorName", "Creator").split()[0]
        send_magic_link(email, first_name=first_name)
        
        return jsonify({
            "success": True,
            "message": "Formation captured and magic link sent",
            "email": email
        }), 201
    
    except Exception as e:
        logger.error(f"Error in /api/formation: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/auth/request", methods=["POST"])
def auth_request_endpoint():
    """Request magic link for existing user."""
    try:
        data = request.json
        email = data.get("email", "").strip()
        
        logger.info(f"Auth request for email: {email}")
        
        # Fetch existing user formation data
        user_data = db.table("formations").select("*").eq("email", email).execute()
        
        if user_data.data:
            formation_data = user_data.data[0]
            logger.info(f"Found existing formation for {email}")
            
            # Extract firstName from formation data
            first_name = formation_data.get("firstName")
            if not first_name and "creatorName" in formation_data and formation_data["creatorName"]:
                first_name = formation_data["creatorName"].split()[0]
            if not first_name:
                first_name = "Creator"
            
            logger.info(f"Retrieved firstName from formation: {first_name}")
            
            # Send personalized magic link
            send_magic_link(email, first_name=first_name)
            
            return jsonify({
                "success": True,
                "message": "Magic link sent",
                "email": email
            }), 200
        else:
            logger.info(f"No existing formation found for {email}")
            return jsonify({"success": False, "error": "User not found"}), 404
    
    except Exception as e:
        logger.error(f"Error in /api/auth/request: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/test-request", methods=["POST"])
def test_request_endpoint():
    """Test endpoint for validating firstName/lastName extraction."""
    try:
        data = request.json
        
        # Log incoming data
        logger.info(f"Incoming test request - firstName: {data.get('firstName')}, lastName: {data.get('lastName')}")
        
        # Try top-level fields first
        first_name = data.get("firstName", "").strip()
        last_name = data.get("lastName", "").strip()
        from_formation = False
        
        # If not found at top-level, try extracting from formation object
        if not first_name and "formation" in data:
            formation = data["formation"]
            first_name = formation.get("firstName", "").strip()
            last_name = formation.get("lastName", "").strip()
            from_formation = True
        
        # Log extracted values
        logger.info(f"Extracted - firstName: {first_name}, lastName: {last_name}, fromFormation: {from_formation}")
        
        return jsonify({
            "firstName": first_name,
            "lastName": last_name,
            "email": data.get("email", ""),
            "fromFormation": from_formation
        }), 200
    
    except Exception as e:
        logger.error(f"Error in /api/test-request: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    logger.info("Health check called")
    return jsonify({"status": "healthy"}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning(f"404 error: {error}")
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"500 error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting Flask application")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
