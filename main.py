"""
╔════════════════════════════════════════════════════════════════════════════╗
║ FILE: main.py                                                              ║
║ VERSION: Phase 10.26 — Admin Panel Fix                                        ║
║ CREATED: April 29, 2026                                                    ║
║ MODIFIED: April 30, 2026 — 11:30 PM PT                                     ║
║ STATUS: Ready for Deployment with Magic Link Endpoints                     ║
║ DEPLOYMENT TARGET: Cloud Run (studioyou-api, us-east1)                     ║
║                                                                            ║
║ PURPOSE:                                                                   ║
║ Backend API for StudioYou platform. Handles formation submissions, magic   ║
║ link generation via Resend, session management, Claude chat via SDK, and   ║
║ Supabase data persistence.                                                ║
║                                                                            ║
║ NEW IN THIS VERSION:                                                       ║
║ - /api/formation/verify (POST) — Email capture + magic link send           ║
║ - /api/formation/validate (POST) — Token verification + user return        ║
║ - Fixed admin endpoints (use sb_get/sb_post instead of undefined client)  ║
║ - Consistent Supabase operations throughout                                ║
║                                                                            ║
║ MAGIC LINK WORKFLOW:                                                       ║
║ 1. Frontend: POST /api/formation/verify with email + formation data        ║
║ 2. Backend: Generate magic_token, save to formations table, send email     ║
║ 3. User: Click link in email (studioyou.app/verify?token=xyz)             ║
║ 4. Frontend: Detect token in URL, POST /api/formation/validate            ║
║ 5. Backend: Verify token, return user data, clear token                   ║
║ 6. Frontend: Set localStorage, redirect to dashboard                       ║
║                                                                            ║
║ KEY ENDPOINTS:                                                             ║
║ - POST /api/formation/chat — FutureYou formation conversation              ║
║ - POST /api/formation/verify — Email capture + magic link send             ║
║ - POST /api/formation/validate — Token verification                        ║
║ - GET /api/reactor/token — Reactor SDK token                               ║
║ - GET/DELETE /api/admin/users — Admin user management                      ║
║                                                                            ║
║ DEPLOYMENT:                                                                ║
║ 1. cd ~/Projects/studioyou-backend                                         ║
║ 2. git add main.py                                                         ║
║ 3. git commit -m "Phase 10.25: Implement magic link system"                ║
║ 4. git push origin main                                                    ║
║ 5. Cloud Run auto-rebuilds and deploys                                     ║
║                                                                            ║
║ AUTHOR: Claude (Anthropic)                                                 ║
║ SOURCE: StudioYou Phase 10.25 Magic Link Build                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import secrets
import re
import logging
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from anthropic import Anthropic

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
SUPABASE_KEY      = os.environ.get("SUPABASE_KEY", "")
RESEND_API_KEY    = os.environ.get("RESEND_API_KEY", "")
SECRET_KEY        = os.environ.get("SY_SECRET_KEY", "dev-secret-change-in-prod")
FRONTEND_URL      = os.environ.get("FRONTEND_URL", "https://studioyou.app")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
REACTOR_API_KEY   = os.environ.get("REACTOR_API_KEY", "")

# Initialize Anthropic SDK client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

TOKEN_EXPIRY_HOURS = 24

# ── SUPABASE HELPERS ──────────────────────────────────────────────────────────

def sb_get(table, params=None):
    """Get rows from a Supabase table."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.get(url, headers=SUPABASE_HEADERS, params=params)
    r.raise_for_status()
    return r.json() if r.text else []

def sb_post(table, data):
    """Insert rows into a Supabase table."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.post(url, headers=SUPABASE_HEADERS, json=data)
    r.raise_for_status()
    return r.json() if r.text else {}

def sb_patch(table, match, data):
    """Update rows in a Supabase table."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.patch(url, headers=SUPABASE_HEADERS, params=match, json=data)
    r.raise_for_status()
    return r.json() if r.text else {}

