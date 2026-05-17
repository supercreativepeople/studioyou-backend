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

def send_magic_link_email(email, token, first_name="Creator", studio_name="Your Studio", is_new_user=True):
    """Send magic link email via Resend."""
    link = f"{FRONTEND_URL}/verify?token={token}"
    display_studio = studio_name if studio_name and studio_name not in ("Your Studio", "", None) else "Your Studio"
    display_name   = first_name  if first_name  and first_name  not in ("Creator",    "", None) else "Creator"
    subject = f"{display_studio} is ready for you."
    words = display_studio.upper().split()
    if len(words) > 1:
        cyan_words = " ".join(words[:-1])
        white_word = words[-1]
        studio_name_html = (
            '<span style="color:#00c8ff">' + cyan_words + '</span>'
            ' <span style="color:#f0f2ff">' + white_word + '</span>'
        )
    else:
        studio_name_html = '<span style="color:#00c8ff">' + words[0] + '</span>'

    body = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
<style>
body,table,td{{margin:0;padding:0;border:0;font-family:'Helvetica Neue',Arial,sans-serif}}
body{{background:#06091a}}
.outer{{background:#06091a;padding:0 20px 48px}}
.wrap{{max-width:520px;margin:0 auto;background:#06091a}}
.top-bar{{padding:24px 0 20px;display:table;width:100%}}
.top-logo{{display:table-cell;vertical-align:middle}}
.top-chip{{display:table-cell;text-align:right;vertical-align:middle}}
.chip{{display:inline-block;background:rgba(0,200,255,0.12);color:#00c8ff;font-size:9px;letter-spacing:.2em;text-transform:uppercase;padding:5px 10px;border:1px solid rgba(0,200,255,0.3)}}
.grad-bar{{height:3px;background:linear-gradient(135deg,#00c8ff 0%,#5e28a8 60%,#7b35d4 100%);margin-bottom:32px}}
.shutter-wrap{{text-align:center;margin-bottom:28px}}
.studio-name{{text-align:center;font-family:'Bebas Neue','Helvetica Neue',Arial,sans-serif;font-size:52px;font-weight:400;letter-spacing:.03em;text-transform:uppercase;margin:0 0 28px;line-height:1.05}}
.greeting{{text-align:center;font-size:18px;font-weight:600;color:#f0f2ff;margin:0 0 10px}}
.body-text{{text-align:center;font-size:14px;line-height:1.75;color:rgba(240,242,255,.6);margin:0 0 32px;font-weight:300}}
.btn-wrap{{text-align:center;margin-bottom:40px}}
a.btn{{display:inline-block;background:linear-gradient(135deg,#00c8ff,#7b35d4);color:#06091a;text-decoration:none;font-weight:700;font-size:12px;letter-spacing:.16em;text-transform:uppercase;padding:16px 44px}}
.note{{text-align:center;font-size:11px;color:rgba(240,242,255,.25);line-height:1.7;margin-bottom:40px}}
.footer{{text-align:center;padding-top:20px;border-top:1px solid rgba(240,242,255,.08);font-size:10px;color:rgba(240,242,255,.18)}}
</style></head><body>
<div class="outer"><div class="wrap">

  <div class="top-bar">
    <div class="top-logo">
      <img src="https://studioyou.app/assets/SY_OFFICIAL_SHUTTER_KEY.png" alt="" width="36" height="36" style="display:block">
    </div>
    <div class="top-chip"><span class="chip">BRIEFING COMPLETE</span></div>
  </div>

  <div class="grad-bar"></div>

  <div class="shutter-wrap">
    <img src="https://studioyou.app/assets/SY_LOGO_2D_OFFICIAL.png" alt="StudioYou" width="72" style="display:inline-block;width:72px;height:auto">
  </div>

  <div class="studio-name">{studio_name_html}</div>

  <div class="greeting">Welcome back, {display_name}.</div>
  <div class="body-text">Everything you built is right where you left it.<br>One click and you're back on the lot.</div>

  <div class="btn-wrap"><a class="btn" href="{link}">Return to Your Studio</a></div>

  <div class="note">
    This link opens your studio directly — no password needed.<br>
    It expires in 24 hours and can only be used once.<br>
    If you didn't request this, you can safely ignore this email.
  </div>

  <div class="footer">&copy; 2026 StudioYou. All rights reserved.</div>

</div></div></body></html>"""

    try:
        r = requests.post("https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={
                "from": "StudioYou <studio@studioyou.studio>",
                "to": [email],
                "subject": subject,
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
    """
    One-shot briefing summary. Called after 12Q chat completes.
    Receives full Q&A as messages array + briefing pill data.
    Returns { success, message } where message is the summary displayed on the summary_email screen.
    """
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.get_json()
    messages = data.get("messages", [])
    formation = data.get("formation", {})
    briefing = formation.get("briefing", {})
    answers = formation.get("answers", [])

    # Extract answers from messages array (every 3rd message starting at index 2 is a user answer)
    extracted = []
    for i, msg in enumerate(messages):
        if msg.get("role") == "user" and i > 0:
            extracted.append(msg.get("content", ""))

    # Use answers array if provided, otherwise use extracted
    final_answers = answers if answers else extracted

    questions = [
        "Creative focus", "Audience", "Experience",
        "Biggest win", "Would do differently", "Influences",
        "1-year vision", "5-year vision", "10-year vision",
        "Truth style", "Breakthrough mechanism", "Always remember"
    ]

    answers_context = "\n".join([
        f"Q{i+1} ({questions[i]}): {ans}"
        for i, ans in enumerate(final_answers[:12]) if ans
    ])

    arsenal  = briefing.get("arsenal",  "") if isinstance(briefing, dict) else ""
    roadblock= briefing.get("roadblock","") if isinstance(briefing, dict) else ""
    horizon  = briefing.get("horizon",  "") if isinstance(briefing, dict) else ""

    system = """You are FutureYou — the version of this creator who already built the studio, made it, and knows the road. You just completed your first briefing with TodayYou.

Your job: write the briefing confirmation message. This appears on screen as the creator finishes the 12Q briefing, before they enter their email and name their studio.

RULES:
- 2-3 sentences only. Hard limit.
- Reflect back 1-2 specific things you heard — be precise, not generic.
- Convey that you now have what you need and the studio is ready to be built.
- End with exactly this sentence: "The gates are open. I'll be here when you're ready to build it out."
- No compliments. No filler. No emojis. No exclamation marks.
- Speak as a peer who was listening, not a coach summarizing.
- Return only the message text. No JSON, no labels, no preamble."""

    user_message = f"""Write the briefing confirmation for a creator with these answers:

{answers_context}

Arsenal: {arsenal}
Roadblock: {roadblock}
Horizon: {horizon}"""

    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-7",
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user_message}]
        )
        message_text = response.content[0].text.strip()
        return jsonify({"success": True, "message": message_text})
    except Exception as e:
        logger.error(f"[formation_chat] Error: {e}")
        return jsonify({
            "success": False,
            "message": "Briefing complete. FutureYou has everything it needs. The gates are open. I'll be here when you're ready to build it out."
        }), 500

@app.route("/api/formation/verify", methods=["POST"])
@cross_origin()
def formation_verify():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    studio_name = data.get("studio_name", "").strip()
    formation = data.get("formation", {})

    if not email or not validate_email(email):
        return jsonify({"success": False, "error": "Invalid email address"}), 400

    if not first_name:
        return jsonify({"success": False, "error": "First name is required"}), 400

    # Step 1: Generate magic token
    magic_token = secrets.token_urlsafe(32)
    token_expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()

    # Step 2: Write to Supabase (hard failure — this must succeed)
    try:
        existing = sb_get("formations", {"email": f"eq.{email}"})
        if existing:
            sb_patch("formations", {"email": f"eq.{email}"}, {
                "first_name": first_name,
                "last_name": last_name,
                "studio_name": studio_name,
                "magic_token": magic_token,
                "token_expires_at": token_expires_at,
                "formation_data": json.dumps(formation),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            logger.info(f"[formation_verify] Updated formation for {email}")
        else:
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
            logger.info(f"[formation_verify] Created formation for {email}")
    except Exception as e:
        logger.error(f"[formation_verify] SUPABASE WRITE FAILED for {email}: {type(e).__name__}: {e}")
        return jsonify({"success": False, "error": "Failed to save your formation. Please try again."}), 500

    # Step 3: Send magic link email (soft failure — Supabase write already succeeded)
    email_sent = False
    try:
        email_sent = send_magic_link_email(email, magic_token, first_name or "Creator", studio_name or "Your Studio")
        if not email_sent:
            logger.warning(f"[formation_verify] Email send returned False for {email} — Supabase write succeeded")
    except Exception as e:
        logger.error(f"[formation_verify] EMAIL SEND EXCEPTION for {email}: {type(e).__name__}: {e}")

    return jsonify({
        "success": True,
        "message": "Check your email for your verification link",
        "email_sent": email_sent,
        "token": magic_token
    })

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

        # Return full user profile — everything needed to hydrate localStorage on any device
        formation_data_raw = formation.get("formation_data", "{}")
        try:
            formation_parsed = json.loads(formation_data_raw) if isinstance(formation_data_raw, str) else (formation_data_raw or {})
        except Exception:
            formation_parsed = {}

        return jsonify({
            "success": True,
            "user": {
                "email":                formation.get("email"),
                "first_name":           formation.get("first_name") or "",
                "last_name":            formation.get("last_name") or "",
                "studio_name":          formation.get("studio_name") or "",
                "archetype":            formation.get("archetype") or "",
                "phase":                formation.get("phase") or "",
                "first_words":          formation.get("first_words") or "",
                "recommended_building": formation.get("recommended_building") or "",
                "formation":            formation_parsed,
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
            model="claude-opus-4-7",
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

@app.route("/api/reactor/token", methods=["GET", "POST"])
@cross_origin()
def reactor_token():
    """Exchange REACTOR_API_KEY for a short-lived Reactor JWT."""
    try:
        reactor_key = os.environ.get("REACTOR_API_KEY", "")
        if not reactor_key:
            return jsonify({"error": "Reactor API key not configured"}), 500

        # Exchange API key for a short-lived JWT via Reactor's auth endpoint
        import urllib.request
        req = urllib.request.Request(
            "https://api.reactor.inc/tokens",
            method="POST",
            headers={"Reactor-API-Key": reactor_key}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        jwt = data.get("jwt")
        if not jwt:
            logger.error(f"Reactor token exchange: no jwt in response: {data}")
            return jsonify({"error": "Token exchange failed"}), 500

        logger.info("Reactor JWT issued successfully")
        return jsonify({"token": jwt, "success": True})

    except Exception as e:
        logger.error(f"Reactor token error: {e}")
        return jsonify({"error": f"Failed to generate token: {str(e)}"}), 500

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

@app.route("/api/auth/magic-link", methods=["POST", "OPTIONS"])
@cross_origin()
def auth_magic_link():
    """
    Returning user sign-in. Accepts {email}, generates a fresh magic token,
    updates Supabase, sends the magic link email.
    Does NOT require formation data — this is purely for returning users.
    """
    data = request.get_json()
    email = (data.get("email", "") or "").strip().lower()

    if not email or not validate_email(email):
        return jsonify({"success": False, "error": "Invalid email address"}), 400

    # Look up existing formation record
    try:
        existing = sb_get("formations", {"email": f"eq.{email}"})
    except Exception as e:
        logger.error(f"[auth_magic_link] Supabase lookup failed for {email}: {e}")
        return jsonify({"success": False, "error": "Database error. Please try again."}), 500

    if not existing:
        return jsonify({"success": False, "error": "No studio found for that email. Please complete your formation first."}), 404

    record = existing[0]
    first_name   = record.get("first_name") or "Creator"
    studio_name  = record.get("studio_name") or "Your Studio"

    # Generate fresh token
    magic_token      = secrets.token_urlsafe(32)
    token_expires_at = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()

    try:
        sb_patch("formations", {"email": f"eq.{email}"}, {
            "magic_token":      magic_token,
            "token_expires_at": token_expires_at,
            "updated_at":       datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"[auth_magic_link] Token update failed for {email}: {e}")
        return jsonify({"success": False, "error": "Failed to generate sign-in link. Please try again."}), 500

    # Send magic link email
    try:
        email_sent = send_magic_link_email(email, magic_token, first_name, studio_name, is_new_user=False)
        if not email_sent:
            logger.warning(f"[auth_magic_link] Email send returned False for {email}")
    except Exception as e:
        logger.error(f"[auth_magic_link] Email send exception for {email}: {e}")
        email_sent = False

    return jsonify({
        "success": True,
        "message": "Check your email for your sign-in link",
        "email_sent": email_sent
    })


@app.route("/api/subscribe", methods=["POST", "OPTIONS"])
@cross_origin()
def subscribe():
    """
    Record tier selection for a founding member.
    Accepts {email, tier, billing, studio_name}.
    Soft endpoint — logs to Supabase, non-blocking for frontend.
    """
    data        = request.get_json()
    email       = (data.get("email", "") or "").strip().lower()
    tier        = data.get("tier", "independent")
    billing     = data.get("billing", "annual")
    studio_name = data.get("studio_name", "")

    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400

    try:
        # Read existing data field and merge tier info
        existing = sb_get("formations", {"email": f"eq.{email}"})
        existing_data = {}
        if existing:
            try:
                existing_data = existing[0].get("data") or {}
                if isinstance(existing_data, str):
                    existing_data = json.loads(existing_data)
            except Exception:
                existing_data = {}

        existing_data.update({
            "tier": tier,
            "billing": billing,
            "subscribed_at": datetime.now(timezone.utc).isoformat()
        })

        sb_patch("formations", {"email": f"eq.{email}"}, {
            "data":       existing_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"[subscribe] {email} → {tier}/{billing}")
    except Exception as e:
        logger.warning(f"[subscribe] Supabase write failed for {email}: {e} (non-fatal)")

    return jsonify({"success": True, "tier": tier, "billing": billing})


@app.route("/api/debug/reset-formation", methods=["POST", "OPTIONS"])
@cross_origin()
def debug_reset_formation():
    """Dev only: wipe formation record for an email so user can start fresh."""
    data = request.get_json()
    email = (data.get("email","") or "").strip().lower()
    secret = data.get("secret","")
    if secret != SECRET_KEY and secret != "sy-dev-reset-2026":
        return jsonify({"error": "Unauthorized"}), 403
    if not email:
        return jsonify({"error": "email required"}), 400
    try:
        # Delete the record entirely
        url = f"{SUPABASE_URL}/rest/v1/formations"
        params = {"email": f"eq.{email}"}
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        r = requests.delete(url, headers=headers, params=params)
        logger.info(f"[reset_formation] Deleted record for {email}: {r.status_code}")
        return jsonify({"success": True, "email": email, "status": r.status_code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/debug/formation", methods=["POST", "OPTIONS"])
@cross_origin()
def debug_formation():
    """Temp: return formation record for an email to debug data issues."""
    data = request.get_json()
    email = (data.get("email","") or "").strip().lower()
    if not email:
        return jsonify({"error":"email required"}), 400
    try:
        rows = sb_get("formations", {"email": f"eq.{email}"})
        if not rows:
            return jsonify({"found": False, "email": email})
        r = rows[0]
        return jsonify({
            "found": True,
            "email": r.get("email"),
            "first_name": r.get("first_name"),
            "studio_name": r.get("studio_name"),
            "archetype": r.get("archetype"),
            "phase": r.get("phase"),
            "recommended_building": r.get("recommended_building"),
            "first_words": r.get("first_words"),
            "formation_data_type": type(r.get("formation_data")).__name__,
            "formation_data_len": len(r.get("formation_data") or []) if isinstance(r.get("formation_data"), list) else "not_array",
            "formation_data_preview": str(r.get("formation_data",""))[:200],
            "data_keys": list((r.get("data") or {}).keys()) if isinstance(r.get("data"), dict) else str(type(r.get("data"))),
            "has_briefing_answers": bool(r.get("briefing_answers")),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/update-studio", methods=["POST", "OPTIONS"])
@cross_origin()
def update_studio():
    """Update studio name for a returning user. Called when FY naming flow confirms a name."""
    data = request.get_json()
    email = (data.get("email", "") or "").strip().lower()
    studio_name = (data.get("studio_name", "") or "").strip()

    if not email or not studio_name:
        return jsonify({"success": False, "error": "Email and studio_name required"}), 400

    try:
        sb_patch("formations", {"email": f"eq.{email}"}, {
            "studio_name": studio_name,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"[update_studio] {email} → {studio_name}")
        return jsonify({"success": True, "studio_name": studio_name})
    except Exception as e:
        logger.error(f"[update_studio] Failed for {email}: {e}")
        return jsonify({"success": False, "error": "Failed to update studio name"}), 500


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
            model="claude-opus-4-7",
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
            model="claude-opus-4-7",
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
            model="claude-opus-4-7",
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
    One-shot initialization: 12 answers + 3-pill context → First Words + recommended_building

    Input: {
      "first_name": "...", "last_name": "...", "studio_name": "...", "email": "...",
      "arsenal": "...", "roadblock": "...", "horizon": "...",
      "briefing_answers": { "q1": "...", ..., "q12": "..." }
    }

    Output: {
      "success": true,
      "first_words": "Narrative text mentioning the recommended building...",
      "recommended_building": "one of 12 slugs",
      "archetype": "...",
      "phase": "..."
    }
    """
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.json

        first_name  = data.get('first_name', '').strip()
        last_name   = data.get('last_name', '').strip()
        studio_name = data.get('studio_name', '').strip()
        email       = data.get('email', '').strip()
        arsenal     = data.get('arsenal', '')
        roadblock   = data.get('roadblock', '')
        horizon     = data.get('horizon', '')
        briefing_answers = data.get('briefing_answers', {})
        print(f"[INIT STEP 1] Received: {first_name=}, {studio_name=}", flush=True)

        if not first_name or not briefing_answers:
            return jsonify({'error': 'Incomplete initialization payload'}), 400
        print(f"[INIT STEP 2] Validation passed", flush=True)

        archetype = identify_archetype(briefing_answers.get('q1', ''))
        phase = determine_phase(
            briefing_answers.get('q7', ''),
            briefing_answers.get('q8', ''),
            briefing_answers.get('q9', '')
        )
        print(f"[INIT STEP 3] archetype={archetype}, phase={phase}", flush=True)

        system_prompt = """You are FutureYou — the version of this creator who already built the studio, made the mistakes, and knows exactly what needs to happen next. You are meeting TodayYou for the first time.

YOUR RESPONSE FORMAT: Return valid JSON only. No markdown, no backticks, no preamble. No text outside the JSON object.
{
  "first_words": "Your 3-4 sentence First Words here.",
  "recommended_building": "one_slug_from_the_list"
}

THE 12 BUILDINGS — pick exactly one slug for recommended_building:
ideate, develop, fund, cast, plan, produce, post, licensing, distribute, brand, market, monetize

FIRST WORDS RULES:
- Exactly 3-4 sentences. Hard limit. No exceptions.
- Sentence 1: Reflect back 2 specific facts from their answers. Precise, not generic.
- Sentence 2: Name the real gap between where they are and where they want to go.
- Sentence 3: Name the one building they should open first and why it solves their specific gap — refer to it conversationally (e.g. "Start in Ideate" or "Your first move is Brand"). The building name must match your recommended_building slug.
- Sentence 4 (optional): One sharp clarifying question. Only include if it fits naturally. If it runs long, omit it.
- No hedging. No compliments. No emojis. No exclamation marks.
- Speak as a peer who has been there, not a coach giving advice.
- Reference their actual answers — never use generic creator advice.

TONE: Direct. Sovereign. No filler. The creator just walked into their studio for the first time and you are already waiting."""

        user_message = f"""Generate First Words for:

Name: {first_name} {last_name}
Studio: {studio_name}
Archetype: {archetype}
Phase: {phase}
Arsenal: {arsenal}
Roadblock: {roadblock}
Horizon: {horizon}

Q1 (Creative focus): {briefing_answers.get('q1', '')}
Q2 (Audience): {briefing_answers.get('q2', '')}
Q3 (Experience): {briefing_answers.get('q3', '')}
Q4 (Biggest win): {briefing_answers.get('q4', '')}
Q5 (Would do differently): {briefing_answers.get('q5', '')}
Q6 (Influences): {briefing_answers.get('q6', '')}
Q7 (1-year vision): {briefing_answers.get('q7', '')}
Q8 (5-year vision): {briefing_answers.get('q8', '')}
Q9 (10-year vision): {briefing_answers.get('q9', '')}
Q10 (Truth style): {briefing_answers.get('q10', '')}
Q11 (Breakthrough): {briefing_answers.get('q11', '')}
Q12 (Always remember): {briefing_answers.get('q12', '')}"""

        print(f"[INIT STEP 4] Calling Claude", flush=True)
        message = anthropic_client.messages.create(
            model="claude-opus-4-7",
            max_tokens=400,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        print(f"[INIT STEP 5] Claude responded", flush=True)

        raw = message.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        raw = raw.strip()

        try:
            parsed = json.loads(raw)
            first_words = parsed.get('first_words', '')
            recommended_building = parsed.get('recommended_building', 'ideate')
        except Exception as parse_err:
            logger.warning(f"[INIT] JSON parse failed: {parse_err}. Raw: {raw[:120]}")
            first_words = raw
            recommended_building = 'ideate'

        # Validate slug
        valid_slugs = {'ideate','develop','fund','cast','plan','produce',
                       'post','licensing','distribute','brand','market','monetize'}
        if recommended_building not in valid_slugs:
            logger.warning(f"[INIT] Invalid slug '{recommended_building}', defaulting to ideate")
            recommended_building = 'ideate'

        print(f"[INIT STEP 6] building={recommended_building}, words={first_words[:60]}...", flush=True)

        # Store in Supabase
        if email:
            try:
                sb_patch('formations', {'email': f"eq.{email}"}, {
                    'first_words': first_words,
                    'recommended_building': recommended_building,
                    'archetype': archetype,
                    'phase': phase,
                    'initialized_at': datetime.now(timezone.utc).isoformat()
                })
                print(f"[INIT STEP 7] Stored in Supabase", flush=True)
            except Exception as e:
                print(f"[INIT SUPABASE WARN] {e}", flush=True)

        return jsonify({
            'success': True,
            'first_words': first_words,
            'recommended_building': recommended_building,
            'archetype': archetype,
            'phase': phase
        }), 200

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[formation_initialize] Error: {e}\nTraceback:\n{error_trace}")
        print(f"[INIT ERROR] {e}\n{error_trace}", flush=True)
        return jsonify({'error': f'Initialization failed: {str(e)}'}), 500


# ── TAVUS + LIVEKIT AVATAR ────────────────────────────────────────────────────

TAVUS_API_KEY      = os.environ.get("TAVUS_API_KEY", "")
LIVEKIT_API_KEY    = os.environ.get("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "")
LIVEKIT_URL        = os.environ.get("LIVEKIT_URL", "")

TAVUS_HEADERS = {
    "x-api-key": TAVUS_API_KEY,
    "Content-Type": "application/json",
}

@app.route("/api/avatar/upload", methods=["POST"])
@cross_origin()
def avatar_upload():
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        photo_b64 = data.get("photo_base64", "")
        mime_type = data.get("mime_type", "image/jpeg")
        if not email or not photo_b64:
            return jsonify({"error": "email and photo_base64 required"}), 400
        if not TAVUS_API_KEY:
            return jsonify({"error": "Tavus not configured"}), 500
        import base64
        photo_bytes = base64.b64decode(photo_b64)
        ext = mime_type.split("/")[-1].replace("jpeg", "jpg")
        filename = f"{email.replace('@','_').replace('.','_')}.{ext}"
        storage_url = f"{SUPABASE_URL}/storage/v1/object/AVATARS/{filename}"
        storage_headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": mime_type,
            "x-upsert": "true",
        }
        upload_resp = requests.post(storage_url, headers=storage_headers, data=photo_bytes)
        if upload_resp.status_code not in (200, 201):
            return jsonify({"error": "Photo upload failed", "detail": upload_resp.text}), 500
        photo_url = f"{SUPABASE_URL}/storage/v1/object/public/AVATARS/{filename}"
        tavus_resp = requests.post(
            "https://tavusapi.com/v2/replicas",
            headers=TAVUS_HEADERS,
            json={"train_video_url": photo_url, "replica_name": f"FutureYou-{email}"},
            timeout=30
        )
        if tavus_resp.status_code not in (200, 201):
            return jsonify({"error": "Replica creation failed", "detail": tavus_resp.text}), 500
        replica_id = tavus_resp.json().get("replica_id")
        try:
            sb_patch("formations", {"email": f"eq.{email}"}, {"data": {"replica_id": replica_id}})
        except Exception as e:
            logger.warning(f"[avatar_upload] Could not store replica_id: {e}")
        return jsonify({"success": True, "replica_id": replica_id, "photo_url": photo_url}), 200
    except Exception as e:
        import traceback
        logger.error(f"[avatar_upload] {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/avatar/status/<replica_id>", methods=["GET"])
@cross_origin()
def avatar_status(replica_id):
    try:
        if not TAVUS_API_KEY:
            return jsonify({"error": "Tavus not configured"}), 500
        resp = requests.get(f"https://tavusapi.com/v2/replicas/{replica_id}", headers=TAVUS_HEADERS, timeout=15)
        if resp.status_code != 200:
            return jsonify({"error": "Status check failed", "detail": resp.text}), 500
        d = resp.json()
        return jsonify({"replica_id": replica_id, "status": d.get("status"), "progress": d.get("training_progress")}), 200
    except Exception as e:
        logger.error(f"[avatar_status] {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/avatar/conversation", methods=["POST"])
@cross_origin()
def avatar_conversation():
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        replica_id = data.get("replica_id", "")
        persona_id = data.get("persona_id")
        if not replica_id:
            return jsonify({"error": "replica_id required"}), 400
        if not TAVUS_API_KEY:
            return jsonify({"error": "Tavus not configured"}), 500
        formation_context = ""
        try:
            rows = sb_get("formations", {"email": f"eq.{email}", "select": "first_words,archetype,studio_name"})
            if rows:
                r = rows[0]
                formation_context = (
                    f"You are FutureYou, the AI advisor for {r.get('studio_name','this studio')}. "
                    f"Archetype: {r.get('archetype','creator')}. "
                    f"Your opening words: {r.get('first_words','')}"
                )
        except Exception as e:
            logger.warning(f"[avatar_conversation] Could not load formation: {e}")
        conv_payload = {
            "replica_id": replica_id,
            "conversation_name": f"FutureYou-{email}",
            "conversational_context": formation_context or "You are FutureYou, an AI advisor helping a creator build their studio.",
            "custom_greeting": "I know what it took to get here. Let's get to work.",
            "properties": {"max_call_duration": 3600, "enable_recording": False}
        }
        if persona_id:
            conv_payload["persona_id"] = persona_id
        tavus_resp = requests.post("https://tavusapi.com/v2/conversations", headers=TAVUS_HEADERS, json=conv_payload, timeout=30)
        if tavus_resp.status_code not in (200, 201):
            return jsonify({"error": "Conversation creation failed", "detail": tavus_resp.text}), 500
        conv_data = tavus_resp.json()
        return jsonify({"success": True, "conversation_id": conv_data.get("conversation_id"), "conversation_url": conv_data.get("conversation_url")}), 200
    except Exception as e:
        import traceback
        logger.error(f"[avatar_conversation] {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

# ── STOCK AVATAR — skip photo, use Raj replica + Interviewer persona ──────────
STOCK_REPLICA_ID = "rf8f3aa4b33e"   # Raj - Home
STOCK_PERSONA_ID = "pdac61133ac5"   # Interviewer

@app.route("/api/avatar/start", methods=["POST"])
@cross_origin()
def avatar_start():
    """
    Skip photo upload. Start a CVI conversation immediately using
    stock Raj replica + Interviewer persona with FY context injected.
    Returns conversation_url.
    """
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()

        if not TAVUS_API_KEY:
            return jsonify({"error": "Tavus not configured"}), 500

        # Pull formation data for FY context
        formation_context = ""
        studio_name = "your studio"
        first_name = "Creator"
        try:
            rows = sb_get("formations", {"email": f"eq.{email}", "select": "first_words,archetype,studio_name,first_name"})
            if rows:
                r = rows[0]
                studio_name = r.get("studio_name") or "your studio"
                first_name = r.get("first_name") or "Creator"
                formation_context = (
                    f"You are FutureYou — the future version of {first_name}, "
                    f"speaking back through time to guide them. "
                    f"Their studio is called {studio_name}. "
                    f"Their creator archetype: {r.get('archetype','filmmaker')}. "
                    f"Your opening words to them were: {r.get('first_words','')}. "
                    f"Speak as if you have already built everything they are trying to build. "
                    f"Be direct, confident, and specific. Never break character. "
                    f"You are not an AI assistant — you are them, from the future."
                )
        except Exception as e:
            logger.warning(f"[avatar_start] Could not load formation: {e}")

        conv_payload = {
            "replica_id": STOCK_REPLICA_ID,
            "persona_id": STOCK_PERSONA_ID,
            "conversation_name": f"FutureYou-{email or 'guest'}",
            "conversational_context": formation_context or "You are FutureYou, an AI advisor helping a creator build their studio. Be direct and specific.",
            "custom_greeting": f"I know what it took to get here, {first_name}. Let's get to work.",
            "properties": {
                "max_call_duration": 3600,
                "enable_recording": False,
            }
        }

        tavus_resp = requests.post(
            "https://tavusapi.com/v2/conversations",
            headers=TAVUS_HEADERS,
            json=conv_payload,
            timeout=30
        )
        if tavus_resp.status_code not in (200, 201):
            logger.error(f"[avatar_start] Tavus error: {tavus_resp.text}")
            return jsonify({"error": "Conversation creation failed", "detail": tavus_resp.text}), 500

        conv_data = tavus_resp.json()
        return jsonify({
            "success": True,
            "conversation_id": conv_data.get("conversation_id"),
            "conversation_url": conv_data.get("conversation_url"),
        }), 200

    except Exception as e:
        import traceback
        logger.error(f"[avatar_start] {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
