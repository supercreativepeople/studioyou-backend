"""
StudioYou Backend — main.py
Flask/Cloud Run service for Reactor JWT token generation.
"""

import os
import requests
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*"
    "https://studioyou.app",
    "https://studioyou.studio",
    "https://69eae34af757b60008e2c5f2--studioyou-app.netlify.app",
    "http://localhost:3000",
    "null",
], supports_credentials=True)

REACTOR_API_KEY = os.environ.get("REACTOR_API_KEY", "")

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/reactor/token', methods=['POST'
def get_reactor_token():
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