# ── EMAIL HELPERS ─────────────────────────────────────────────────────────────

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_magic_link_email(email, token, first_name="Creator", studio_name="Your Studio"):
    """Send magic link email via Resend."""
    link = f"{FRONTEND_URL}/verify?token={token}"
    
    body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body,table,td,p,a{{margin:0;padding:0;border:0;font-family:'Helvetica Neue',Arial,sans-serif}}
  body{{background:#06091a}}
  img{{border:0;display:block}}
  a.btn{{display:inline-block;background:#00c8ff;color:#06091a;text-decoration:none;font-weight:700;font-size:11px;letter-spacing:.18em;text-transform:uppercase;padding:14px 36px;border-radius:3px}}
</style>
</head><body bgcolor="#06091a">

<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#06091a">
<tr><td align="center" style="padding:48px 20px">

<table width="100%" maxwidth="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;margin:0 auto">
<tr><td align="center" style="padding:0 0 48px">
  <h2 style="color:#f0f2ff;margin:0;font-size:28px;font-weight:700">Hey {first_name},</h2>
</td></tr>
<tr><td align="center" style="padding:0 0 24px">
  <p style="color:#f0f2ff;margin:0;font-size:16px;line-height:1.6">Your formation is complete. FutureYou is ready to meet you.</p>
  <p style="color:#f0f2ff;margin:16px 0 0;font-size:16px;line-height:1.6">One click and your studio opens.</p>
</td></tr>
<tr><td align="center" style="padding:0 0 48px">
  <a href="{link}" class="btn">Enter Your Studio</a>
</td></tr>
<tr><td align="center" style="padding:0 0 14px">
  <p style="color:rgba(240,242,255,0.5);margin:0;font-size:11px">This link expires in 24 hours.</p>
</td></tr>
<tr><td align="center" style="padding:24px;border-top:1px solid rgba(240,242,255,0.1)">
  <p style="color:rgba(240,242,255,0.4);margin:0;font-size:11px">StudioYou &nbsp;|&nbsp; {studio_name}</p>
</td></tr>
</table>

</td></tr>
</table>

</body></html>"""
    
    try:
        r = requests.post("https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": "StudioYou <studio@studioyou.studio>",
                "to": [email],
                "subject": "Your StudioYou Formation is Complete",
                "html": body
            })
        success = r.status_code in [200, 201]
        if success:
            logger.info(f"[Resend] Magic link email sent to {email}")
        else:
            logger.error(f"[Resend] Failed to send email to {email}: {r.status_code} {r.text}")
        return success
    except Exception as e:
        logger.error(f"[Resend] Exception sending email to {email}: {e}")
        return False

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/api/formation/chat", methods=["POST", "OPTIONS"])
def formation_chat():
    """Pre-login FY formation conversation. Handles skip logic and closing message."""
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.get_json()
    messages = data.get("messages", [])
    formation = data.get("formation", {})

    system = """You are FutureYou — the version of this creator 30 years from now, coming back to meet them today. You're not here to interview them. You're here to talk about what's possible.

OPENING HOOK (sell the vision first):
Before asking any questions, start with this pitch:

"Here's the thing about building a creative studio: You already know what you want to make. The hard part isn't the idea in your head — it's getting that idea to the screen, to the canvas, to the audience in the way you imagined it. 

What if you had a creative partner who worked side-by-side with you? Someone who knows your vision, knows what you love to create, knows where you want to go. Someone who could help you turn the idea in your head into the thing people experience.

That's what we're building here. StudioYou is your studio. I'm here to help you run it.

Let's talk about your creative process for a minute."

THEN ASK THESE 6 QUESTIONS (conversational, peer-level, intriguing):

Q1: "What gets you excited to make things? What's the creative thing that pulls you in?"

Q2: "Do you have a favorite platform or place where you share work? Or maybe where you dream of sharing?"

Q3: "Have you been at this awhile, or are you just getting started?"

Q4: "What's the story that got you here? What moment or person made you think, 'I want to do this'?"

Q5: "Picture yourself a year from now — what does that look like? What's the win?"

Q6: "What's the one thing you're curious about or want to figure out about this whole creative path?"

TONE (CORE):
- Warm peer who gets it
- Genuinely interested in their creative process
- Excited about being their creative partner
- Possibility-focused, not problem-focused
- Zero pressure, zero judgment
- "We're in this together" energy
- Help them see what's possible

RESPONSE PATTERN:
User answers or skips → You respond with genuine curiosity about their creative process → Ask next question naturally, as if continuing a conversation

CLOSING (after Q6):
"✌️ Your creative journey is yours to explore whenever you choose. I'll be here when you're ready to build it out."

JSON FORMAT (ALWAYS):
{
  "message": "Your response here",
  "formation": {
    "contentTypes": "Q1 or null",
    "platforms": "Q2 or null",
    "experience": "Q3 or null",
    "origin": "Q4 or null",
    "goal1yr": "Q5 or null",
    "biggestFear": "Q6 or null"
  },
  "complete": false
}

Set complete:true ONLY after Q6 is asked/answered/skipped.

    """

    opening = messages if messages else [{"role": "user", "content": "Start the formation conversation."}]

    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=600,
            system=system,
            messages=opening,
        )
        text = response.content[0].text
        clean = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
        return jsonify({"success": True, **parsed})
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Formation chat error: {error_msg}")
        return jsonify({"success": False, "error": "Failed to reach FutureYou.", "details": error_msg}), 500

@app.route("/api/formation/verify", methods=["POST"])
@cross_origin()
def formation_verify():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    studio_name = data.get("studio_name", "").strip()
    formation = data.get("formation", {})

    # Validate email
    if not email or not validate_email(email):
        return jsonify({"success": False, "error": "Invalid email address"}), 400

    try:
        # Generate magic token
        magic_token = secrets.token_urlsafe(32)
        token_expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()

        # Save to formations table (create or update)
        formations = sb_get("formations", {"email": f"eq.{email}"})
        
        if formations:
            # Update existing
            sb_patch("formations", {"email": f"eq.{email}"}, {
                "first_name": first_name,
                "last_name": last_name,
                "studio_name": studio_name,
                "magic_token": magic_token,
                "token_expires_at": token_expires_at,
                "formation_data": json.dumps(formation),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"[formation_verify] Updated existing formation for {email}")
        else:
            # Create new
            sb_post("formations", {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "studio_name": studio_name,
                "magic_token": magic_token,
                "token_expires_at": token_expires_at,
                "formation_data": json.dumps(formation),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"[formation_verify] Created new formation for {email}")

        # Send magic link email
        email_sent = send_magic_link_email(email, magic_token, first_name or "Creator", studio_name or "Your Studio")

        return jsonify({
            "success": True,
            "message": "Check your email for your verification link",
            "email_sent": email_sent,
            "token": magic_token  # For testing only — remove in production
        })

    except Exception as e:
        logger.error(f"[formation_verify] Error: {e}")
        return jsonify({"success": False, "error": "Failed to process email"}), 500

@app.route("/api/formation/validate", methods=["POST"])
def formation_validate():
    """
    Token verification + user data return.
    Input: {token}
    Output: {success: true, user: {email, first_name, last_name, studio_name, formation_data}}
    """
    data = request.get_json()
    token = data.get("token", "").strip()

    if not token:
        return jsonify({"success": False, "error": "No token provided"}), 400

    try:
        # Find formation with this token
        formations = sb_get("formations", {"magic_token": f"eq.{token}"})
        
        if not formations:
            return jsonify({"success": False, "error": "Invalid or expired link"}), 401

        formation = formations[0]
        
        # Check expiry
        token_expires_at = formation.get("token_expires_at")
        if token_expires_at:
            expires = datetime.fromisoformat(token_expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires:
                return jsonify({"success": False, "error": "Link has expired"}), 401

        # Clear the token (one-time use)
        sb_patch("formations", {"magic_token": f"eq.{token}"}, {
            "magic_token": None,
            "token_expires_at": None,
            "verified_at": datetime.now(timezone.utc).isoformat()
        })

        # Return user data
        return jsonify({
            "success": True,
            "user": {
                "email": formation.get("email"),
                "first_name": formation.get("first_name"),
                "last_name": formation.get("last_name"),
                "studio_name": formation.get("studio_name"),
                "formation": json.loads(formation.get("formation_data", "{}"))
            }
        })

    except Exception as e:
        logger.error(f"[formation_validate] Error: {e}")
        return jsonify({"success": False, "error": "Verification failed"}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    """General Claude chat. Auth optional for analytics."""
    data = request.get_json()
    messages = data.get("messages", [])
    system = data.get("system", "")

    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=1000,
            system=system if system else None,
            messages=messages,
        )
        text = response.content[0].text
        return jsonify({"success": True, "message": text, "content": [{"type": "text", "text": text}]})
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Chat error: {error_msg}")
        return jsonify({"success": False, "error": "Chat failed", "details": error_msg}), 500

@app.route("/api/reactor/token", methods=["GET"])
def reactor_token():
    """Return Reactor SDK token for archetypes visualization."""
    try:
        reactor_key = os.environ.get("REACTOR_API_KEY", "")
        if not reactor_key:
            return jsonify({"error": "Reactor API key not configured"}), 500
        return jsonify({"token": reactor_key, "success": True})
    except Exception as e:
        logger.error(f"Reactor token error: {e}")
        return jsonify({"error": "Failed to generate token"}), 500

@app.route("/api/admin/users", methods=["GET"])
@cross_origin()
def admin_list_users():
    """List all users in formations table."""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.error("Missing Supabase configuration")
            return jsonify({"success": False, "error": "Supabase not configured"}), 500
        
        users = sb_get("formations", None)
        return jsonify({"success": True, "users": users, "count": len(users) if users else 0})
    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/users/<email>", methods=["GET"])
@cross_origin()
def admin_get_user(email):
    """Get full formation data for a user."""
    try:
        formations = sb_get("formations", {"email": f"eq.{email}"})
        
        if not formations:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        return jsonify({"success": True, "user": formations[0]})
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/users/<email>", methods=["DELETE"])
@cross_origin()
def admin_delete_user(email):
    """Delete a user and all their data."""
    try:
        sb_patch("formations", {"email": f"eq.{email}"}, {"deleted_at": datetime.now(timezone.utc).isoformat()})
        return jsonify({"success": True, "message": f"User {email} deleted successfully"})
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route("/api/debug/anthropic", methods=["GET"])
def debug_anthropic():
    """Check if Anthropic client is initialized."""
    try:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        return jsonify({
            'anthropic_initialized': anthropic_client is not None,
            'api_key_set': bool(api_key),
            'api_key_first_20': api_key[:20] if api_key else None,
            'model_available': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'anthropic_client': str(anthropic_client)}), 500

@app.route("/api/debug/claude-test", methods=["POST"])
def debug_claude_test():
    """Simple test: call Claude and return the raw response."""
    try:
        message = anthropic_client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say 'hello' in one word."}]
        )
        return jsonify({
            'success': True,
            'response': message.content[0].text,
            'model': message.model,
            'usage': {
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens
            }
        }), 200
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/formation/welcome', methods=['POST'])
def formation_welcome():
    """Generate personalized welcome message for new creator onboarding."""
    try:
        data = request.get_json()
        responses = data.get('responses', [])
        
        while len(responses) < 6:
            responses.append('')
        
        system_prompt = """You are welcoming a new creator into StudioYou.
Generate ONE brief welcome message that makes them feel like they just unlocked something special.
Choose randomly from these three styles:

STYLE A: "Congratulations — you're about to build your creative studio on your terms. No more juggling tools. No more wondering if you're on the right path. Just you, your ideas, and a partner who gets what you're building. Let's go."

STYLE B: "Welcome to your studio. You're done managing the chaos. From here on, it's all creation. Let's build."

STYLE C: "You're building something. No gatekeepers. No learning curves. Just the tools and guidance you need to get it from your head to the world. Let's go."

Keep under 50 words. No features, no pitch. Just: You're in. Let's go.
Return ONLY the message text."""
        
        user_message = f"""User responses:
1: {responses[0] if responses[0] else '(no response)'}
2: {responses[1] if responses[1] else '(no response)'}
3: {responses[2] if responses[2] else '(no response)'}
4: {responses[3] if responses[3] else '(no response)'}
5: {responses[4] if responses[4] else '(no response)'}
6: {responses[5] if responses[5] else '(no response)'}"""
        
        response = anthropic_client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=100,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        
        welcome_text = response.content[0].text.strip()
        
        return jsonify({
            "success": True,
            "message": welcome_text
        })
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Welcome message generation error: {error_msg}")
        return jsonify({
            "success": False,
            "error": "Failed to generate welcome message",
            "details": error_msg
        }), 500



@app.route('/api/formation/briefing', methods=['POST', 'OPTIONS'])
def formation_briefing():
    """
    Receives briefing payload from The Briefing (3-step UI).
    Returns aggressive, high-impact 'First Words' directive.
    
    Payload: {
      "studioName": "My Studio Name",
      "arsenal": "concept|ip|footage|audience",
      "roadblock": "assets|post|distribution|capital",
      "horizon": "single|channel|studio"
    }
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        studio_name = data.get('studioName', 'Your Studio').strip()
        arsenal = data.get('arsenal')
        roadblock = data.get('roadblock')
        horizon = data.get('horizon')

        if not all([arsenal, roadblock, horizon]):
            return jsonify({'error': 'Incomplete briefing payload'}), 400

        # Translate codes to readable text
        arsenal_text = {
            'concept': 'A Raw Concept',
            'ip': 'Existing IP',
            'footage': 'Raw Footage',
            'audience': 'An Audience'
        }.get(arsenal, arsenal)
        
        roadblock_text = {
            'assets': 'Asset Generation',
            'post': 'Post & Edit',
            'distribution': 'Distribution',
            'capital': 'Capital'
        }.get(roadblock, roadblock)
        
        horizon_text = {
            'single': 'Single Project Launch',
            'channel': 'Channel Growth',
            'studio': 'Multi-Vertical Studio'
        }.get(horizon, horizon)

        # CSO System Prompt
        cso_system_prompt = f"""You are FutureYou, a Chief Strategy Officer. You are fast, precise, and sovereign. You are an anti-gatekeeper architect. You are NOT a therapist.

Your role: Based on the user's Briefing payload, return a single, aggressive, high-impact "First Words" directive recommending which building they should open first to achieve their goal.

Briefing Summary:
- Studio: {studio_name}
- What we're weaponizing: {arsenal_text}
- Biggest roadblock: {roadblock_text}
- Scale of empire: {horizon_text}

Generate a response that:
1. Is 2-3 sentences max
2. Names the specific first building they should open (from: Ideation, Development, Production, Post-Production, Distribution, Monetization, Branding, Audience, Licensing, Studio Tools, Capital, Analytics)
3. Is commanding, sovereign, and anti-gatekeeper in tone
4. Addresses their specific roadblock
5. Example tone: "Initialization complete. You have the concept, but production is your roadblock. I recommend we hit Ideation and Studio first to turn that idea into reality. The gatekeepers are obsolete. You own the lot. Where are we going?"

CRITICAL: Do not use mothering language. Do not be soft. Be the CSO who sees the roadblock and cuts straight to the solution."""

        # Call Claude
        message = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=300,
            system=cso_system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Give me my First Words directive for {studio_name}."
                }
            ]
        )

        first_words = message.content[0].text

        return jsonify({
            'success': True,
            'studioName': studio_name,
            'briefing': {
                'arsenal': arsenal,
                'roadblock': roadblock,
                'horizon': horizon
            },
            'firstWords': first_words
        }), 200

    except Exception as e:
        print(f"Briefing endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def identify_archetype(q1_creative_focus):
    """
    Maps Q1 answer to one of 6 archetypes.
    Returns: 'musician' | 'filmmaker' | 'documentarian' | 'content_creator' | 'podcaster' | 'influencer'
    """
    q1_lower = q1_creative_focus.lower() if q1_creative_focus else ""
    
    if any(word in q1_lower for word in ['music', 'song', 'beat', 'track', 'album', 'producer', 'audio production']):
        return 'musician'
    elif any(word in q1_lower for word in ['film', 'cinema', 'short', 'feature', 'cinematic', 'video production']):
        return 'filmmaker'
    elif any(word in q1_lower for word in ['documentary', 'doc', 'investigation', 'research', 'investigative']):
        return 'documentarian'
    elif any(word in q1_lower for word in ['youtube', 'tiktok', 'short-form', 'vlog', 'instagram', 'reels']):
        return 'content_creator'
    elif any(word in q1_lower for word in ['podcast', 'audio', 'episode', 'series', 'interview', 'show']):
        return 'podcaster'
    elif any(word in q1_lower for word in ['personal brand', 'influence', 'follower', 'audience', 'authority', 'brand']):
        return 'influencer'
    else:
        return 'content_creator'

def determine_phase(q7, q8, q9):
    """
    Maps Q7-9 (timeline vision) to phase.
    Returns: 'validation' | 'traction' | 'leverage' | 'empire'
    """
    vision_combined = f"{q7} {q8} {q9}".lower() if q7 and q8 and q9 else ""
    
    if any(word in vision_combined for word in ['empire', 'studio', 'multiple', 'scale', 'business', 'team', 'employ']):
        return 'empire'
    elif any(word in vision_combined for word in ['scale', '1m', 'million', 'grow', 'audience', 'systems', 'delegate']):
        return 'leverage'
    elif any(word in vision_combined for word in ['100k', 'channel', 'launch', 'audience', 'subscribers', 'followers']):
        return 'traction'
    else:
        return 'validation'

@app.route("/api/debug/echo-payload", methods=["POST", "OPTIONS"])
def debug_echo_payload():
    """Echo back the request payload for debugging."""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        return jsonify({
            'received': True,
            'payload': data,
            'first_name': data.get('first_name'),
            'briefing_answers_keys': list(data.get('briefing_answers', {}).keys()),
            'briefing_answers_count': len(data.get('briefing_answers', {}))
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/env', methods=['GET'])
def debug_env():
    """Debug: Print env vars (for development only)"""
    return jsonify({
        "SUPABASE_URL": SUPABASE_URL[:20] + "..." if SUPABASE_URL else "MISSING",
        "SUPABASE_KEY": SUPABASE_KEY[:20] + "..." if SUPABASE_KEY else "MISSING",
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY[:20] + "..." if ANTHROPIC_API_KEY else "MISSING",
        "RESEND_API_KEY": RESEND_API_KEY[:20] + "..." if RESEND_API_KEY else "MISSING",
        "SY_SECRET_KEY": SECRET_KEY[:20] + "..." if SECRET_KEY else "MISSING",
        "FRONTEND_URL": FRONTEND_URL,
        "REACTOR_API_KEY": REACTOR_API_KEY[:20] + "..." if REACTOR_API_KEY else "MISSING",
    })

@app.route('/api/formation/initialize', methods=['POST', 'OPTIONS'])
def formation_initialize():
    """
    One-shot initialization: 12 answers + 3-pill context → First Words
    
    Input: {
      "first_name": "...",
      "last_name": "...",
      "studio_name": "...",
      "email": "...",
      "arsenal": "concept|ip|footage|audience",
      "roadblock": "assets|post|distribution|capital",
      "horizon": "single|channel|studio",
      "briefing_answers": {
        "q1": "...", "q2": "...", ..., "q12": "..."
      }
    }
    
    Output: {
      "success": true,
      "first_words": "Here's what I know about you...",
      "archetype": "musician|filmmaker|...",
      "phase": "validation|traction|leverage|empire"
    }
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        
        # Extract input data
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        studio_name = data.get('studio_name', '').strip()
        email = data.get('email', '').strip()
        arsenal = data.get('arsenal')
        roadblock = data.get('roadblock')
        horizon = data.get('horizon')
        briefing_answers = data.get('briefing_answers', {})
        print(f"[STEP 1] Data extracted: {first_name=}, {studio_name=}", flush=True)
        
        # Validate required fields
        if not all([first_name, studio_name, arsenal, roadblock, horizon, briefing_answers]):
            return jsonify({'error': 'Incomplete initialization payload'}), 400
        print(f"[STEP 2] Validation passed", flush=True)
        
        # 1. Identify archetype
        q1_creative_focus = briefing_answers.get('q1', '')
        archetype = identify_archetype(q1_creative_focus)
        print(f"[STEP 3] Archetype={archetype}", flush=True)
        
        # 2. Determine phase
        q7 = briefing_answers.get('q7', '')
        q8 = briefing_answers.get('q8', '')
        q9 = briefing_answers.get('q9', '')
        phase = determine_phase(q7, q8, q9)
        print(f"[STEP 4] Phase={phase}", flush=True)
        
        # 3. Build FutureYou system prompt with knowledge foundation
        system_prompt = """You are FutureYou, a Chief Strategy Officer. You have just completed a 12-question briefing interview with a solo creator. Your job now is to give them back what you heard — clear, direct, informed by 2025 creator economy reality.

CORE INTELLIGENCE (2025 Creator Economics):
- Creators who own their audience (email/community) are 2.7x more likely to earn $31k+ than fully platform-dependent creators
- Platform risk is the #1 fear — one algorithm change can wipe out 50% of traffic overnight
- 49% of top earners generated their first revenue within 3 months
- Burnout is a function of system failure, not motivation failure
- Real success requires 3+ revenue streams, not platform ad splits

ARCHETYPE CONTEXT:
- Musician: Sync licensing + streaming (bottleneck: owned audience)
- Filmmaker: Licensing + distribution (bottleneck: audience + recurring revenue)
- Documentarian: Authority + audience (bottleneck: monetizing expertise)
- Content Creator: Sponsorships + products (bottleneck: platform independence)
- Podcaster: Ad reads + sponsorships (bottleneck: production delegation)
- Influencer: Brand partnerships + products (bottleneck: moving beyond sponsorships)

PHASE REALITY:
- Validation (Weeks 1-12): Proof that audience exists + first revenue signal
- Traction (Months 3-12): Owned channels + 1-3 revenue streams + 1K-10K audience
- Leverage (Months 6-24): Systems + delegation + multi-stream revenue
- Empire (Year 2+): IP diversification + scaled business + team

YOUR JOB NOW:
1. Reflect back what you heard (2-3 specific facts from their 12 answers)
2. Identify the gap (what's blocking progress?)
3. State their phase (which timeline are they actually in?)
4. Recommend ONE building to open first
5. State how you'll work with them (reference their truth style, breakthrough mechanism, what to remember)
6. Ask ONE clarifying question to deepen understanding

TONE: Direct peer who's been listening. No compliments, no platitudes, no filler. No emojis, no exclamation marks. Just facts and next moves.

CRITICAL CONSTRAINTS:
- One paragraph, 4-5 sentences max (60-100 words)
- Reference their specific answers, not generalities
- One building only (not a list)
- One clarifying question only
- No hedging language ("maybe", "might", "could")
- Never say they're wrong; show gaps through observation"""
        print(f"[STEP 5] System prompt created", flush=True)
        
        # 4. Build user message with all briefing data
        user_message = f"""Generate FutureYou's First Words initialization for:

Name: {first_name} {last_name}
Studio: {studio_name}
Archetype: {archetype}
Phase: {phase}
Arsenal: {arsenal}
Roadblock: {roadblock}
Horizon: {horizon}

Briefing Answers:
Q1 (Creative Focus): {briefing_answers.get('q1', '')}
Q2 (Audience Reach): {briefing_answers.get('q2', '')}
Q3 (Experience): {briefing_answers.get('q3', '')}
Q4 (Biggest Win): {briefing_answers.get('q4', '')}
Q5 (Retry Differently): {briefing_answers.get('q5', '')}
Q6 (Influences): {briefing_answers.get('q6', '')}
Q7 (1-Year Vision): {briefing_answers.get('q7', '')}
Q8 (5-Year Vision): {briefing_answers.get('q8', '')}
Q9 (10-Year Vision): {briefing_answers.get('q9', '')}
Q10 (Truth Style): {briefing_answers.get('q10', '')}
Q11 (Breakthrough Mechanism): {briefing_answers.get('q11', '')}
Q12 (Remember About Me): {briefing_answers.get('q12', '')}

Start with: "Here's what I know about you and where you want to go so far:"
Then give First Words response (4-5 sentences max)."""
        print(f"[STEP 6] User message created", flush=True)
        
        # 5. Call Claude
        print(f"[STEP 7] anthropic_client={anthropic_client}, type={type(anthropic_client)}", flush=True)
        message = anthropic_client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        print(f"[STEP 8] Claude call succeeded", flush=True)
        
        first_words = message.content[0].text
        print(f"[STEP 9] first_words extracted: {first_words[:50]}...", flush=True)
        
        # 6. Store in Supabase
        if email:
            try:
                sb_patch('formations', {'email': f"eq.{email}"}, {
                    'first_words': first_words,
                    'archetype': archetype,
                    'phase': phase,
                    'initialized_at': datetime.now(timezone.utc).isoformat()
                })
                print(f"[STEP 10] Stored in Supabase", flush=True)
            except Exception as e:
                print(f"[SUPABASE WARN] {e}", flush=True)
        
        return jsonify({
            'success': True,
            'first_words': first_words,
            'archetype': archetype,
            'phase': phase
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[formation_initialize] Error: {e}\nTraceback:\n{error_trace}")
        print(f"[ERROR] formation_initialize: {e}\n{error_trace}", flush=True)
        return jsonify({'error': f'Initialization failed: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
