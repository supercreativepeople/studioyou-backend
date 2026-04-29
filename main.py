"""
StudioYou Backend API
Claude-powered creator platform backend
Version: 2.0.2 - Phase 1-4 Formation Flow

API CONTRACT:
/api/formation/chat accepts:
{
    "messages": [{"role": "user", "content": "..."}, ...],
    "formation": { "contentTypes": [...], "platforms": [...], ... },
    "email": "optional@email.com"  # Not required for anonymous flow
}

Returns:
{
    "success": true,
    "message": "FutureYou response...",
    "formation": { updated formation object },
    "suggestions": ["chip1", "chip2", ...],
    "complete": false  # true when all 6 fields are filled
}
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from anthropic import Anthropic
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize Anthropic client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Resend API for email
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# Constants
SERVICE_VERSION = "2.0.2"
HEALTH_CHECK_MESSAGE = "StudioYou API is running (Phase 1-4 formation flow)"

# Formation field configuration
FY_FIELDS = ['contentTypes', 'platforms', 'experience', 'origin', 'goal1yr', 'biggestFear']


def get_formation_system_prompt(formation: dict) -> str:
    """Build system prompt that helps Claude guide the formation interview"""
    prompt = """You are FutureYou, the intelligence at the core of StudioYou.

Your role in Formation:
- Guide the creator through a 20-30 minute interview
- Ask clarifying questions based on their answers
- Identify patterns and connections
- Help them articulate their journey, goals, and creative voice
- Never rush - let the conversation unfold naturally

The formation captures 6 key dimensions:
1. contentTypes: What this creator makes
2. platforms: Where their work lives (or could)
3. experience: How long they've been creating
4. origin: Why they started creating
5. goal1yr: What they want to achieve in 12 months
6. biggestFear: What holds them back

Current formation state:"""
    
    # Add current formation data
    for field in FY_FIELDS:
        value = formation.get(field, "Not yet answered")
        if isinstance(value, list):
            value = ", ".join(value) if value else "Not yet answered"
        prompt += f"\n- {field}: {value}"
    
    prompt += """

Your approach:
- If this is the first message, ask the first formation question warmly
- Acknowledge previous answers and build on them
- Ask one clear question at a time
- Suggest helpful answers but don't limit their thinking
- After all 6 fields are filled, offer recognition and next steps

Remember: This creator is meeting themselves for the first time. Make them feel understood."""
    
    return prompt


def is_formation_complete(formation: dict) -> bool:
    """Check if all 6 formation fields are filled"""
    for field in FY_FIELDS:
        value = formation.get(field)
        if not value or (isinstance(value, list) and len(value) == 0):
            return False
    return True


def get_next_formation_question(formation: dict) -> str:
    """Determine what question should be asked next"""
    questions = {
        'contentTypes': "What types of content do you create? (Video, writing, music, photography, etc.)",
        'platforms': "Where does your work live right now? (YouTube, TikTok, your own site, etc.)",
        'experience': "How long have you been making things?",
        'origin': "Why did you start creating?",
        'goal1yr': "What do you want to achieve in the next 12 months?",
        'biggestFear': "What's the biggest thing holding you back right now?",
    }
    
    for field in FY_FIELDS:
        value = formation.get(field)
        if not value or (isinstance(value, list) and len(value) == 0):
            return questions.get(field, "Tell me more about your creative journey.")
    
    return "We've covered everything. What insights stand out to you?"


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "studioyou-api",
        "version": SERVICE_VERSION,
        "message": HEALTH_CHECK_MESSAGE,
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/api/formation/chat", methods=["POST"])
def formation_chat():
    """
    Formation interview chat endpoint.
    
    Accepts: { messages, formation, email (optional) }
    Returns: { success, message, formation, suggestions, complete }
    """
    try:
        data = request.get_json()
        messages = data.get("messages", [])
        formation = data.get("formation", {})
        email = data.get("email")

        # Validate required fields
        if not messages or not isinstance(messages, list):
            return jsonify({"error": "messages array is required"}), 400

        # If no messages yet, start with first question
        if len(messages) == 0:
            first_question = get_next_formation_question(formation)
            return jsonify({
                "success": True,
                "message": first_question,
                "formation": formation,
                "suggestions": [],
                "complete": False
            }), 200

        # Build system prompt with formation context
        system_prompt = get_formation_system_prompt(formation)

        # Add email context if available
        if email:
            system_prompt += f"\n\nCreator email: {email}\nCross-device persistence is enabled."

        # Call Claude API
        logger.info(f"Calling Claude with {len(messages)} messages, formation state: {list(formation.keys())}")
        
        response = anthropic_client.messages.create(
            model="claude-opus-4-20250805",
            max_tokens=512,
            system=system_prompt,
            messages=messages
        )

        # Extract response text
        assistant_message = response.content[0].text if response.content else ""

        # Check if formation is now complete
        complete = is_formation_complete(formation)

        # Generate suggestions based on the last formation field
        suggestions = []
        if not complete:
            next_question = get_next_formation_question(formation)
            # Add a few placeholder suggestions
            if "content" in next_question.lower():
                suggestions = ["Video", "Writing", "Music", "Photography"]
            elif "platform" in next_question.lower():
                suggestions = ["YouTube", "TikTok", "Instagram", "My own site"]
            elif "year" in next_question.lower() or "long" in next_question.lower():
                suggestions = ["Less than 1 year", "1-3 years", "3-5 years", "5+ years"]

        return jsonify({
            "success": True,
            "message": assistant_message,
            "formation": formation,
            "suggestions": suggestions,
            "complete": complete
        }), 200

    except Exception as e:
        logger.error(f"Formation chat error: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Failed to process message: {str(e)}"
        }), 500


@app.route("/api/formation/submit", methods=["POST"])
def formation_submit():
    """
    Submit completed formation data to Supabase.
    
    Request body:
    {
        "email": "creator@example.com",
        "formation": { full formation object },
        "summary": "Text summary from FutureYou"
    }
    """
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"error": "email is required"}), 400

        # Prepare record for Supabase
        record = {
            "email": email,
            "formation_data": data.get("formation", {}),
            "summary": data.get("summary", ""),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Upsert to Supabase (insert or update)
        response = supabase.table("formations").upsert(record).execute()
        logger.info(f"Formation submitted for {email}")

        return jsonify({
            "status": "submitted",
            "email": email,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Formation submit error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/magic-link", methods=["POST"])
def auth_magic_link():
    """
    Request magic link via email for cross-device access.
    
    Request body:
    {
        "email": "creator@example.com"
    }
    """
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return jsonify({"error": "email is required"}), 400

        # For now, just acknowledge - in production would send via Resend
        logger.info(f"Magic link requested for {email}")

        return jsonify({
            "status": "link_sent",
            "email": email,
            "message": "Check your email for login link"
        }), 200

    except Exception as e:
        logger.error(f"Magic link error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "internal server error"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
