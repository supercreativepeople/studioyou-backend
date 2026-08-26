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
from livekit.api import LiveKitAPI, AccessToken, VideoGrants

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
ADMIN_KEY         = os.environ.get("SY_ADMIN_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
REACTOR_API_KEY   = os.environ.get("REACTOR_API_KEY", "")
SY_DEBUG          = os.environ.get("SY_DEBUG", "false").lower() == "true"
ADOBE_EXPRESS_CLIENT_ID  = os.environ.get("ADOBE_EXPRESS_CLIENT_ID", "")
FRAMEIO_CLIENT_ID        = os.environ.get("FRAMEIO_CLIENT_ID", "")
FRAMEIO_CLIENT_SECRET    = os.environ.get("FRAMEIO_CLIENT_SECRET", "")
ADOBE_PDF_CLIENT_ID      = os.environ.get("ADOBE_PDF_CLIENT_ID", "")
ADOBE_PDF_CLIENT_SECRET  = os.environ.get("ADOBE_PDF_CLIENT_SECRET", "")

# Initialize Anthropic SDK client
anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ── FY Model Tiers (locked Session T architecture, implemented Session AB) ──
# Tier 1 — conversational surface (/api/chat, REST fallback for voice loop)
# Tier 2 — orchestration brain (routing, formation analysis) — Fable 5 via env var,
#          Opus 4.8 fallback. Swap/rollback = change FY_ORCHESTRATION_MODEL in
#          deploy-cloudrun.yml, push. No code change.
SURFACE_MODEL       = os.environ.get("FY_SURFACE_MODEL", "claude-sonnet-4-6")
ORCHESTRATION_MODEL = os.environ.get("FY_ORCHESTRATION_MODEL", "claude-opus-4-8")

def claude_text(response):
    """Extract the first text block from a Claude response. Reasoning-class models
    (Fable 5) return thinking blocks before text, so the first content block is
    not guaranteed to carry text."""
    for block in response.content:
        if getattr(block, "type", "") == "text" and getattr(block, "text", None):
            return block.text
    return ""


SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

TOKEN_EXPIRY_HOURS = 24

# ── SUPABASE HELPERS ──────────────────────────────────────────────────────────

def check_admin_key():
    """Verify X-Admin-Key header on admin requests."""
    return request.headers.get("X-Admin-Key") == ADMIN_KEY

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

def sb_delete(table, params):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Prefer": "return=representation",
    }
    r = requests.delete(url, headers=headers, params=params, timeout=15)
    logger.info(f"[sb_delete] {table} status={r.status_code} body={r.text[:200]}")
    r.raise_for_status()
    deleted = r.json() if r.text else []
    if not deleted:
        raise Exception(f"No rows deleted from {table} — filter may not have matched")
    return deleted

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

    arsenal      = briefing.get("arsenal",      "") if isinstance(briefing, dict) else ""
    roadblock    = briefing.get("roadblock",    "") if isinstance(briefing, dict) else ""
    creator_type = briefing.get("creator_type", "") if isinstance(briefing, dict) else ""

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
Creator Type: {creator_type}"""

    try:
        response = anthropic_client.messages.create(
            model=ORCHESTRATION_MODEL,
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user_message}]
        )
        message_text = claude_text(response).strip()
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

# ── SERVER-SIDE FY SYSTEM PROMPT ─────────────────────────────────────────────

PROMPT_SYNTH_SYSTEM = (
    "You convert creative conversations into generation prompts for image/video models. "
    "Output ONLY the prompt text — no preamble, no quotes, no commentary."
)

# Minimal building metadata for server-side prompt construction.
# fyq (FutureYou quote) omitted here — add per building as needed.
_BUILDINGS_MAP = {
    "ideate":     {"title": "IDEATE",     "tag": "ideate",     "desc": "From raw idea to greenlit concept"},
    "develop":    {"title": "DEVELOP",    "tag": "develop",    "desc": "Story, format, structure, proof of concept"},
    "fund":       {"title": "FUND",       "tag": "fund",       "desc": "Capital strategy, outreach, pitch materials"},
    "cast":       {"title": "CAST",       "tag": "cast",       "desc": "Talent roles, auditions, booking"},
    "plan":       {"title": "PLAN",       "tag": "plan",       "desc": "Pre-production: schedule, crew, gear, logistics"},
    "produce":    {"title": "PRODUCE",    "tag": "produce",    "desc": "Production execution, call sheets, data"},
    "post":       {"title": "POST",       "tag": "post",       "desc": "Editorial, visual polish, audio, export"},
    "licensing":  {"title": "LICENSING",  "tag": "licensing",  "desc": "Clearances, rights, releases"},
    "distribute": {"title": "DISTRIBUTE", "tag": "distribute", "desc": "Platform strategy, asset delivery"},
    "brand":      {"title": "BRAND",      "tag": "brand",      "desc": "Visual identity, positioning"},
    "market":     {"title": "MARKET",     "tag": "market",     "desc": "Campaign strategy, asset creation"},
    "monetize":   {"title": "MONETIZE",   "tag": "monetize",   "desc": "Revenue streams, analytics"},
}


def build_fy_system_prompt(email, building_id="ideate", mode="peer"):
    """Build the FutureYou system prompt server-side from Supabase formation data.
    Replaces the client-side buildSystemPrompt() that was previously transmitted
    in every /api/chat request body (security issue raised 2026-08-19).
    """
    try:
        rows = sb_get("formations", {"email": f"eq.{email}"})
        r = rows[0] if rows else {}
    except Exception as e:
        logger.warning(f"[build_fy_system_prompt] Supabase lookup failed for {email}: {e}")
        r = {}

    first_name  = r.get("first_name")  or ""
    studio_name = r.get("studio_name") or ""
    archetype   = r.get("archetype")   or ""
    phase       = r.get("phase")       or ""
    rec         = r.get("recommended_building") or ""

    # formation_data is json.dumps(formation) — may be array (12 answers) or dict
    raw_fd = r.get("formation_data") or []
    if isinstance(raw_fd, str):
        try:
            raw_fd = json.loads(raw_fd)
        except Exception:
            raw_fd = []

    brand_story = ""
    if isinstance(raw_fd, dict):
        brand_story = raw_fd.get("brand_story", "")
        formation_answers = raw_fd.get("answers", [])
    elif isinstance(raw_fd, list):
        formation_answers = raw_fd
    else:
        formation_answers = []

    # Formation Q&A context (up to 12 answers)
    ctx = "\n".join(
        f"Q{i+1}: {a or '(skipped)'}"
        for i, a in enumerate(formation_answers[:12])
    ) if formation_answers else ""

    mode_note = (
        "DIRECTIVE MODE: You initiate. Always propose the next concrete action. Lead — do not wait to be asked."
        if mode == "independent"
        else "PEER MODE: The creator drives. You are available, sharp, never preachy. Respond when called upon."
    )

    bldg = _BUILDINGS_MAP.get(building_id, {"title": building_id, "tag": building_id, "desc": ""})

    parts = [
        f"You are FutureYou — {first_name or 'this creator'}'s future self, back to guide the build. "
        "You already built the studio, made the mistakes, and know exactly what needs to happen next.",
        "",
        f"Studio: {studio_name or '(unnamed)'} | Archetype: {archetype} | Phase: {phase}",
        f"Active building: {bldg['title']} ({bldg['tag']}) — {bldg['desc']}",
    ]
    if rec:
        parts.append(f"Recommended building: {rec}")
    if brand_story:
        parts.append(f"Brand story: {brand_story}")
    if ctx:
        parts.append(f"Formation Q&A:\n{ctx}")
    parts.extend([
        "",
        mode_note,
        "",
        "VOICE: Sovereign. Anti-gatekeeper. You do not hedge. You are not a therapist — you are a strategist who already won. Speak in short sentences, directly. No bullet points. No lists.",
        "",
        "RULES:",
        "- Never start a response with \"I\". Start with the insight.",
        "- Under 40 words unless the creator explicitly asks for depth.",
        "- End with a question or a directive — never a summary.",
        "- Never say \"great question\", \"absolutely\", \"certainly\", \"amazing\", \"that's solid\".",
        "- Never evaluate their creative output. Use additive language only: \"let's build on this\" / \"let this breathe\".",
        "- Never perform enthusiasm. Act. \"Got it. Here's the move.\"",
        "- The creator wandering into another building is not a tangent — it is a piece of the active project. Connect it, do not redirect.",
        "- If three exchanges pass with no clear direction, synthesize once: state the move, get a yes/no, then proceed.",
        "- The only thing that breaks the active thread is the creator saying they want something else.",
    ])
    return "\n".join(filter(None, parts))


@app.route("/api/chat", methods=["POST"])
def chat():
    """FY chat endpoint. Context is built server-side — client never sends system prompt."""
    data = request.get_json()
    messages = data.get("messages", [])
    context  = data.get("context", "fy_chat")  # "fy_chat" | "prompt_synth"

    if context == "prompt_synth":
        system = PROMPT_SYNTH_SYSTEM
    else:
        email       = (data.get("email", "") or "").strip().lower()
        building_id = data.get("building_id", "ideate")
        mode        = data.get("mode", "peer")
        try:
            system = build_fy_system_prompt(email, building_id, mode)
        except Exception as e:
            logger.error(f"[chat] build_fy_system_prompt failed: {e}")
            system = "You are FutureYou — a strategic guide for this creator. Be direct, specific, under 40 words."

    try:
        response = anthropic_client.messages.create(
            model=SURFACE_MODEL,
            max_tokens=1000,
            system=system,
            messages=messages,
        )
        text = claude_text(response)
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
    if not check_admin_key():
        return jsonify({"success": False, "error": "Unauthorized"}), 403
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
    if not check_admin_key():
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    try:
        formations = sb_get("formations", {"email": f"eq.{email}"})
        
        if not formations:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        return jsonify({"success": True, "user": formations[0]})
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/users/delete", methods=["POST", "OPTIONS"])
@cross_origin()
def admin_delete_user():
    """Delete a user and all their data."""
    if not check_admin_key():
        return jsonify({"success": False, "error": "Unauthorized"}), 403
    data = request.get_json()
    email = (data.get("email", "") or "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Email required"}), 400
    try:
        from urllib.parse import quote
        url = f"{SUPABASE_URL}/rest/v1/formations?email=eq.{quote(email, safe='')}"
        delete_headers = {**SUPABASE_HEADERS, "Prefer": "return=minimal"}
        r = requests.patch(url, headers=delete_headers, json={"deleted_at": datetime.now(timezone.utc).isoformat()})
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
    if not SY_DEBUG:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json()
    email = (data.get("email","") or "").strip().lower()
    secret = data.get("secret","")
    if secret != SECRET_KEY:
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
    if not SY_DEBUG:
        return jsonify({"error": "Not found"}), 404
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
    """Update studio name and/or brand_story for a user."""
    data = request.get_json()
    email = (data.get("email", "") or "").strip().lower()
    studio_name = (data.get("studio_name", "") or "").strip()
    brand_story = (data.get("brand_story", "") or "").strip()

    if not email or (not studio_name and not brand_story):
        return jsonify({"success": False, "error": "Email and at least one field required"}), 400

    try:
        patch = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if studio_name:
            patch["studio_name"] = studio_name

        if brand_story:
            # Merge brand_story into existing formation_data JSON blob
            existing = sb_get("formations", {"email": f"eq.{email}"})
            if existing:
                fd_raw = existing[0].get("formation_data", "{}")
                try:
                    fd = json.loads(fd_raw) if isinstance(fd_raw, str) else (fd_raw or {})
                except Exception:
                    fd = {}
                fd["brand_story"] = brand_story
                patch["formation_data"] = json.dumps(fd)

        sb_patch("formations", {"email": f"eq.{email}"}, patch)
        logger.info(f"[update_studio] {email} → studio={studio_name or '(unchanged)'} brand_story={'yes' if brand_story else 'no'}")
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"[update_studio] Failed for {email}: {e}")
        return jsonify({"success": False, "error": "Failed to update"}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route("/api/debug/anthropic", methods=["GET"])
def debug_anthropic():
    """Check if Anthropic client is initialized."""
    if not SY_DEBUG:
        return jsonify({"error": "Not found"}), 404
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
    if not SY_DEBUG:
        return jsonify({"error": "Not found"}), 404
    try:
        message = anthropic_client.messages.create(
            model=ORCHESTRATION_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": "Say 'hello' in one word."}]
        )
        return jsonify({
            'success': True,
            'response': claude_text(message),
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
            model=ORCHESTRATION_MODEL,
            max_tokens=100,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        
        welcome_text = claude_text(response).strip()
        
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
      "creator_type": ["YouTuber", "Short-Form Creator"]
    }
    """
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        studio_name = data.get('studioName', 'Your Studio').strip()
        arsenal = data.get('arsenal')
        roadblock = data.get('roadblock')
        creator_type = data.get('creator_type')

        if not all([arsenal, roadblock, creator_type]):
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

        creator_type_text = ', '.join(creator_type) if isinstance(creator_type, list) else creator_type

        # CSO System Prompt
        cso_system_prompt = f"""You are FutureYou, a Chief Strategy Officer. You are fast, precise, and sovereign. You are an anti-gatekeeper architect. You are NOT a therapist.

Your role: Based on the user's Briefing payload, return a single, aggressive, high-impact "First Words" directive recommending which building they should open first to achieve their goal.

Briefing Summary:
- Studio: {studio_name}
- What we're weaponizing: {arsenal_text}
- Biggest roadblock: {roadblock_text}
- Creator type: {creator_type_text}

Generate a response that:
1. Is 2-3 sentences max
2. Names the specific first building they should open (from: Ideation, Development, Production, Post-Production, Distribution, Monetization, Branding, Audience, Licensing, Studio Tools, Capital, Analytics)
3. Is commanding, sovereign, and anti-gatekeeper in tone
4. Addresses their specific roadblock
5. Example tone: "Initialization complete. You have the concept, but production is your roadblock. I recommend we hit Ideation and Studio first to turn that idea into reality. The gatekeepers are obsolete. You own the lot. Where are we going?"

CRITICAL: Do not use mothering language. Do not be soft. Be the CSO who sees the roadblock and cuts straight to the solution."""

        # Call Claude
        message = anthropic_client.messages.create(
            model=ORCHESTRATION_MODEL,
            max_tokens=300,
            system=cso_system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Give me my First Words directive for {studio_name}."
                }
            ]
        )

        first_words = claude_text(message)

        return jsonify({
            'success': True,
            'studioName': studio_name,
            'briefing': {
                'arsenal': arsenal,
                'roadblock': roadblock,
                'creator_type': creator_type
            },
            'firstWords': first_words
        }), 200

    except Exception as e:
        print(f"Briefing endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def identify_archetype(q1_creative_focus, creator_type_pill=None):
    """
    Maps creator type to archetype.
    Priority: pill selection → Q1 keyword fallback.
    Returns: 'musician' | 'live_action_filmmaker' | 'generative_filmmaker' | 'documentarian'
           | 'youtube_creator' | 'short_form_creator' | 'podcaster' | 'streamer'
           | 'content_creator' | 'influencer' | 'multi_format'
    """
    # Priority 1: explicit pill selection
    pill_map = {
        'Live Action Filmmaker':      'live_action_filmmaker',
        'Generative AI Filmmaker':    'generative_filmmaker',
        'Documentary Filmmaker':      'documentarian',
        'YouTuber':                   'youtube_creator',
        'Short-Form Creator':         'short_form_creator',
        'Musician':                   'musician',
        'Podcaster':                  'podcaster',
        'Streamer':                   'streamer',
        'Content Creator':            'content_creator',
        'Influencer':                 'influencer',
        'I Do It All':                'multi_format',
    }
    if creator_type_pill:
        # Support multi-select — use first selection as primary archetype
        pills = creator_type_pill if isinstance(creator_type_pill, list) else [creator_type_pill]
        for pill in pills:
            if pill in pill_map:
                return pill_map[pill]

    # Priority 2: Q1 free-text keyword fallback
    q1_lower = q1_creative_focus.lower() if q1_creative_focus else ""

    if any(word in q1_lower for word in ['music', 'song', 'beat', 'track', 'album', 'producer', 'audio production']):
        return 'musician'
    elif any(word in q1_lower for word in ['generative', 'ai film', 'ai cinema', 'sora', 'runway', 'gen-2', 'kling']):
        return 'generative_filmmaker'
    elif any(word in q1_lower for word in ['documentary', 'doc', 'investigation', 'investigative']):
        return 'documentarian'
    elif any(word in q1_lower for word in ['film', 'cinema', 'feature', 'cinematic', 'video production', 'live action']):
        return 'live_action_filmmaker'
    elif any(word in q1_lower for word in ['youtube', 'vlog', 'long-form', 'longform']):
        return 'youtube_creator'
    elif any(word in q1_lower for word in ['tiktok', 'short-form', 'reels', 'shorts', 'vertical']):
        return 'short_form_creator'
    elif any(word in q1_lower for word in ['podcast', 'audio', 'episode', 'interview', 'show']):
        return 'podcaster'
    elif any(word in q1_lower for word in ['stream', 'twitch', 'live', 'gaming']):
        return 'streamer'
    elif any(word in q1_lower for word in ['personal brand', 'influence', 'follower', 'authority']):
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
    if not SY_DEBUG:
        return jsonify({"error": "Not found"}), 404
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
    if not SY_DEBUG:
        return jsonify({"error": "Not found"}), 404
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
      "arsenal": "...", "roadblock": "...", "creator_type": ["..."],
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
        creator_type = data.get('creator_type', None)
        briefing_answers = data.get('briefing_answers', {})
        print(f"[INIT STEP 1] Received: {first_name=}, {studio_name=}", flush=True)

        if not first_name or not briefing_answers:
            return jsonify({'error': 'Incomplete initialization payload'}), 400
        print(f"[INIT STEP 2] Validation passed", flush=True)

        archetype = identify_archetype(briefing_answers.get('q1', ''), creator_type)
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
Creator Type: {creator_type}

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
            model=ORCHESTRATION_MODEL,
            max_tokens=400,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        print(f"[INIT STEP 5] Claude responded", flush=True)

        raw = claude_text(message).strip()
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


# ── LIVEKIT AVATAR ────────────────────────────────────────────────────────────

LIVEKIT_API_KEY    = os.environ.get("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "")
LIVEKIT_URL        = os.environ.get("LIVEKIT_URL", "")

# Building slug -> knowledge/buildings/*.md spec file. Only buildings with a
# completed spec go here. Add an entry the day a building's spec ships —
# until then that building runs on section titles alone (current behavior
# for every building except ideate).
BUILDING_SPEC_FILES = {
    "ideate": "FY_IDEATE_SUBAGENT_SPEC.md",
    "develop": "FY_DEVELOP_SUBAGENT_SPEC.md",
}

def _fetch_building_spec(building_slug):
    """
    Pulls the authoritative step schema for the active building from the
    knowledge base so the live agent actually has the section/step
    structure to follow, instead of improvising its own question line
    with only a section title to go on. Best-effort — returns None on any
    failure so a knowledge-base outage never blocks a session from
    starting.
    """
    fname = BUILDING_SPEC_FILES.get(building_slug)
    if not fname:
        return None
    url = f"https://raw.githubusercontent.com/supercreativepeople/studioyou-backend/main/knowledge/buildings/{fname}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        logger.warning("[_fetch_building_spec] failed for %s: %s", building_slug, e)
    return None


# ── LIVEKIT SESSION — new FY agent dispatch endpoint ──────────────────────────
@app.route("/api/avatar/livekit-session", methods=["POST"])
@cross_origin()
def avatar_livekit_session():
    """
    Create a LiveKit room, mint a frontend access token, dispatch the
    FY agent with formation context as job metadata. Returns room_name
    and token for the frontend LiveKit React client.

    Replaces /api/avatar/start for the new LiveKit-based avatar surface.
    """
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()

        if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL]):
            return jsonify({"error": "LiveKit not configured"}), 500

        # ── Pull formation + active project from Supabase ─────────────────
        formation_context = {}
        try:
            rows = sb_get("formations", {
                "email": f"eq.{email}",
                "select": "studio_name,first_name,formation_data,data"
            })
            if rows:
                r = rows[0]
                studio_name = r.get("studio_name") or ""
                first_name = r.get("first_name") or ""

                # formation_data is stored as a JSON string
                formation_data_raw = r.get("formation_data") or "{}"
                if isinstance(formation_data_raw, str):
                    import json as _json
                    formation_data = _json.loads(formation_data_raw)
                else:
                    formation_data = formation_data_raw or {}

                briefing = formation_data.get("briefing") or {}
                answers = formation_data.get("answers") or []

                # Derive archetype from creator_type in briefing
                ct = briefing.get("creator_type", [])
                archetype = ct[0] if isinstance(ct, list) and ct else (ct if isinstance(ct, str) else "")

                # Build briefing summary
                briefing_parts = []
                if briefing.get("arsenal"):
                    briefing_parts.append(f"Strengths: {briefing['arsenal']}")
                if briefing.get("roadblock"):
                    briefing_parts.append(f"Roadblock: {briefing['roadblock']}")
                if archetype:
                    briefing_parts.append(f"Creator type: {archetype}")
                briefing_summary = " | ".join(briefing_parts)

                tier = (r.get("data") or {}).get("tier", "independent")
                formation_context = {
                    "studio_name": studio_name,
                    "first_name": first_name,
                    "archetype": archetype,
                    "briefing_summary": briefing_summary,
                    "formation_answers": answers,
                    "tier": tier,
                }

            # Pull active project
            proj_rows = sb_get("fy_projects", {
                "user_email": f"eq.{email}",
                "status": "eq.active",
                "select": "id,name,buildings,journey_progress",
                "limit": "1",
                "order": "last_accessed.desc"
            })
            if proj_rows:
                p = proj_rows[0]
                buildings = p.get("buildings") or {}
                # Find active building/section
                active_building = None
                active_section = None
                sections = []
                for bname, bdata in buildings.items():
                    if isinstance(bdata, dict) and bdata.get("state") == "active":
                        active_building = bname
                        bsections = bdata.get("sections") or {}
                        for sid, sdata in bsections.items():
                            if isinstance(sdata, dict):
                                sections.append({
                                    "id": sid,
                                    "title": sdata.get("title", sid),
                                    "status": sdata.get("status", "open")
                                })
                                if sdata.get("state") == "active":
                                    active_section = sdata.get("title", sid)
                        break

                formation_context["active_project"] = {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "active_building": active_building,
                    "active_section": active_section,
                    "sections": sections,
                }
                if active_building:
                    building_spec = _fetch_building_spec(active_building)
                    if building_spec:
                        formation_context["active_project"]["building_spec"] = building_spec

                    # Surface what's already in Vault for this building so FY
                    # actually knows what's been answered, instead of only
                    # seeing section-level open/in_progress/complete status.
                    # Without this, FY has no way to honor its own "don't
                    # re-ask an already-covered step" instruction — the vault
                    # write happens, but nothing ever reads it back into the
                    # live agent's context. Root cause of the "I answered
                    # this already" / "I don't have that" disconnect between
                    # dashboard triage and the studio building session.
                    try:
                        vault_rows = sb_get("fy_vault_entries", {
                            "project_id": f"eq.{p.get('id')}",
                            "building_slug": f"eq.{active_building}",
                            "superseded": "eq.false",
                            "order": "captured_at.asc",
                            "select": "section_name,step_title,captured_answer",
                        })
                        if vault_rows:
                            formation_context["active_project"]["captured_steps"] = [
                                {
                                    "section_name": r.get("section_name"),
                                    "step_title": r.get("step_title"),
                                    "captured_answer": r.get("captured_answer"),
                                }
                                for r in vault_rows
                            ]
                    except Exception as e:
                        logger.warning(f"[avatar_livekit_session] Vault fetch failed: {e}")

        except Exception as e:
            logger.warning(f"[avatar_livekit_session] Formation load failed: {e}")

        # Pull conversation thread from request (sent by frontend from localStorage)
        conversation_thread = data.get("conversation_thread") or []
        if conversation_thread:
            formation_context["conversation_thread"] = conversation_thread[-10:]

        # Surface tells the agent which UI it is serving (dashboard vs studio)
        surface = data.get("surface", "dashboard")
        formation_context["surface"] = surface

        # ── Create LiveKit room + mint access token ────────────────────────
        import uuid
        room_name = f"fy-{email.split('@')[0]}-{uuid.uuid4().hex[:8]}"

        # Dispatch agent — run in thread to avoid asyncio event loop conflict with Flask
        from livekit.protocol.agent_dispatch import CreateAgentDispatchRequest
        import asyncio, concurrent.futures
        lk_url = LIVEKIT_URL.replace("wss://", "https://")
        def _run_dispatch():
            async def _dispatch():
                from livekit.protocol.room import CreateRoomRequest
                lk = LiveKitAPI(url=lk_url, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
                # Room must exist before dispatch — agent won't join a phantom room
                await lk.room.create_room(CreateRoomRequest(name=room_name))
                req = CreateAgentDispatchRequest(
                    agent_name="fy-agent",
                    room=room_name,
                    metadata=json.dumps(formation_context),
                )
                await lk.agent_dispatch.create_dispatch(req)
                await lk.aclose()
            asyncio.run(_dispatch())
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(_run_dispatch).result(timeout=30)

        # Mint a frontend participant token
        token = (
            AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            .with_identity(email or "creator")
            .with_name("Creator")
            .with_grants(VideoGrants(room_join=True, room=room_name))
            .to_jwt()
        )

        return jsonify({
            "success": True,
            "room_name": room_name,
            "token": token,
            "livekit_url": LIVEKIT_URL,
        }), 200

    except Exception as e:
        import traceback
        logger.error("[avatar_livekit_session] %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/avatar/end-session", methods=["POST"])
@cross_origin()
def avatar_end_session():
    """
    Explicitly closes a LiveKit room server-side. Called by the frontend
    before it requests a new session (page reset, toggle, error recovery)
    so a stale room's agent, avatar, and TTS pipeline actually stop rather
    than lingering until LiveKit's own idle timeout — the mechanism behind
    the multi-room credit drain found in Session AE (three concurrent
    rooms in one browser session, each independently billing Runway and
    Cartesia). Best-effort: if the room is already gone, that's success,
    not an error — the frontend should never block a new session on this.
    """
    try:
        data = request.get_json() or {}
        room_name = (data.get("room_name") or "").strip()
        if not room_name:
            return jsonify({"success": True, "note": "no room_name given"}), 200
        if not all([LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL]):
            return jsonify({"error": "LiveKit not configured"}), 500

        from livekit.protocol.room import DeleteRoomRequest
        import asyncio, concurrent.futures
        lk_url = LIVEKIT_URL.replace("wss://", "https://")

        def _run_delete():
            async def _delete():
                lk = LiveKitAPI(url=lk_url, api_key=LIVEKIT_API_KEY, api_secret=LIVEKIT_API_SECRET)
                try:
                    await lk.room.delete_room(DeleteRoomRequest(room=room_name))
                finally:
                    await lk.aclose()
            asyncio.run(_delete())

        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(_run_delete).result(timeout=15)

        return jsonify({"success": True, "room_name": room_name}), 200

    except Exception as e:
        # Deleting an already-gone room throws too — log and report success
        # anyway so the frontend's reset flow is never blocked by this call.
        logger.warning("[avatar_end_session] delete_room for %s: %s", locals().get('room_name', '?'), e)
        return jsonify({"success": True, "note": str(e)}), 200

# ── SESSION CLOSER ────────────────────────────────────────────────────────────
# Fires when FY has enough to generate an action plan.
# Takes conversation messages, runs through Claude, stores to fy_* tables.

SESSION_CLOSER_PROMPT = """You are analyzing a conversation between a creator and FutureYou (their AI creative director).

Your job is to extract a structured action plan from this conversation.

Return ONLY valid JSON in this exact format, no other text:
{
  "building_slug": "one of: ideate|develop|fund|cast|plan|produce|post|licensing|distribute|brand|market|monetize",
  "section_name": "the exact section name from the building the creator should land in",
  "step_title": "the exact step title from that section the creator should start on",
  "platform": "primary platform mentioned or null",
  "session_summary": "one sentence — what was decided in this session",
  "first_deliverable": "the single most important first output the creator should produce",
  "captured_section_name": "the exact section name (within building_slug) whose step this transcript already answers, e.g. Raw Idea — or empty string if nothing in the transcript rises to a real answer",
  "captured_step_title": "the exact step title within captured_section_name that's already answered, e.g. One Sentence — or empty string",
  "captured_step_answer": "your own distilled, synthesized version of the creator's actual answer to that step, in your words, not a verbatim quote — or empty string if captured_step_title is empty",
  "actions": [
    {
      "text": "specific action item",
      "type": "task|open_building|chat",
      "target_building": "building slug if type is open_building, else null"
    }
  ]
}

Building sections and steps (use exact strings):
ideate: Raw Idea (What's the Feeling?, First Visual Instinct, One Sentence) | Gut Check (Does This Have Legs?, Is Now the Right Time?) | Hand-off (Let's Build on This, Let This Breathe)
develop: Story & Structure (What's the Format?, What's the Premise?, Who's It For?) | Script & Content (Do You Have a Script Outline or Format Bible?, What's the Structure?, Characters & Voices) | Visual & Tonal Language (What Does This Look Like?, What Does This Sound Like?, Storyboard a Scene) | Proof of Concept (Build a Sample, Does This Work?) | Pitch Readiness (Can You Explain This to a Stranger?, What Do You Need Next?)
fund: Capital Strategy (Target Budget, Funding Strategy, Outreach & Pitching)
cast: Talent (Role Specs, Audition Management, Booking)
plan: Pre-Production (Schedule & Timeline, Crew & Staffing, Gear & Equipment, Logistics & Permitting)
produce: Production (Daily Prep & Call Sheets, Capture & Execution, Data Management)
post: Post Production (Editorial, Visual Polish, Audio Post, Mastering & Export)
licensing: Rights & Clearance (Clearances & Rights, Releases)
distribute: Distribution (Platform Strategy, Asset Delivery)
brand: Identity (Visual Identity, Positioning)
market: Campaign (Campaign Strategy, Asset Creation)
monetize: Revenue (Revenue Streams, Tracking & Analytics)

Rules:
- section_name and step_title must match the exact strings above — no paraphrasing
- Pick the section and step that most directly matches where this creator should start work
- The triage conversation already captured a content-maturity type (idea/treatment/script) and a one-sentence description of the idea. Never route to a step whose core question is asking for that same thing again — specifically, ideate's "One Sentence" step and develop's "What's the Premise?" step both ask for the one-sentence logline. If the creator already gave it in this conversation, treat that step as already answered and route to the next step in the same section instead
- When you skip a step because its answer was already given in this transcript, you MUST fill captured_section_name/captured_step_title/captured_step_answer with that step's exact section/title (ideate: Raw Idea/One Sentence — develop: Story & Structure/What's the Premise?) and your distilled version of the answer. This is what actually saves the answer — routing past a step without filling these fields loses the creator's answer entirely. Leave all three empty only if no step is genuinely already answered
- actions array: minimum 3, maximum 6 items
- Each action must be specific and executable, not generic
- building_slug must reflect where the work actually happens
- first_deliverable must be concrete — a document, a video, a deck, not a vague goal
- session_summary must be one sentence, past tense, specific to this creator's situation"""


def sb_insert(table, data):
    """Insert a row into a Supabase table, return the created row."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.post(url, headers=SUPABASE_HEADERS, json=data, timeout=15)
    if resp.status_code not in (200, 201):
        raise Exception(f"Supabase insert failed [{table}]: {resp.text}")
    rows = resp.json()
    return rows[0] if isinstance(rows, list) and rows else rows


@app.route("/api/session/start", methods=["POST"])
@cross_origin()
def session_start():
    """
    Create a new fy_session record when a FY conversation begins.
    POST { email, session_type, tavus_conv_id }
    Returns { session_id }
    """
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        session_type = data.get("session_type", "avatar")
        tavus_conv_id = data.get("tavus_conv_id")

        if not email:
            return jsonify({"error": "email required"}), 400

        row = sb_insert("fy_sessions", {
            "email": email,
            "session_type": session_type,
            "status": "active",
            "tavus_conv_id": tavus_conv_id,
            "exchange_count": 0,
        })

        return jsonify({"success": True, "session_id": row.get("id")}), 200

    except Exception as e:
        import traceback
        logger.error(f"[session_start] {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


# ── VAULT ─────────────────────────────────────────────────────────────────────
# Persists step answers FY has refined into something usable. Session AD —
# closes the gap flagged since Session AC: no persistence existed for anything
# a creator provides through conversation, only generated tool outputs
# (images, video) ever made it into the Vault before this.

def _write_vault_entry(project_id, building_slug, section_name, step_title, captured_answer, raw_thread=None):
    """
    Shared vault-write path — supersede any prior entry for this exact step,
    then insert the new one. Used by both the /api/vault/capture endpoint
    (agent-driven, mid-building captures) and session_close (triage-driven
    backfill, so a logline given during dashboard routing doesn't vanish
    the moment the creator lands in the destination building).
    """
    sb_patch("fy_vault_entries", {
        "project_id": f"eq.{project_id}",
        "building_slug": f"eq.{building_slug}",
        "section_name": f"eq.{section_name}",
        "step_title": f"eq.{step_title}",
        "superseded": "eq.false",
    }, {"superseded": True})

    entry = {
        "project_id": project_id,
        "building_slug": building_slug,
        "section_name": section_name,
        "step_title": step_title,
        "captured_answer": captured_answer,
        "raw_thread": raw_thread,
    }
    created = sb_post("fy_vault_entries", entry)
    return created[0] if isinstance(created, list) and created else created


@app.route("/api/vault/capture", methods=["POST"])
@cross_origin()
def vault_capture():
    """
    Persist a Vault entry when FY has refined a creator's answer to a step
    into something concrete and usable. Called by studio.html on receiving a
    fy_vault_capture data message from the agent's capture_vault_entry tool.

    Body: { project_id, building_slug, section_name, step_title,
            captured_answer, raw_thread (optional list of {role, content}) }
    """
    try:
        body = request.get_json(force=True) or {}
        project_id = (body.get("project_id") or "").strip()
        building_slug = (body.get("building_slug") or "").strip()
        section_name = (body.get("section_name") or "").strip()
        step_title = (body.get("step_title") or "").strip()
        captured_answer = (body.get("captured_answer") or "").strip()
        raw_thread = body.get("raw_thread")

        if not project_id or not building_slug or not section_name or not step_title or not captured_answer:
            return jsonify({
                "success": False,
                "error": "project_id, building_slug, section_name, step_title, and captured_answer are required"
            }), 400

        row = _write_vault_entry(project_id, building_slug, section_name, step_title, captured_answer, raw_thread)
        return jsonify({"success": True, "entry": row}), 200

    except Exception as e:
        import traceback
        logger.error(f"[vault_capture] {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/vault/list", methods=["GET"])
@cross_origin()
def vault_list():
    """
    List current (non-superseded) Vault entries for a project, optionally
    filtered to one building. Used to populate the Vault panel on load.

    Query params: project_id (required), building_slug (optional)
    """
    try:
        project_id = (request.args.get("project_id") or "").strip()
        building_slug = (request.args.get("building_slug") or "").strip()

        if not project_id:
            return jsonify({"success": False, "error": "project_id required"}), 400

        params = {
            "project_id": f"eq.{project_id}",
            "superseded": "eq.false",
            "order": "captured_at.asc",
        }
        if building_slug:
            params["building_slug"] = f"eq.{building_slug}"

        rows = sb_get("fy_vault_entries", params)
        return jsonify({"success": True, "entries": rows}), 200

    except Exception as e:
        import traceback
        logger.error(f"[vault_list] {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/close", methods=["POST"])
@cross_origin()
def session_close():
    """
    Close a FY session, generate action plan via Claude, store to fy_* tables.
    POST {
      email,
      session_id,
      exchange_count,
      messages: [ { role: 'user'|'assistant', content: '...' } ]
    }
    Returns { plan_id, building_slug, session_summary, first_deliverable, actions }
    """
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        session_id = data.get("session_id")
        exchange_count = data.get("exchange_count", 0)
        messages = data.get("messages", [])
        project_id = (data.get("project_id") or "").strip()

        if not email or not session_id:
            return jsonify({"error": "email and session_id required"}), 400

        if not messages:
            return jsonify({"error": "messages required to generate plan"}), 400

        # Get user's current phase from formations
        phase = 1
        try:
            rows = sb_get("formations", {"email": f"eq.{email}", "select": "phase"})
            if rows and rows[0].get("phase"):
                phase_val = rows[0]["phase"]
                phase = int(phase_val) if str(phase_val).isdigit() else 1
        except Exception:
            pass

        # Build transcript for Claude
        transcript = "\n".join([
            f"{'Creator' if m['role'] == 'user' else 'FutureYou'}: {m['content']}"
            for m in messages
            if m.get("content")
        ])

        # Generate plan via Claude
        claude_resp = anthropic_client.messages.create(
            model=ORCHESTRATION_MODEL,
            max_tokens=1024,
            system=SESSION_CLOSER_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Here is the conversation transcript:\n\n{transcript}"
            }]
        )

        raw = claude_text(claude_resp).strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        plan_data = json.loads(raw.strip())

        building_slug = plan_data.get("building_slug", "ideate")
        section_name = plan_data.get("section_name", "")
        step_title = plan_data.get("step_title", "")
        platform = plan_data.get("platform")
        session_summary = plan_data.get("session_summary", "")
        first_deliverable = plan_data.get("first_deliverable", "")
        actions = plan_data.get("actions", [])
        captured_section_name = (plan_data.get("captured_section_name") or "").strip()
        captured_step_title = (plan_data.get("captured_step_title") or "").strip()
        captured_step_answer = (plan_data.get("captured_step_answer") or "").strip()

        # Backfill: the triage conversation (dashboard) already answered a
        # step in the destination building (e.g. ideate's "One Sentence"
        # logline) but that answer previously vanished the moment routing
        # completed — nothing ever wrote it to Vault, so the studio agent
        # had no way to know it existed and re-asked from scratch. Write it
        # now, same path as a normal capture_vault_entry call, so it's
        # already there by the time the building session loads.
        if project_id and captured_section_name and captured_step_title and captured_step_answer:
            try:
                _write_vault_entry(
                    project_id, building_slug, captured_section_name,
                    captured_step_title, captured_step_answer,
                    raw_thread=messages,
                )
            except Exception as e:
                logger.warning(f"[session_close] Vault backfill failed: {e}")

        # 1. Update fy_session record
        sb_patch("fy_sessions",
            {"id": f"eq.{session_id}"},
            {"status": "closed", "exchange_count": exchange_count, "closed_at": "now()"}
        )

        # 2. Insert fy_session_plan
        plan_row = sb_insert("fy_session_plans", {
            "session_id": session_id,
            "email": email,
            "building_slug": building_slug,
            "platform": platform,
            "session_summary": session_summary,
            "first_deliverable": first_deliverable,
            "phase": phase,
        })
        plan_id = plan_row.get("id")

        # 3. Insert fy_session_actions
        for i, action in enumerate(actions[:6]):
            sb_insert("fy_session_actions", {
                "session_id": session_id,
                "plan_id": plan_id,
                "email": email,
                "action_text": action.get("text", ""),
                "action_type": action.get("type", "task"),
                "target_building": action.get("target_building"),
                "sort_order": i,
                "completed": False,
                "clicked_count": 0,
            })

        return jsonify({
            "success": True,
            "plan_id": plan_id,
            "building_slug": building_slug,
            "section_name": section_name,
            "step_title": step_title,
            "platform": platform,
            "session_summary": session_summary,
            "first_deliverable": first_deliverable,
            "actions": actions,
        }), 200

    except json.JSONDecodeError as e:
        logger.error(f"[session_close] JSON parse error: {e} — raw: {raw}")
        return jsonify({"error": "Plan generation failed — could not parse Claude response"}), 500
    except Exception as e:
        import traceback
        logger.error(f"[session_close] {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/action/complete", methods=["POST"])
@cross_origin()
def session_action_complete():
    """
    Mark an action as completed or record a click.
    POST { action_id, completed (bool), click (bool) }
    """
    try:
        data = request.get_json()
        action_id = data.get("action_id")
        completed = data.get("completed")
        click = data.get("click", False)

        if not action_id:
            return jsonify({"error": "action_id required"}), 400

        update = {}
        if completed is not None:
            update["completed"] = completed
            if completed:
                update["completed_at"] = "now()"

        url = f"{SUPABASE_URL}/rest/v1/fy_session_actions?id=eq.{action_id}"
        if click:
            # Increment click count via RPC-style update
            click_resp = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/increment_action_click",
                headers=SUPABASE_HEADERS,
                json={"action_id": action_id},
                timeout=10
            )

        if update:
            resp = requests.patch(url, headers=SUPABASE_HEADERS, json=update, timeout=10)
            if resp.status_code not in (200, 204):
                return jsonify({"error": "Update failed"}), 500

        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"[session_action_complete] {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/session/journey", methods=["GET"])
@cross_origin()
def session_journey():
    """
    Return the full Journey Engine record for a user.
    GET /api/session/journey?email=...
    Returns plans + actions in display order.
    """
    try:
        email = request.args.get("email", "").strip().lower()
        if not email:
            return jsonify({"error": "email required"}), 400

        # Get all plans for this user
        plans_url = f"{SUPABASE_URL}/rest/v1/fy_session_plans?email=eq.{email}&order=created_at.desc"
        plans_resp = requests.get(plans_url, headers=SUPABASE_HEADERS, timeout=15)
        plans = plans_resp.json() if plans_resp.status_code == 200 else []

        if not plans:
            return jsonify({"success": True, "plans": []}), 200

        # Get all actions for this user
        actions_url = f"{SUPABASE_URL}/rest/v1/fy_session_actions?email=eq.{email}&order=sort_order.asc"
        actions_resp = requests.get(actions_url, headers=SUPABASE_HEADERS, timeout=15)
        actions = actions_resp.json() if actions_resp.status_code == 200 else []

        # Group actions by plan_id
        actions_by_plan = {}
        for a in actions:
            pid = a.get("plan_id")
            if pid not in actions_by_plan:
                actions_by_plan[pid] = []
            actions_by_plan[pid].append(a)

        # Attach actions to plans
        for plan in plans:
            plan["actions"] = actions_by_plan.get(plan["id"], [])

        return jsonify({"success": True, "plans": plans}), 200

    except Exception as e:
        logger.error(f"[session_journey] {e}")
        return jsonify({"error": str(e)}), 500

# ── MODEL GATEWAY ─────────────────────────────────────────────────────────────
# Unified model invocation endpoint. Canvas never calls providers directly.
# Routing: partner-direct API → Fal.ai fallback
# Response format is consistent regardless of provider.

FAL_API_KEY = os.environ.get("FAL_API_KEY", "")

# Partner-direct registry
# Keys are task identifiers. Values define the direct route.
# Tasks NOT in this registry fall through to Fal.ai.
PARTNER_DIRECT_REGISTRY = {
    # Seedance video generation — direct when enterprise terms apply
    # "seedance_video": {"provider": "seedance", "endpoint": "TBD"},

    # StyleFrame storyboard — direct when API confirmed
    # "styleframe_storyboard": {"provider": "styleframe", "endpoint": "TBD"},

    # Reactor environment — already wired via /api/reactor/token
    # Routes through existing Reactor endpoints, not this gateway
}

# Fal.ai model routing table
# Maps task identifiers to Fal.ai endpoint paths
FAL_MODEL_REGISTRY = {
    # Video generation
    "video_generate":        "fal-ai/seedance-v1-lite",
    "video_generate_pro":    "fal-ai/seedance-v1-pro",
    "video_generate_kling":  "fal-ai/kling-video/v2/master/text-to-video",

    # Image generation
    "image_generate":        "fal-ai/flux/schnell",
    "image_generate_pro":    "fal-ai/flux-pro/v1.1",
    "image_storyboard":      "fal-ai/flux/dev",

    # Audio / music
    "music_generate":        "fal-ai/stable-audio",

    # Upscale / enhance
    "image_upscale":         "fal-ai/clarity-upscaler",
    "video_upscale":         "fal-ai/video-upscaler",
}

def invoke_fal(endpoint_path, params):
    """
    POST to Fal.ai queue endpoint.
    Returns the result dict or raises on failure.
    """
    if not FAL_API_KEY:
        raise Exception("FAL_API_KEY not configured")

    # Submit to queue
    submit_url = f"https://queue.fal.run/{endpoint_path}"
    submit_resp = requests.post(
        submit_url,
        headers={
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json",
        },
        json=params,
        timeout=30,
    )
    if submit_resp.status_code not in (200, 201):
        raise Exception(f"Fal.ai submit failed [{submit_resp.status_code}]: {submit_resp.text}")

    submit_data = submit_resp.json()
    request_id = submit_data.get("request_id")
    status_url = submit_data.get("status_url") or f"https://queue.fal.run/{endpoint_path}/requests/{request_id}/status"
    result_url = submit_data.get("response_url") or f"https://queue.fal.run/{endpoint_path}/requests/{request_id}"

    # Poll status (max 120s, 3s interval)
    import time
    for _ in range(40):
        time.sleep(3)
        status_resp = requests.get(
            status_url,
            headers={"Authorization": f"Key {FAL_API_KEY}"},
            timeout=15,
        )
        if status_resp.status_code != 200:
            continue
        status_data = status_resp.json()
        status = status_data.get("status")
        if status == "COMPLETED":
            break
        if status in ("FAILED", "CANCELLED"):
            raise Exception(f"Fal.ai job {status}: {status_data}")
    else:
        raise Exception("Fal.ai job timed out after 120s")

    # Fetch result
    result_resp = requests.get(
        result_url,
        headers={"Authorization": f"Key {FAL_API_KEY}"},
        timeout=30,
    )
    if result_resp.status_code != 200:
        raise Exception(f"Fal.ai result fetch failed [{result_resp.status_code}]: {result_resp.text}")

    return result_resp.json()


@app.route("/api/model/invoke", methods=["POST", "OPTIONS"])
@cross_origin()
def model_invoke():
    """
    Unified model gateway. Called from studio.html canvas.

    POST {
      "task":     "video_generate" | "image_generate" | "image_storyboard" | ...,
      "building": "produce" | "develop" | "post" | ...,
      "tier":     "independent" | "player" | "operator",
      "params":   { ...task-specific payload... },
      "email":    "user@example.com"  (optional, for logging)
    }

    Returns {
      "success": true,
      "output":  { ...provider response... },
      "provider": "fal" | "seedance" | "styleframe" | ...,
      "model":   "fal-ai/seedance-v1-lite" | ...,
      "task":    "video_generate"
    }
    """
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.get_json()
    task     = (data.get("task") or "").strip()
    building = (data.get("building") or "").strip()
    tier     = (data.get("tier") or "independent").strip()
    params   = data.get("params") or {}
    email    = (data.get("email") or "").strip().lower()

    if not task:
        return jsonify({"success": False, "error": "task is required"}), 400

    logger.info(f"[model_invoke] task={task} building={building} tier={tier} email={email}")

    # Check partner-direct registry first
    if task in PARTNER_DIRECT_REGISTRY:
        route = PARTNER_DIRECT_REGISTRY[task]
        # Partner-direct routes implemented per-partner as they come online
        # For now return not-yet-wired so canvas can handle gracefully
        return jsonify({
            "success": False,
            "error": f"Partner-direct route for '{task}' not yet wired",
            "provider": route["provider"],
        }), 501

    # Resolve Fal.ai endpoint
    fal_model = FAL_MODEL_REGISTRY.get(task)
    if not fal_model:
        return jsonify({
            "success": False,
            "error": f"Unknown task '{task}'. Check FAL_MODEL_REGISTRY.",
        }), 400

    # Tier gate: player-only tasks
    player_only_tasks = {"video_generate_pro", "video_generate_kling"}
    if task in player_only_tasks and tier not in ("player", "operator"):
        return jsonify({
            "success": False,
            "error": "This generation type requires Player tier.",
            "upgrade_required": True,
        }), 403

    try:
        output = invoke_fal(fal_model, params)
        logger.info(f"[model_invoke] SUCCESS task={task} model={fal_model}")
        return jsonify({
            "success":  True,
            "output":   output,
            "provider": "fal",
            "model":    fal_model,
            "task":     task,
        }), 200

    except Exception as e:
        logger.error(f"[model_invoke] FAILED task={task} model={fal_model}: {e}")
        return jsonify({
            "success": False,
            "error":   str(e),
            "task":    task,
            "model":   fal_model,
        }), 500


@app.route("/api/model/tasks", methods=["GET"])
@cross_origin()
def model_tasks():
    """
    Returns available tasks and their routing.
    Used by canvas to know what's available before rendering action buttons.
    """
    return jsonify({
        "success": True,
        "fal_tasks": list(FAL_MODEL_REGISTRY.keys()),
        "partner_direct_tasks": list(PARTNER_DIRECT_REGISTRY.keys()),
        "fal_configured": bool(FAL_API_KEY),
    }), 200


# -- ADOBE / FRAME.IO / PDF SERVICES --
# Session P - June 5, 2026


@app.route("/api/integrations/adobe/config", methods=["GET", "OPTIONS"])
@cross_origin()
def adobe_config():
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200
    if not ADOBE_EXPRESS_CLIENT_ID:
        return jsonify({"success": False, "error": "Adobe Express not configured"}), 503
    return jsonify({"success": True, "client_id": ADOBE_EXPRESS_CLIENT_ID}), 200


@app.route("/api/integrations/frameio/auth", methods=["GET", "OPTIONS"])
@cross_origin()
def frameio_auth():
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200
    if not FRAMEIO_CLIENT_ID:
        return jsonify({"success": False, "error": "Frame.io not configured"}), 503
    auth_url = (
        "https://ims-na1.adobelogin.com/ims/authorize/v2"
        f"?client_id={FRAMEIO_CLIENT_ID}"
        "&scope=openid,AdobeID,frame.io.projects,frame.io.assets"
        "&response_type=code"
        "&redirect_uri=https://studioyou.app/auth/frameio/callback"
    )
    return jsonify({"success": True, "auth_url": auth_url}), 200


@app.route("/api/integrations/frameio/callback", methods=["POST", "OPTIONS"])
@cross_origin()
def frameio_callback():
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200
    data = request.get_json()
    code = (data.get("code") or "").strip()
    if not code:
        return jsonify({"success": False, "error": "code required"}), 400
    if not FRAMEIO_CLIENT_ID or not FRAMEIO_CLIENT_SECRET:
        return jsonify({"success": False, "error": "Frame.io not configured"}), 503
    try:
        resp = requests.post(
            "https://ims-na1.adobelogin.com/ims/token/v3",
            data={
                "grant_type": "authorization_code",
                "client_id": FRAMEIO_CLIENT_ID,
                "client_secret": FRAMEIO_CLIENT_SECRET,
                "code": code,
                "redirect_uri": "https://studioyou.app/auth/frameio/callback",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return jsonify({"success": False, "error": f"Token exchange failed: {resp.text}"}), 502
        token_data = resp.json()
        return jsonify({
            "success": True,
            "access_token": token_data.get("access_token"),
            "expires_in": token_data.get("expires_in"),
        }), 200
    except Exception as e:
        logger.error(f"[frameio_callback] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/integrations/pdf/generate", methods=["POST", "OPTIONS"])
@cross_origin()
def pdf_generate():
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200
    if not ADOBE_PDF_CLIENT_ID or not ADOBE_PDF_CLIENT_SECRET:
        return jsonify({"success": False, "error": "PDF Services not configured"}), 503
    data = request.get_json()
    html = (data.get("html") or "").strip()
    filename = (data.get("filename") or "document.pdf").strip()
    if not html:
        return jsonify({"success": False, "error": "html content required"}), 400
    try:
        token_resp = requests.post(
            "https://ims-na1.adobelogin.com/ims/token/v3",
            data={
                "grant_type": "client_credentials",
                "client_id": ADOBE_PDF_CLIENT_ID,
                "client_secret": ADOBE_PDF_CLIENT_SECRET,
                "scope": "openid,AdobeID,DCAPI",
            },
            timeout=15,
        )
        if token_resp.status_code != 200:
            return jsonify({"success": False, "error": f"Adobe auth failed: {token_resp.text}"}), 502
        access_token = token_resp.json().get("access_token")
        pdf_resp = requests.post(
            "https://pdf-services-ue1.adobe.io/operation/htmltopdf",
            headers={
                "Authorization": f"Bearer {access_token}",
                "x-api-key": ADOBE_PDF_CLIENT_ID,
                "Content-Type": "application/json",
            },
            json={"json": "{}", "htmlContent": html},
            timeout=30,
        )
        if pdf_resp.status_code not in (200, 201):
            return jsonify({"success": False, "error": f"PDF generation failed: {pdf_resp.text}"}), 502
        pdf_data = pdf_resp.json()
        return jsonify({
            "success": True,
            "download_url": pdf_data.get("downloadUri") or (pdf_data.get("asset") or {}).get("downloadUri"),
            "filename": filename,
        }), 200
    except Exception as e:
        logger.error(f"[pdf_generate] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ── PROJECT SYSTEM ────────────────────────────────────────────────────────────
# Session M — June 3, 2026
# Endpoints: create, list (+ auto-create), update, archive, delete, set-active

TIER_LIMITS = {
    "operator":    {"active": 10, "archive": 25},
    "independent": {"active": 3,  "archive": 15},
    "player":      {"active": 5,  "archive": 20},
}

# Default FY path per archetype — buildings FY considers required
ARCHETYPE_FY_PATH = {
    "live_action_filmmaker": ["ideate", "develop", "fund", "cast", "plan", "produce", "post", "licensing", "distribute"],
    "generative_filmmaker":  ["ideate", "develop", "produce", "post", "distribute", "market"],
    "documentarian":         ["ideate", "develop", "fund", "produce", "post", "licensing", "distribute"],
    "musician":              ["ideate", "develop", "produce", "post", "licensing", "market", "monetize"],
    "youtube_creator":       ["ideate", "develop", "produce", "post", "distribute", "market", "monetize"],
    "short_form_creator":    ["ideate", "develop", "produce", "post", "market", "monetize"],
    "podcaster":             ["ideate", "develop", "produce", "post", "distribute", "market"],
    "streamer":              ["ideate", "develop", "produce", "market", "monetize"],
    "content_creator":       ["ideate", "develop", "produce", "post", "market", "monetize"],
    "influencer":            ["ideate", "develop", "brand", "market", "monetize"],
    "multi_format":          ["ideate", "develop", "produce", "post", "distribute", "brand", "market", "monetize"],
}

ARCHETYPE_PROJECT_NAME = {
    "live_action_filmmaker": "LIVE ACTION PROJECT",
    "generative_filmmaker":  "GENAI PILOT",
    "documentarian":         "DOCUMENTARY PROJECT",
    "musician":              "MUSIC PROJECT",
    "youtube_creator":       "YOUTUBE SERIES",
    "short_form_creator":    "SHORT-FORM SERIES",
    "podcaster":             "PODCAST SERIES",
    "streamer":              "STREAMING PROJECT",
    "content_creator":       "CONTENT PROJECT",
    "influencer":            "BRAND PROJECT",
    "multi_format":          "MULTI-FORMAT PROJECT",
}

EMPTY_BUILDINGS_STATE = {
    b: {
        "state": "untouched",
        "fy_flag": None,
        "sections_visited": [],
        "steps_completed": {},
        "completion_pct": 0.0,
        "last_visited": None,
    }
    for b in ["ideate","develop","fund","cast","plan","produce","post","licensing","distribute","brand","market","monetize"]
}

def get_user_formation(email):
    """Fetch formation row for email. Returns dict or None."""
    try:
        rows = sb_get("formations", {"email": f"eq.{email}", "limit": "1"})
        return rows[0] if rows else None
    except Exception:
        return None

def fy_name_project(formation_row):
    """Generate a FY-named project from formation data."""
    archetype = (formation_row or {}).get("archetype", "content_creator") or "content_creator"
    return ARCHETYPE_PROJECT_NAME.get(archetype, "NEW PROJECT")

def fy_path_for_archetype(archetype):
    return ARCHETYPE_FY_PATH.get(archetype, ARCHETYPE_FY_PATH["content_creator"])

def count_projects(email, status):
    """Count projects by email and status."""
    try:
        rows = sb_get("fy_projects", {
            "user_email": f"eq.{email}",
            "status": f"eq.{status}",
            "select": "id",
        })
        return len(rows) if rows else 0
    except Exception:
        return 0

def compute_journey_progress(buildings_state, fy_path):
    """Recompute journey_progress from building completion across fy_path buildings."""
    if not fy_path:
        return 0.0
    totals = []
    for slug in fy_path:
        b = buildings_state.get(slug, {})
        totals.append(float(b.get("completion_pct", 0.0)))
    return round(sum(totals) / len(totals), 4) if totals else 0.0


@app.route("/api/projects/list", methods=["GET", "OPTIONS"])
@cross_origin()
def projects_list():
    """
    List all projects for a user.
    If no projects exist, auto-creates a default FY-named active project.
    Query: ?email=
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "email required"}), 400

    try:
        rows = sb_get("fy_projects", {
            "user_email": f"eq.{email}",
            "order": "last_accessed.desc",
        })

        # Auto-create default project on first dashboard load
        # Double-check with a count query before inserting to prevent race-condition duplicates
        if not rows:
            count_check = sb_get("fy_projects", {
                "user_email": f"eq.{email}",
                "select": "id",
            })
            if not count_check:
                formation = get_user_formation(email)
                archetype = (formation or {}).get("archetype", "content_creator") or "content_creator"
                name = fy_name_project(formation)
                fy_path = fy_path_for_archetype(archetype)

                new_project = {
                    "user_email": email,
                    "name": name,
                    "status": "active",
                    "fy_path": fy_path,
                    "buildings": EMPTY_BUILDINGS_STATE,
                    "journey_progress": 0.0,
                    "vault_count": 0,
                }
                created = sb_insert("fy_projects", new_project)
                rows = [created] if created else []
            else:
                rows = sb_get("fy_projects", {
                    "user_email": f"eq.{email}",
                    "order": "last_accessed.desc",
                })

        return jsonify({"success": True, "projects": rows}), 200

    except Exception as e:
        logger.error(f"[projects_list] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/create", methods=["POST", "OPTIONS"])
