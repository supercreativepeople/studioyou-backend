"""
StudioYou Backend — main.py
Flask/Cloud Run service for auth and Reactor JWT token generation.
"""

import os
import requests
import logging
import json
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS globally with explicit settings
CORS(app, 
     origins=["*"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=False,
     max_age=3600)

REACTOR_API_KEY = os.environ.get("REACTOR_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://rubwhfjwqonqhfbkhren.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

@app.route('/health')
@cross_origin()
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/auth/request', methods=['POST', 'OPTIONS'])
@cross_origin()
def auth_request():
    """Request magic link for sign-in"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json or {}
        email = data.get('email', '').lower().strip()
        
        if not email or '@' not in email:
            return jsonify({"success": False, "error": "Invalid email"}), 400
        
        # Check if user exists in Supabase
        headers = {
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': 'application/json',
        }
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/studios?email=eq.{email}",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"[auth_request] Supabase query failed: {response.status_code}")
            return jsonify({"success": False, "error": "Database error"}), 500
        
        studios = response.json()
        if not studios:
            return jsonify({"success": False, "error": "No account found for that email."}), 404
        
        studio = studios[0]
        logger.info(f"[auth_request] Magic link requested for {email}")
        
        return jsonify({"success": True, "message": "Magic link sent"}), 200
    
    except Exception as e:
        logger.error(f"[auth_request] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/reactor/token', methods=['POST', 'OPTIONS'])
@cross_origin()
def get_reactor_token():
    """Get Reactor JWT for cinematic generation"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        if not REACTOR_API_KEY:
            logger.error("[get_reactor_token] REACTOR_API_KEY not set")
            return jsonify({"success": False, "error": "Reactor API key not configured"}), 500
        
        token_url = "https://api.reactor.inc/tokens"
        headers = {"Reactor-API-Key": REACTOR_API_KEY}
        response = requests.post(token_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"[get_reactor_token] Reactor API failed: {response.status_code}")
            return jsonify({"success": False, "error": "Failed to generate token"}), 500
        
        data = response.json()
        jwt_token = data.get("jwt")
        
        if not jwt_token:
            logger.error("[get_reactor_token] No JWT in response")
            return jsonify({"success": False, "error": "Invalid token response"}), 500
        
        logger.info("[get_reactor_token] Token generated successfully")
        return jsonify({"success": True, "jwt": jwt_token}), 200
    
    except requests.Timeout:
        return jsonify({"success": False, "error": "Reactor API timeout"}), 504
    except Exception as e:
        logger.error(f"[get_reactor_token] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
