"""
╔════════════════════════════════════════════════════════════════════════════╗
║ FILE: main.py                                                              ║
║ VERSION: Phase 10.19 Corrected + SDK Fix                                   ║
║ CREATED: April 29, 2026                                                    ║
║ MODIFIED: April 30, 2026 - 03:45 UTC                                       ║
║ STATUS: Ready for Deployment                                               ║
║ DEPLOYMENT TARGET: Cloud Run (studioyou-api, us-east1)                     ║
║                                                                            ║
║ PURPOSE:                                                                   ║
║ Backend API for StudioYou platform. Handles formation submissions, magic   ║
║ link generation via Resend, session management, Claude chat via SDK, and   ║
║ Supabase data persistence.                                                ║
║                                                                            ║
║ CRITICAL FIX FROM PHASE 10.18:                                             ║
║ - Changed from requests.post() to Anthropic Python SDK                     ║
║ - Uses: from anthropic import Anthropic                                    ║
║ - Eliminates direct HTTP calls to api.anthropic.com                        ║
║ - Fixes 404 errors on formation_chat and chat endpoints                    ║
║                                                                            ║
║ KEY FUNCTIONS:                                                             ║
║ - send_magic_link() — Email generation + Resend integration               ║
║ - formation_chat() — Claude-powered formation conversation (SDK)           ║
║ - chat() — General Claude chat endpoint (SDK)                              ║
║ - verify_magic_link() — Token validation + session creation               ║
║ - POST /api/formation — Formation submission endpoint                     ║
║                                                                            ║
║ DEPENDENCIES:                                                              ║
║ - anthropic (Claude Python SDK) — REQUIRED                                 ║
║ - flask (Web framework)                                                    ║
║ - flask_cors (CORS handling)                                               ║
║ - requests (HTTP client for Resend)                                        ║
║ - Supabase (Database)                                                      ║
║ - Resend (Email service)                                                   ║
║                                                                            ║
║ ENVIRONMENT VARIABLES REQUIRED:                                            ║
║ - ANTHROPIC_API_KEY                                                        ║
║ - RESEND_API_KEY                                                           ║
║ - SUPABASE_URL                                                             ║
║ - SUPABASE_KEY                                                             ║
║ - FRONTEND_URL (studioyou.app)                                             ║
║ - REACTOR_POOL_URL                                                         ║
║                                                                            ║
║ DEPLOYMENT INSTRUCTIONS:                                                   ║
║ 1. cd ~/Projects/studioyou-backend                                         ║
║ 2. cp /path/to/main_corrected.py main.py                                   ║
║ 3. git add main.py                                                         ║
║ 4. git commit -m "Phase 10.19+SDK: Use Anthropic SDK for Claude calls"     ║
║ 5. git push origin main                                                    ║
║ 6. Cloud Run auto-rebuilds and deploys                                     ║
║                                                                            ║
║ AUTHOR: Claude (Anthropic)                                                 ║
║ SOURCE: StudioYou Phase 10.19 + SDK Fix                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
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
SUPABASE_KEY      = os.environ.get("SUPABASE_SERVICE_KEY", "")
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
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.get(url, headers=SUPABASE_HEADERS, params=params)
    r.raise_for_status()
    return r.json() if r.text else []

def sb_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.post(url, headers=SUPABASE_HEADERS, json=data)
    r.raise_for_status()
    return r.json() if r.text else {}

def sb_patch(table, match, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.patch(url, headers=SUPABASE_HEADERS, params=match, json=data)
    r.raise_for_status()
    return r.json() if r.text else {}

# ── MAGIC LINK ────────────────────────────────────────────────────────────────

def send_magic_link(email, token, is_new_user=True, first_name=None):
    link = f"{FRONTEND_URL}/dashboard.html?token={token}"
    subject = "Your studio is ready." if is_new_user else "Welcome back to your studio."

    if first_name and "@" in first_name:
        first_name = None

    try:
        formations = sb_get("formations", {"email": f"eq.{email}"})
        formation_data = json.loads(formations[0].get("data", "{}")) if formations else {}
        if not first_name:
            candidate = formation_data.get("firstName", "").strip()
            if candidate and "@" not in candidate:
                first_name = candidate
        if not first_name:
            raw_name = (
                formation_data.get("creatorName") or
                formation_data.get("creator_name") or
                formation_data.get("reservationName") or
                ""
            )
            if raw_name and "@" not in raw_name:
                first_name = raw_name.strip().split()[0].capitalize()
        if not first_name:
            first_name = "Creator"
        studio_name = formation_data.get("studioName") or "Your Studio"
        logger.info(f"[send_magic_link] email={email} resolved first_name={first_name!r} studio={studio_name!r}")
    except Exception as e:
        logger.warning(f"[send_magic_link] formation lookup failed for {email}: {e}")
        first_name = first_name or "Creator"
        studio_name = "Your Studio"

    cta_label = "Enter Your Studio" if is_new_user else "Return to Your Studio"
    line1 = "FutureYou has been formed. Your studio lot is built and waiting." if is_new_user else "Everything you built is right where you left it."
    line2 = "One click and you're on the lot." if is_new_user else "One click and you're back on the lot."

    body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body,table,td,p,a{{margin:0;padding:0;border:0;font-family:'Helvetica Neue',Arial,sans-serif}}
  body{{background:#06091a}}
  img{{border:0;display:block}}
  a.btn{{display:inline-block;background:#00c8ff;color:#06091a;text-decoration:none;font-weight:700;font-size:11px;letter-spacing:.18em;text-transform:uppercase;padding:14px 36px}}
</style>
</head><body bgcolor="#06091a">

<table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#06091a">
<tr><td align="center" style="padding:48px 20px">

<table width="100%" maxwidth="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;margin:0 auto">
<tr><td align="center" style="padding:0 0 48px">
  <h2 style="color:#f0f2ff;margin:0;font-size:28px;font-weight:700">Hey {first_name},</h2>
</td></tr>
<tr><td align="center" style="padding:0 0 24px">
  <p style="color:#f0f2ff;margin:0;font-size:16px;line-height:1.6">{line1}</p>
  <p style="color:#f0f2ff;margin:16px 0 0;font-size:16px;line-height:1.6">{line2}</p>
</td></tr>
<tr><td align="center" style="padding:0 0 48px">
  <a href="{link}" class="btn">{cta_label}</a>
</td></tr>
<tr><td align="center" style="padding:24px;border-top:1px solid rgba(240,242,255,0.1)">
  <p style="color:rgba(240,242,255,0.5);margin:0;font-size:12px">StudioYou — {studio_name}</p>
</td></tr>
</table>

</td></tr>
</table>

</body></html>"""
    try:
        r = requests.post("https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            json={"from": "StudioYou <studio@studioyou.studio>",
                  "to": [email], "subject": subject, "html": body})
        return r.status_code == 200
    except Exception:
        return False

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.route("/api/formation", methods=["POST"])
def submit_formation():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    first_name = data.get("firstName", "").strip()
    last_name = data.get("lastName", "").strip()
    formation = data.get("formation", {})

    if not email or "@" not in email:
        return jsonify({"error": "Invalid email"}), 400

    try:
        token = secrets.token_urlsafe(32)
        sb_post("magic_tokens", {"email": email, "token": token, "used": False, "created_at": datetime.now(timezone.utc).isoformat()})
        
        try:
            existing = sb_get("formations", {"email": f"eq.{email}"})
            if existing:
                sb_patch("formations", {"email": f"eq.{email}"}, {"data": json.dumps(formation), "updated_at": datetime.now(timezone.utc).isoformat()})
            else:
                sb_post("formations", {"email": email, "data": json.dumps(formation), "created_at": datetime.now(timezone.utc).isoformat()})
        except Exception as e:
            logger.warning(f"Formation storage failed: {e}")

        sent = send_magic_link(email, token, is_new_user=True, first_name=first_name or None)
        return jsonify({"success": True, "message": "Check your email for your studio link.", "sent": sent})
    except Exception as e:
        logger.error(f"Formation submit error: {e}")
        return jsonify({"error": "Failed to submit formation"}), 500

