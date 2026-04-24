"""
StudioYou Backend — main.py
Flask/Cloud Run service for auth and formation data persistence.
"""

import os
import json
import secrets
import hashlib
import logging
import subprocess
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=[
    "https://studioyou.app",
    "https://studioyou.studio",
    "http://localhost:3000",
    "null",
])

SUPABASE_URL      = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY      = os.environ.get("SUPABASE_SERVICE_KEY", "")
RESEND_API_KEY    = os.environ.get("RESEND_API_KEY", "")
SECRET_KEY        = os.environ.get("SY_SECRET_KEY", "dev-secret-change-in-prod")
FRONTEND_URL      = os.environ.get("FRONTEND_URL", "https://studioyou.app")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
REACTOR_API_KEY   = os.environ.get("REACTOR_API_KEY", "")

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"}), 200

@app.route('/api/reactor/token', methods=['POST'])
def get_reactor_token():
    """
    Generate JWT token for Reactor SDK (Helios cinematic generation).
    POST body: {} (no required fields)
    Returns: { "jwt": "eyJ0eXAi..." }
    """
    try:
        if not REACTOR_API_KEY:
            logger.error("[get_reactor_token] REACTOR_API_KEY not set")
            return jsonify({"success": False, "error": "Reactor API key not configured"}), 500
        
        reactor_endpoint = os.environ.get("REACTOR_API_ENDPOINT", "https://reactor.unstable.run")
        token_url = f"{reactor_endpoint}/api/jwt"
        
        headers = {
            "Authorization": f"Bearer {REACTOR_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "account_id": "studioyou",
            "sub": "studioyou-user",
            "roles": ["viewer"],
        }
        
        response = requests.post(token_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"[get_reactor_token] Reactor API failed: {response.status_code} {response.text}")
            return jsonify({"success": False, "error": "Failed to generate token"}), 500
        
        data = response.json()
        jwt_token = data.get("jwt")
        
        if not jwt_token:
            logger.error("[get_reactor_token] No JWT in response")
            return jsonify({"success": False, "error": "Invalid token response"}), 500
        
        logger.info("[get_reactor_token] Token generated successfully")
        return jsonify({"success": True, "jwt": jwt_token}), 200
    
    except requests.Timeout:
        logger.error("[get_reactor_token] Reactor API timeout")
        return jsonify({"success": False, "error": "Reactor API timeout"}), 504
    except Exception as e:
        logger.error(f"[get_reactor_token] Unexpected error: {type(e).__name__}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
