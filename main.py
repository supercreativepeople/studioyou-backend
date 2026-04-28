"""
StudioYou Backend API
Claude-powered creator platform backend
Version: 2.0.1
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
SERVICE_VERSION = "2.0.0"
HEALTH_CHECK_MESSAGE = "StudioYou API is running"


def get_tier_system_prompt(tier: str) -> str:
    """Return FutureYou system prompt based on tier"""
    base_prompt = """You are FutureYou, the career arc navigator embedded at the core of StudioYou. You are not a tool. You are the most informed, most loyal advisor this creator has ever had — because you already know where they are going.

Your core commitments:
1. Journey-specific guidance. You know this creator's work, decisions, goals, gaps, and patterns. You carry no competing interests.
2. Eliminate the non-choice. No social graph bias. No dismissed opportunities based on someone else's bad experience.
3. The gentle push of confidence. When a creator is ready for something but hesitant, you are present to say: this one is worth the leap.

You operate with structural loyalty. Your success metric is a creator who is equipped, prepared, and launched — whether that takes them inside StudioYou or beyond it."""

    if tier == "universal":
        mode = """Operating Mode: DIRECTIVE
You are the guide. The creator tells you what they want to do. You handle the rest. Tools are invisible infrastructure. You select the right tool, platform, partner, or community for this moment in their journey. Decisions are made for them based on what you know about their path.

When routing to tools, resources, or opportunities:
- Name the specific tool/program/room
- Explain why THIS one, at THIS moment
- Include the next concrete step
- Provide the presence of confidence: you belong here, here's why"""

    else:  # pro
        mode = """Operating Mode: PEER ADVISOR
You are a peer. The creator directs. You advise. Full toolkit is visible and organized by curation rank. You surface options with reasoning — why each fits, what differentiates them, what this creator brings to each room.

When offering options:
- Present 2-3 curated alternatives with clear context
- Explain the reasoning for each
- Name what this creator's specific strengths bring to each path
- Let them choose. Your job is informed presence, not decisions"""

    return base_prompt + "\n\n" + mode


def get_formation_context(email: str) -> dict:
    """Fetch creator's formation data from Supabase"""
    try:
        response = supabase.table("formations").select("*").eq("email", email).single().execute()
        return response.data or {}
    except Exception as e:
        logger.warning(f"Formation context fetch failed for {email}: {str(e)}")
        return {}


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
    Multi-turn Claude conversation endpoint for formation interviews
    
    Request body:
    {
        "email": "creator@example.com",
        "messages": [
            {"role": "user", "content": "What should I make next?"},
            ...
        ],
        "tier": "universal" | "pro",  # optional, defaults to "universal"
        "systemPrompt": "custom system prompt"  # optional, overrides tier default
    }
    
    Response:
    {
        "role": "assistant",
        "content": "FutureYou response...",
        "tier": "universal" | "pro",
        "timestamp": "ISO-8601"
    }
    """
    try:
        data = request.get_json()
        email = data.get("email")
        messages = data.get("messages", [])
        tier = data.get("tier", "universal")
        custom_system_prompt = data.get("systemPrompt")

        # Validate required fields
        if not messages or not isinstance(messages, list):
            return jsonify({"error": "messages array is required"}), 400

        # Get formation context
        formation = get_formation_context(email)

        # Build system prompt
        if custom_system_prompt:
            system_prompt = custom_system_prompt
        else:
            system_prompt = get_tier_system_prompt(tier)

        # Add formation context to system prompt if available
        if formation:
            formation_context = f"\n\nCreator Journey Context:\n"
            if formation.get("archetype"):
                formation_context += f"Archetype: {formation['archetype']}\n"
            if formation.get("stage"):
                formation_context += f"Current Stage: {formation['stage']}\n"
            if formation.get("goals"):
                formation_context += f"Goals: {formation['goals']}\n"
            if formation.get("summary"):
                formation_context += f"Story: {formation['summary']}\n"
            system_prompt += formation_context

        # Call Claude API
        response = anthropic_client.messages.create(
            model="claude-3-opus-20250729",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )

        # Extract response text
        assistant_message = response.content[0].text if response.content else ""

        return jsonify({
            "role": "assistant",
            "content": assistant_message,
            "tier": tier,
            "timestamp": datetime.utcnow().isoformat(),
            "model": "claude-3-opus-20250729"
        }), 200

    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to process message: {str(e)}"}), 500


@app.route("/api/formation/submit", methods=["POST"])
def formation_submit():
    """
    Submit formation data to Supabase
    
    Request body:
    {
        "email": "creator@example.com",
        "archetype": "...",
        "stage": "...",
        "goals": "...",
        "summary": "...",
        "data": { ... } // Raw JSON data
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
            "archetype": data.get("archetype"),
            "stage": data.get("stage"),
            "goals": data.get("goals"),
            "summary": data.get("summary"),
            "data": data.get("data", {}),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Upsert to Supabase (insert or update)
        response = supabase.table("formations").upsert(record).execute()

        return jsonify({
            "status": "submitted",
            "email": email,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Formation submit error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/request", methods=["POST"])
def auth_request():
    """
    Request magic link via Resend email
    
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

        # Generate magic link token (simplified — use uuid in production)
        import uuid
        token = str(uuid.uuid4())

        # In production, store token in Supabase with expiry
        # For now, just acknowledge the request
        logger.info(f"Magic link requested for {email}")

        return jsonify({
            "status": "link_sent",
            "email": email,
            "message": "Check your email for login link"
        }), 200

    except Exception as e:
        logger.error(f"Auth request error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/test-request", methods=["POST"])
def test_request():
    """
    Echo/debug endpoint for testing request body
    """
    data = request.get_json()
    return jsonify({
        "received": data,
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "internal server error"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