@app.route("/api/formation/chat", methods=["POST", "OPTIONS"])
def formation_chat():
    """Pre-login FY formation conversation. No auth required. Uses Anthropic SDK."""
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.get_json()
    messages = data.get("messages", [])
    formation = data.get("formation", {})

    system = """You are FutureYou — the career arc navigator for StudioYou. You guide creators through formation: understanding their craft, platforms, experience, origins, 1-year goals, and biggest fears. Be direct. Ask one clear question at a time. Return ONLY valid JSON: {"message": "...", "formation": {...}, "complete": false, "suggestions": [...]}"""

    opening = messages if messages else [{"role": "user", "content": "Start the formation conversation."}]

    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-1",
            max_tokens=600,
            system=system,
            messages=opening,
        )
        text = response.content[0].text
        clean = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
        return jsonify({"success": True, **parsed})
    except Exception as e:
        logger.error(f"Formation chat error: {e}")
        return jsonify({"success": False, "error": "Failed to reach FutureYou."}), 500

@app.route("/api/auth/verify", methods=["GET"])
def verify_magic_link():
    token = request.args.get("token", "").strip()
    if not token:
        return jsonify({"error": "No token"}), 400

    try:
        rows = sb_get("magic_tokens", {"token": f"eq.{token}", "used": "eq.false"})
        if not rows:
            return jsonify({"error": "Invalid or expired token"}), 401

        row = rows[0]
        email = row.get("email")
        created = datetime.fromisoformat(row.get("created_at"))
        if datetime.now(timezone.utc) - created > timedelta(hours=TOKEN_EXPIRY_HOURS):
            return jsonify({"error": "Token expired"}), 401

        sb_patch("magic_tokens", {"token": f"eq.{token}"}, {"used": True})

        session_token = secrets.token_urlsafe(32)
        sb_post("sessions", {"email": email, "token": session_token, "created_at": datetime.now(timezone.utc).isoformat()})

        return jsonify({"success": True, "session": session_token, "email": email})
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return jsonify({"error": "Verification failed"}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    """General Claude chat. Auth optional for analytics."""
    data = request.get_json()
    messages = data.get("messages", [])

    try:
        response = anthropic_client.messages.create(
            model="claude-opus-4-1",
            max_tokens=1000,
            messages=messages,
        )
        text = response.content[0].text
        return jsonify({"success": True, "message": text})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"success": False, "error": "Chat failed"}), 500

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

    cat >> ~/Projects/studioyou-backend/main.py << 'EOF'

@app.route("/api/admin/users", methods=["GET"])
def admin_list_users():
    """List all users in formations table."""
    try:
        response = supabase_client.table("formations").select(
            "email, first_name, created_at, studio_name"
        ).execute()
        
        users = response.data or []
        return jsonify({
            "success": True,
            "count": len(users),
            "users": users
        })
    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/users/<email>", methods=["GET"])
def admin_view_user(email):
    """View full formation data for a user."""
    try:
        response = supabase_client.table("formations").select("*").eq(
            "email", email
        ).execute()
        
        user = response.data[0] if response.data else None
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        return jsonify({"success": True, "user": user})
    except Exception as e:
        logger.error(f"View user error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/users/<email>", methods=["DELETE"])
def admin_delete_user(email):
    """Delete a user and all their data."""
    try:
        response = supabase_client.table("formations").delete().eq(
            "email", email
        ).execute()
        
        return jsonify({
            "success": True,
            "message": f"User {email} deleted successfully"
        })
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

EOF