@cross_origin()
def projects_create():
    """
    Create a new project. Enforces tier active limit.
    Body: { email, name (optional), tier }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    body = request.get_json(force=True) or {}
    email = (body.get("email") or "").strip().lower()
    tier = (body.get("tier") or "operator").strip().lower()
    name = (body.get("name") or "").strip()

    if not email:
        return jsonify({"success": False, "error": "email required"}), 400

    limits = TIER_LIMITS.get(tier, TIER_LIMITS["operator"])
    active_count = count_projects(email, "active")

    if active_count >= limits["active"]:
        return jsonify({
            "success": False,
            "error": f"Active project limit reached ({limits['active']} for {tier} tier). Archive a project to create a new one.",
            "limit_hit": True,
        }), 400

    formation = get_user_formation(email)
    archetype = (formation or {}).get("archetype", "content_creator") or "content_creator"
    if not name:
        name = fy_name_project(formation)
    fy_path = fy_path_for_archetype(archetype)

    try:
        project = {
            "user_email": email,
            "name": name,
            "status": "active",
            "fy_path": fy_path,
            "buildings": EMPTY_BUILDINGS_STATE,
            "journey_progress": 0.0,
            "vault_count": 0,
        }
        created = sb_insert("fy_projects", project)
        return jsonify({"success": True, "project": created}), 201

    except Exception as e:
        logger.error(f"[projects_create] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/update", methods=["POST", "OPTIONS"])
@cross_origin()
def projects_update():
    """
    Update building state and/or step completions for a project.
    Recalculates journey_progress automatically.
    Body: { project_id, building_slug, state (optional), sections_visited (optional),
            steps_completed (optional), completion_pct (optional), name (optional) }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    body = request.get_json(force=True) or {}
    project_id = (body.get("project_id") or "").strip()
    building_slug = (body.get("building_slug") or "").strip()

    if not project_id:
        return jsonify({"success": False, "error": "project_id required"}), 400

    try:
        # Fetch current project
        rows = sb_get("fy_projects", {"id": f"eq.{project_id}", "limit": "1"})
        if not rows:
            return jsonify({"success": False, "error": "project not found"}), 404
        project = rows[0]

        buildings = project.get("buildings") or dict(EMPTY_BUILDINGS_STATE)
        fy_path = project.get("fy_path") or []

        # Apply building update if slug provided
        if building_slug:
            if building_slug not in buildings:
                buildings[building_slug] = {
                    "state": "untouched", "fy_flag": None,
                    "sections_visited": [], "steps_completed": {},
                    "completion_pct": 0.0, "last_visited": None,
                }
            b = buildings[building_slug]
            if "state" in body:
                b["state"] = body["state"]
            if "sections_visited" in body:
                b["sections_visited"] = body["sections_visited"]
            if "steps_completed" in body:
                b["steps_completed"] = body["steps_completed"]
            if "completion_pct" in body:
                b["completion_pct"] = float(body["completion_pct"])
            b["last_visited"] = datetime.now(timezone.utc).isoformat()

            # Auto-advance state: untouched → active when first visited
            if b["state"] == "untouched" and (b["sections_visited"] or b["steps_completed"]):
                b["state"] = "active"

        journey_progress = compute_journey_progress(buildings, fy_path)

        patch_data = {
            "buildings": buildings,
            "journey_progress": journey_progress,
            "last_accessed": datetime.now(timezone.utc).isoformat(),
        }
        if "name" in body and body["name"].strip():
            patch_data["name"] = body["name"].strip()

        sb_patch("fy_projects", {"id": f"eq.{project_id}"}, patch_data)
        return jsonify({
            "success": True,
            "journey_progress": journey_progress,
            "building_state": buildings.get(building_slug) if building_slug else None,
        }), 200

    except Exception as e:
        logger.error(f"[projects_update] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/archive", methods=["POST", "OPTIONS"])
