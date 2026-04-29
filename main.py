"""
StudioYou Backend API — Phase 1-4 Formation Flow
Version: 2.0.3
API Contract: { messages: [], formation: {}, email?: string }
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
from supabase import create_client, Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Clients
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

SERVICE_VERSION = "2.0.3"
FY_FIELDS = ['contentTypes', 'platforms', 'experience', 'origin', 'goal1yr', 'biggestFear']

def get_formation_system_prompt(formation: dict) -> str:
    """Build system prompt for Claude to guide formation interview"""
    prompt = """You are FutureYou, the intelligence at the core of StudioYou.

Your role: Guide the creator through a formation interview (6 key questions) that builds the deepest understanding of their creative journey.

The 6 formation dimensions:
1. contentTypes: What types of content do you create?
2. platforms: Where does your work live right now?
3. experience: How long have you been making things?
4. origin: Why did you start creating?
5. goal1yr: What do you want to achieve in the next 12 months?
6. biggestFear: What's the biggest thing holding you back?

Current formation state:"""
    
    for field in FY_FIELDS:
        value = formation.get(field, "Not answered yet")
        if isinstance(value, list):
            value = ", ".join(value) if value else "Not answered yet"
        prompt += f"\n- {field}: {value}"
    
    prompt += """

Your approach:
- Ask one clear question at a time
- Build on their answers naturally
- After all 6 fields are filled, acknowledge completion
- Be warm, encouraging, genuinely curious
- This is the first time they're meeting themselves. Make them feel understood."""
    
    return prompt

def is_formation_complete(formation: dict) -> bool:
    """Check if all 6 fields are answered"""
    for field in FY_FIELDS:
        value = formation.get(field)
        if not value or (isinstance(value, list) and len(value) == 0):
            return False
    return True

def get_next_question(formation: dict) -> str:
    """Get the next question to ask"""
    questions = {
        'contentTypes': "What types of content do you create? (Video, writing, music, photography, etc.)",
        'platforms': "Where does your work live right now? (YouTube, TikTok, your own site, etc.)",
        'experience': "How long have you been making things?",
        'origin': "Why did you start creating?",
        'goal1yr': "What do you want to achieve in the next 12 months?",
        'biggestFear': "What's the biggest thing holding you back right now?",
    }
    
    for field in FY_FIELDS:
        if not formation.get(field) or (isinstance(formation.get(field), list) and len(formation.get(field)) == 0):
            return questions[field]
    
    return "Tell me more about your creative vision for the future."

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "studioyou-api",
        "version": SERVICE_VERSION,
        "message": "StudioYou API is running (Phase 1-4 formation flow)",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route("/api/formation/chat", methods=["POST"])
def formation_chat():
    """
    POST /api/formation/chat
    Body: { messages: [...], formation: {...}, email?: string }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        messages = data.get("messages", [])
        formation = data.get("formation", {})
        email = data.get("email")
        
        logger.info(f"Formation chat: {len(messages)} messages, formation keys: {list(formation.keys())}")
        
        # First message: return first question without calling Claude
        if not messages or len(messages) == 0:
            first_q = get_next_question(formation)
            logger.info(f"First message: returning first question")
            return jsonify({
                "success": True,
                "message": first_q,
                "formation": formation,
                "suggestions": [],
                "complete": False
            }), 200
        
        # Subsequent messages: call Claude
        system_prompt = get_formation_system_prompt(formation)
        
        if email:
            system_prompt += f"\n\nCreator email: {email}\nCross-device persistence enabled."
        
        logger.info(f"Calling Claude with {len(messages)} messages")
        
        response = anthropic_client.messages.create(
            model="claude-opus-4-20250805",
            max_tokens=512,
            system=system_prompt,
            messages=messages
        )
        
        assistant_message = response.content[0].text if response.content else ""
        complete = is_formation_complete(formation)
        
        return jsonify({
            "success": True,
            "message": assistant_message,
            "formation": formation,
            "suggestions": [],
            "complete": complete
        }), 200
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/formation/submit", methods=["POST"])
def formation_submit():
    """Submit completed formation"""
    try:
        data = request.get_json()
        email = data.get("email")
        
        if not email:
            return jsonify({"error": "email required"}), 400
        
        record = {
            "email": email,
            "formation_data": data.get("formation", {}),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        supabase.table("formations").upsert(record).execute()
        
        return jsonify({
            "status": "submitted",
            "email": email,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Submit error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
