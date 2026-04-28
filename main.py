# StudiYou Backend - v1.2.0 - Branded Email Template (April 24, 2026)
import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from supabase import create_client
from dotenv import load_dotenv
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
                    if "firstName" in formation_data and formation_data["firstName"]:
                        first_name = formation_data["firstName"]
                    elif "creatorName" in formation_data and formation_data["creatorName"]:
                        first_name = formation_data["creatorName"].split()[0]
                    else:
                        first_name = "Creator"
                
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
                                
                                <!-- YOUR STUDIO label and Formation Arc badge -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 16px;">
                                    <tr>
                                        <td align="left">
                                            <p style="margin: 0; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: rgba(240, 242, 255, 0.5); font-weight: 500;">Your Studio</p>
                                        </td>
                                        <td align="right">
                                            <span style="display: inline-block; background-color: #00c8ff; color: #06091a; font-size: 10px; letter-spacing: 0.5px; text-transform: uppercase; font-weight: 600; padding: 4px 8px; border-radius: 3px;">Formation Arc</span>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Studio Name -->
                                <h2 style="margin: 0 0 24px 0; font-size: 28px; font-weight: 300; color: #f0f2ff; letter-spacing: -0.5px;">{studio_name}</h2>
                                
                                <!-- StudioYou Logo -->
                                <div style="margin: 32px 0; text-align: center;">
                                    <img src="https://studioyou.app/assets/SY_OFFICIAL_SHUTTER_KEY.png" alt="StudioYou" width="48" height="48" style="display: inline-block; object-fit: contain;">
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
                "from": RESEND_FROM_EMAIL,
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
            first_name = formation_data.get("firstName") or formation_data.get("creatorName", "Creator").split()[0]
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