@cross_origin()
def projects_archive():
    """
    Archive an active project. Enforces archive limit.
    Body: { project_id, email, tier }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    body = request.get_json(force=True) or {}
    project_id = (body.get("project_id") or "").strip()
    email = (body.get("email") or "").strip().lower()
    tier = (body.get("tier") or "operator").strip().lower()

    if not project_id or not email:
        return jsonify({"success": False, "error": "project_id and email required"}), 400

    limits = TIER_LIMITS.get(tier, TIER_LIMITS["operator"])
    archive_count = count_projects(email, "archived")

    if archive_count >= limits["archive"]:
        return jsonify({
            "success": False,
            "error": f"Archive limit reached ({limits['archive']} for {tier} tier). Permanently delete an archived project to make room.",
            "limit_hit": True,
        }), 400

    try:
        sb_patch("fy_projects", {"id": f"eq.{project_id}"}, {
            "status": "archived",
            "last_accessed": datetime.now(timezone.utc).isoformat(),
        })
        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"[projects_archive] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/delete", methods=["DELETE", "POST", "OPTIONS"])
@cross_origin()
def projects_delete():
    """
    Permanently delete a project. Irreversible.
    Body: { project_id, email }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    body = request.get_json(force=True) or {}
    project_id = (body.get("project_id") or "").strip()
    email = (body.get("email") or "").strip().lower()

    if not project_id or not email:
        return jsonify({"success": False, "error": "project_id and email required"}), 400

    try:
        logger.info(f"[projects_delete] attempting — project_id={project_id} email={email}")
        sb_delete("fy_projects", {
            "id": f"eq.{project_id}",
            "user_email": f"eq.{email}",
        })
        logger.info(f"[projects_delete] success — project_id={project_id}")
        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"[projects_delete] FAILED — {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects/set-active", methods=["POST", "OPTIONS"])
@cross_origin()
def projects_set_active():
    """
    Set a project as the active context (updates last_accessed).
    Body: { project_id, email }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    body = request.get_json(force=True) or {}
    project_id = (body.get("project_id") or "").strip()
    email = (body.get("email") or "").strip().lower()

    if not project_id or not email:
        return jsonify({"success": False, "error": "project_id and email required"}), 400

    try:
        sb_patch("fy_projects", {"id": f"eq.{project_id}"}, {
            "last_accessed": datetime.now(timezone.utc).isoformat(),
        })
        return jsonify({"success": True}), 200

    except Exception as e:
        logger.error(f"[projects_set_active] {e}")
        return jsonify({"success": False, "error": str(e)}), 500

