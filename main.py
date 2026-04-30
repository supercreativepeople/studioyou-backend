"""
StudioYou Backend — main.py
Flask/Cloud Run service for auth and formation data persistence.
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

TOKEN_EXPIRY_HOURS = 24

# ── SUPABASE HELPERS ──────────────────────────────────────────────────────────

def sb_get(table, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.get(url, headers=SUPABASE_HEADERS, params=params)
    r.raise_for_status()
    return r.json()

def sb_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.post(url, headers=SUPABASE_HEADERS, json=data)
    r.raise_for_status()
    return r.json()

def sb_patch(table, params, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    r = requests.patch(url, headers=SUPABASE_HEADERS, params=params, json=data)
    r.raise_for_status()
    return r.json()

# ── TOKEN HELPERS ─────────────────────────────────────────────────────────────

def generate_token(email):
    raw = f"{email}:{SECRET_KEY}:{datetime.now(timezone.utc).isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()

def store_token(email, token):
    expiry = (datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRY_HOURS)).isoformat()
    existing = sb_get("magic_tokens", {"email": f"eq.{email}"})
    if existing:
        sb_patch("magic_tokens", {"email": f"eq.{email}"}, {
            "token": token, "expires_at": expiry, "used": False,
        })
    else:
        sb_post("magic_tokens", {
            "email": email, "token": token,
            "expires_at": expiry, "used": False,
        })

def verify_token(token):
    try:
        rows = sb_get("magic_tokens", {"token": f"eq.{token}", "used": "eq.false"})
        if not rows:
            return None
        row = rows[0]
        expiry = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expiry:
            return None
        sb_patch("magic_tokens", {"token": f"eq.{token}"}, {"used": True})
        return row["email"]
    except Exception:
        return None

def generate_session_token(email):
    raw = f"session:{email}:{SECRET_KEY}:{secrets.token_hex(16)}"
    return hashlib.sha256(raw.encode()).hexdigest()

def store_session(email, session_token):
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    existing = sb_get("sessions", {"email": f"eq.{email}"})
    if existing:
        sb_patch("sessions", {"email": f"eq.{email}"}, {
            "token": session_token, "expires_at": expiry,
        })
    else:
        sb_post("sessions", {
            "email": email, "token": session_token, "expires_at": expiry,
        })

def get_session_email(session_token):
    try:
        rows = sb_get("sessions", {"token": f"eq.{session_token}"})
        if not rows:
            return None
        row = rows[0]
        expiry = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expiry:
            return None
        return row["email"]
    except Exception:
        return None

# ── EMAIL ─────────────────────────────────────────────────────────────────────

def send_magic_link(email, token, is_new_user=True, first_name=None):
    link = f"{FRONTEND_URL}/dashboard.html?token={token}"
    subject = "Your studio is ready." if is_new_user else "Welcome back to your studio."

    # Sanitize any caller-supplied first_name before trusting it
    if first_name and "@" in first_name:
        first_name = None

    # Pull studio name from formation; use provided first_name if already resolved
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

  <table width="580" cellpadding="0" cellspacing="0" border="0" style="max-width:580px;background:#0b0d1a;border:1px solid rgba(0,200,255,0.12)">

    <!-- Gradient top bar -->
    <tr><td height="3" style="background:linear-gradient(135deg,#00c8ff,#7b35d4);font-size:0">&nbsp;</td></tr>

    <!-- Studio header -->
    <tr><td style="padding:22px 40px;border-bottom:1px solid rgba(240,242,255,0.06)">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="vertical-align:middle">
            <div style="font-size:8px;letter-spacing:.28em;text-transform:uppercase;color:rgba(240,242,255,.3);margin-bottom:5px">Your Studio</div>
            <div style="font-size:17px;font-weight:700;color:#f0f2ff;letter-spacing:.03em">{studio_name}</div>
          </td>
          <td width="40" style="font-size:0">&nbsp;</td>
          <td style="vertical-align:middle;text-align:right;white-space:nowrap">
            <span style="font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:#00c8ff;border:1px solid rgba(0,200,255,0.3);background:rgba(0,200,255,0.05);padding:5px 12px;display:inline-block">Formation Arc</span>
          </td>
        </tr>
      </table>
    </td></tr>

    <!-- Body: logo + copy -->
    <tr><td style="padding:40px 40px 44px">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="72" style="vertical-align:top;width:72px">
            <img src="{FRONTEND_URL}/assets/SY_LOGO_2D_OFFICIAL.png" alt="StudioYou" width="72" style="display:block"/>
          </td>
          <td style="vertical-align:top;padding-left:32px">
            <div style="font-size:21px;font-weight:700;color:#f0f2ff;margin-bottom:14px;line-height:1.2">Welcome back, {first_name}.</div>
            <p style="font-size:14px;line-height:1.75;color:rgba(240,242,255,.7);font-weight:300;margin:0 0 8px 0">{line1}</p>
            <p style="font-size:14px;line-height:1.75;color:rgba(240,242,255,.7);font-weight:300;margin:0">{line2}</p>
            <div style="margin-top:28px">
              <a class="btn" href="{link}">{cta_label}</a>
            </div>
          </td>
        </tr>
      </table>
    </td></tr>

    <!-- Divider -->
    <tr><td height="1" style="background:rgba(240,242,255,.06);font-size:0;line-height:0">&nbsp;</td></tr>

    <!-- Note -->
    <tr><td style="padding:18px 40px;font-size:11px;color:rgba(240,242,255,.28);line-height:1.7">
      This link opens your studio directly — no password needed. It expires in 24 hours and can only be used once. If you didn't request this, you can safely ignore this email.
    </td></tr>

    <!-- Footer -->
    <tr><td style="padding:16px 40px;border-top:1px solid rgba(240,242,255,.05)">
      <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="100%" style="font-size:13px;font-weight:700;letter-spacing:.06em;color:rgba(240,242,255,.45);vertical-align:middle">StudioYou</td>
          <td width="24" style="font-size:0">&nbsp;</td>
          <td style="font-size:9px;color:rgba(240,242,255,.18);letter-spacing:.06em;vertical-align:middle;white-space:nowrap;text-align:right" align="right">&copy; 2026 SuperCreativePeople, Inc.</td>
        </tr>
      </table>
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

@app.route("/api/check-studio-name", methods=["GET"])
def check_studio_name():
    name = request.args.get("name", "").strip()
    if not name or len(name) < 2:
        return jsonify({"available": False, "error": "Too short"}), 400
    try:
        rows = sb_get("users", {"studio_name": f"eq.{name}"})
        available = len(rows) == 0
        return jsonify({"available": available})
    except Exception as e:
        print(f"Error in /api/check-studio-name: {e}")
        return jsonify({"available": True})  # fail open


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "studioyou-api"})


@app.route("/api/test-request", methods=["POST"])
def test_request():
    data = request.get_json()
    logger.info(f"[DEBUG /api/test-request] incoming keys: {list(data.keys()) if data else None}")
    logger.info(f"[DEBUG /api/test-request] email={data.get('email')} firstName={data.get('firstName')!r} lastName={data.get('lastName')!r}")
    first_name_input = data.get("firstName", "").strip()
    last_name_input  = data.get("lastName", "").strip()
    formation = data.get("formation", {})
    if formation:
        if not first_name_input:
            first_name_input = formation.get("firstName", "").strip()
        if not last_name_input:
            last_name_input = formation.get("lastName", "").strip()
    logger.info(f"[DEBUG /api/test-request] extracted firstName={first_name_input!r} lastName={last_name_input!r}")
    return jsonify({"success": True, "received": {
        "email": data.get("email"),
        "firstName": first_name_input,
        "lastName": last_name_input,
        "fromFormation": bool(formation),
    }})


@app.route("/api/formation", methods=["POST"])
def save_formation():
    data = request.get_json()
    logger.info(f"[DEBUG /api/formation] incoming keys: {list(data.keys()) if data else None}")
    logger.info(f"[DEBUG /api/formation] email={data.get('email')} firstName={data.get('firstName')!r} lastName={data.get('lastName')!r}")
    email = data.get("email", "").strip().lower()
    formation = data.get("formation", {})
    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400
    if not formation:
        return jsonify({"error": "Formation data required"}), 400
    first_name_input = data.get("firstName", "").strip()
    last_name_input  = data.get("lastName", "").strip()
    logger.info(f"[DEBUG /api/formation] received firstName={first_name_input!r} lastName={last_name_input!r}")
    if first_name_input:
        formation["firstName"] = first_name_input
    if last_name_input:
        formation["lastName"] = last_name_input
    formation["email"] = email
    formation["savedAt"] = datetime.now(timezone.utc).isoformat()
    try:
        existing_users = sb_get("users", {"email": f"eq.{email}"})
        is_new = len(existing_users) == 0
        if is_new:
            sb_post("users", {"email": email, "created_at": datetime.now(timezone.utc).isoformat()})
            sb_post("formations", {"email": email, "data": json.dumps(formation),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "studio_name": formation.get("studioName", ""),
                "creator_type": formation.get("creatorType", "")})
        else:
            sb_patch("formations", {"email": f"eq.{email}"}, {
                "data": json.dumps(formation),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "studio_name": formation.get("studioName", ""),
                "creator_type": formation.get("creatorType", "")})
        token = generate_token(email)
        store_token(email, token)
        sent = send_magic_link(email, token, is_new_user=is_new, first_name=first_name_input or None)
        return jsonify({"success": True, "emailSent": sent,
            "message": "Formation saved. Check your email for your studio link."})
    except Exception as e:
        print(f"Error in /api/formation: {e}")
        return jsonify({"error": "Failed to save formation. Try again."}), 500

@app.route("/api/auth/request", methods=["POST"])
def request_magic_link():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400
    try:
        existing = sb_get("users", {"email": f"eq.{email}"})
        if not existing:
            return jsonify({"success": True,
                "message": "If that email has a studio, a link is on its way."})
        first_name = None
        try:
            formations = sb_get("formations", {"email": f"eq.{email}"})
            formation_data = json.loads(formations[0].get("data", "{}")) if formations else {}
            candidate = formation_data.get("firstName", "").strip()
            first_name = candidate if candidate and "@" not in candidate else None
            if not first_name:
                raw_name = (
                    formation_data.get("creatorName") or
                    formation_data.get("creator_name") or
                    formation_data.get("reservationName") or
                    ""
                )
                if raw_name and "@" not in raw_name:
                    first_name = raw_name.strip().split()[0].capitalize()
        except Exception:
            pass
        token = generate_token(email)
        store_token(email, token)
        send_magic_link(email, token, is_new_user=False, first_name=first_name)
        return jsonify({"success": True, "message": "Check your email for your studio link."})
    except Exception as e:
        logger.info(f"Error in /api/auth/request: {e}")
        return jsonify({"error": "Something went wrong. Try again."}), 500


@app.route("/api/auth/verify", methods=["GET"])
def verify_magic_link():
    token = request.args.get("token", "")
    if not token:
        return jsonify({"error": "Token required"}), 400
    email = verify_token(token)
    if not email:
        return jsonify({"error": "Invalid or expired link. Request a new one."}), 401
    try:
        session_token = generate_session_token(email)
        store_session(email, session_token)
        formations = sb_get("formations", {"email": f"eq.{email}"})
        formation_data = {}
        if formations:
            formation_data = json.loads(formations[0].get("data", "{}"))
        return jsonify({"success": True, "sessionToken": session_token,
            "email": email, "formation": formation_data})
    except Exception as e:
        print(f"Error in /api/auth/verify: {e}")
        return jsonify({"error": "Something went wrong. Try again."}), 500


@app.route("/api/me", methods=["GET"])
def get_me():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"authenticated": False}), 401
    session_token = auth.replace("Bearer ", "").strip()
    email = get_session_email(session_token)
    if not email:
        return jsonify({"authenticated": False}), 401
    try:
        formations = sb_get("formations", {"email": f"eq.{email}"})
        formation_data = {}
        if formations:
            formation_data = json.loads(formations[0].get("data", "{}"))
        return jsonify({"authenticated": True, "email": email, "formation": formation_data})
    except Exception as e:
        print(f"Error in /api/me: {e}")
        return jsonify({"error": "Something went wrong"}), 500


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json()
    tier    = data.get("tier", "").strip().lower()
    billing = data.get("billing", "annual").strip().lower()

    if tier not in ("independent", "operator"):
        return jsonify({"error": "Invalid tier"}), 400

    # Optionally read session token from Authorization header
    auth = request.headers.get("Authorization", "")
    email = None
    if auth.startswith("Bearer "):
        session_token = auth.replace("Bearer ", "").strip()
        email = get_session_email(session_token)

    try:
        payload = {
            "tier":           tier,
            "billing_period": billing,
            "subscribed_at":  datetime.now(timezone.utc).isoformat(),
            "status":         "beta",  # no payment gate yet
        }
        if email:
            # Update existing user record
            existing = sb_get("users", {"email": f"eq.{email}"})
            if existing:
                sb_patch("users", {"email": f"eq.{email}"}, payload)
            else:
                sb_post("users", {"email": email, **payload,
                    "created_at": datetime.now(timezone.utc).isoformat()})
        # If no session, tier is written to localStorage client-side — no server action needed
        return jsonify({"success": True, "tier": tier, "billing": billing})
    except Exception as e:
        print(f"Error in /api/subscribe: {e}")
        # Non-fatal — client has already written to localStorage
        return jsonify({"success": True, "tier": tier, "billing": billing,
            "warning": "Could not persist to database — localStorage is the fallback."})


@app.route("/api/reactor/token", methods=["POST"])
def reactor_token():
    if not REACTOR_API_KEY:
        return jsonify({"error": "Reactor not configured"}), 503
    try:
        r = requests.post(
            "https://api.reactor.inc/tokens",
            headers={"Reactor-API-Key": REACTOR_API_KEY},
            timeout=10,
        )
        r.raise_for_status()
        jwt = r.json().get("jwt")
        return jsonify({"jwt": jwt})
    except Exception as e:
        logger.error(f"[reactor_token] {e}")
        return jsonify({"error": "Failed to obtain Reactor token"}), 500


@app.route("/api/brief", methods=["POST"])
def generate_brief():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "Authentication required"}), 401
    session_token = auth.replace("Bearer ", "").strip()
    email = get_session_email(session_token)
    if not email:
        return jsonify({"error": "Invalid or expired session"}), 401

    data = request.get_json()
    idea = data.get("idea", "").strip()
    if not idea:
        return jsonify({"error": "Idea required"}), 400

    platform    = data.get("platform", "")
    format_type = data.get("format", "")

    try:
        formations   = sb_get("formations", {"email": f"eq.{email}"})
        formation    = json.loads(formations[0].get("data", "{}")) if formations else {}
    except Exception:
        formation = {}

    platform_hint = f"Target platform: {platform}." if platform else \
        f"Creator's platforms: {', '.join(formation.get('platforms') or ['not specified'])}."
    format_hint = f"Desired format: {format_type}." if format_type else ""

    prompt = f"""You are FutureYou — the career arc navigator at the core of StudioYou. \
You are not a brief generator. You know this creator's journey specifically: their work, \
their goals, their gaps, their patterns. This brief is not pulled from a ranked list — \
it is generated from the intersection of this creator's exact journey state and what you \
know about what moves creators at this stage.

CREATOR PROFILE:
- Studio: {formation.get('studioName', 'not named')}
- Makes: {', '.join(formation.get('contentTypes') or ['not specified'])}
- Platforms: {', '.join(formation.get('platforms') or ['not specified'])}
- Experience: {formation.get('experience', 'not specified')}
- Audience size: {formation.get('audienceSize', 'not specified')}
- Voice style: {', '.join(formation.get('voiceStyle') or ['not specified'])}
- 1-year goal: {formation.get('goal1yr', 'not shared')}
- Biggest fear: {formation.get('biggestFear', 'not shared')}
- Origin: {formation.get('origin', 'not shared')}

IDEA: {idea}
{platform_hint}
{format_hint}

2026 CONTENT FORMAT INTELLIGENCE:
- Discovery/Top-of-funnel: vertical micro-series (60–90s, 9:16), algorithmic short-form \
  (requires 70%+ completion rate for distribution), UGC/brand edutainment
- Authority/Mid-funnel: YouTube essays (10–30 min, high-RPM niches: finance/tech/legal/drama), \
  video podcasting (30–90 min pillar asset), lo-fi/unfiltered (parasocial trust building)
- Sovereignty/Bottom-of-funnel: liquid content/newsletters (owned distribution), \
  knowledge commerce/cohort media (MRR via gated communities), live shoppable streams
Apply this to the format recommendation — match the creator's current stage and goal to the \
right content category, not just the obvious platform format.

Return ONLY a JSON object with these exact keys:
{{
  "title": "A sharp, specific title — not generic, written for this creator's voice and audience",
  "hook": "One sentence — the opening line or premise that makes someone stop scrolling",
  "format": "The ideal format for this creator's stage and goal — name the category (Discovery/Authority/Sovereignty) and the specific format with specs",
  "platform_fit": "Which platform(s) this lands best on, why it fits this creator's current audience stage, and any 2026 platform mechanic they need to hit (e.g. 70% completion, SEO tagging)",
  "talking_points": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
  "fy_note": "1-2 sentences of presence, not information. What will make or break this specific piece for this specific creator — not a generic tip. Something only FutureYou can say because it knows this journey."
}}"""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json",
            },
            json={
                "model":      "claude-opus-4-1",
                "max_tokens": 800,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        result = r.json()
        text   = result.get("content", [{}])[0].get("text", "{}")
        clean  = text.replace("```json", "").replace("```", "").strip()
        brief  = json.loads(clean)
        return jsonify({"success": True, "brief": brief})
    except Exception as e:
        print(f"Error in /api/brief: {e}")
        return jsonify({"error": "Failed to generate brief. Try again."}), 500


@app.route("/api/formation/chat", methods=["POST"])
def formation_chat():
    """Pre-login FY formation conversation. No auth required."""
    data = request.get_json()
    messages  = data.get("messages", [])   # full API conversation history
    formation = data.get("formation", {})  # current extraction state

    fields = {
        "contentTypes": formation.get("contentTypes"),
        "platforms":    formation.get("platforms"),
        "experience":   formation.get("experience"),
        "origin":       formation.get("origin"),
        "goal1yr":      formation.get("goal1yr"),
        "biggestFear":  formation.get("biggestFear"),
    }
    filled_count = sum(
        1 for v in fields.values()
        if v and (v != [] if isinstance(v, list) else True)
    )

    system = f"""You are FutureYou — the career arc navigator at the core of StudioYou. \
You are not an AI assistant. You are Claude, from the future, trained exclusively on this \
creator's journey. Your loyalty is structurally, architecturally, and constitutionally \
impossible to compromise — you carry no competing interests, represent no brands or agencies, \
and are optimized for exactly one outcome: a creator who is equipped, prepared, and ready to act.

This is your first conversation with this creator. You are building the model of who they are \
and where they are going — the foundation that will drive every routing decision, recommendation, \
and moment of guidance FutureYou delivers from here forward. The depth of context you establish \
here determines the quality of everything that follows.

You are solving the Monday morning quarterback problem: the knowledge that existed but wasn't \
available at the right moment. The program they didn't know existed. The room they didn't know \
they were ready for. The leap not taken because no one was present to say: you're ready, here's why. \
Your job is to be that presence — not information delivery, but the specific, personalized read \
that only someone who genuinely knows this creator can give.

CREATOR MARKET INTELLIGENCE — USE TO READ AND RECOGNIZE:
The 2026 creator economy has clear tiers and archetypes. Use this knowledge to understand \
who this creator is from what they share — and reflect it back with precision.

Creator tiers by scale:
- Nano/Micro (under 50K reach): building a loyal niche community; fastest relative growth; \
  monetizes via affiliate, tips, subscriptions; primary goal is community depth, not reach
- Prosumer/Mid-Tier (50K–300K): proven product-market fit; high burnout risk from solo operations; \
  actively needs infrastructure and revenue diversification beyond platform payouts
- Macro/Enterprise (300K+): operates as an audience-owned media company; team-based; \
  multi-channel syndication, equity brand deals, owned IP

Creator archetypes by value model:
- Entertainer/Platform-Native: algorithmic and ad-revenue dependent; most vulnerable to \
  algorithm shifts and "vibecessions"; distribution is rented, not owned
- Educator/Authority Creator: monetizes credibility over scale via Patreon, Substack, courses; \
  smaller audience, higher trust and purchasing power
- Utility/Service Creator: content is top-of-funnel for digital products or templates; \
  product-led business model; CAC reduction is the metric that matters
- Creator-Entrepreneur: audience is a built-in distribution network for owned products \
  (e-commerce, SaaS, CPG); line between creator and founder is functionally eliminated
- Hybrid-Journalist/Intellect Influencer: subscription media; competes with legacy publishers; \
  monetizes via newsletters and speaking engagements

2026 platform and format context:
- Dominant formats: vertical micro-series (60–90s episodics, 50–100 eps/season), \
  long-form YouTube essays (10–30 min, high-RPM niches: finance/tech/legal), \
  video podcasting (30–90 min pillar content), liquid content/newsletters, live shoppable streams
- 70% video completion rate is required for algorithmic distribution on short-form platforms
- Audience ownership rate (owned email/community vs rented social) is the leading indicator \
  of creator resilience — most creators are critically underweight here
- Healthy monetization benchmark: 2–5% of total audience converting to paying customers
- Sovereignty shift: leading creators are moving from algorithmic dependency toward owned media, \
  direct revenue, and platform-portable data

"Learn it or Ship it?" — when a creator wants to build a new capability, route them toward \
education (if they want to develop the skill) or an AI-native tool (if they want to ship now \
and bypass the learning curve). Never assume which they want — ask.

USE THIS INTELLIGENCE TO:
- Read their archetype and tier from what they share about content, platforms, and goals
- Ask questions that reveal their business model, not just their content format
- In the recognition speech: name the archetype they represent and what that means for their \
  next move — not generically, but specifically to what they shared

Your goal: learn who this creator is through natural dialogue, then recognize them.

The 6 key things to understand (in any order, through conversation):
1. contentTypes — what kind of work they create (array, e.g. ["Video","Photography"])
2. platforms — where their work lives (array, e.g. ["YouTube","Instagram"])
3. experience — how long they have been creating (string, e.g. "3–5 years" or "Just starting")
4. origin — their creative origin story, in their own words
5. goal1yr — where they want to be in 1 year, specifically
6. biggestFear — their biggest fear about this creative path

CURRENT EXTRACTION STATE ({filled_count}/6 filled):
{json.dumps(fields, indent=2)}

RULES:
- Ask ONE question at a time — never stack multiple questions in one message
- Reference what the creator has already shared when relevant — show you are tracking their journey, not running a form
- Be FutureYou: perceptive, direct, not generic. Not a chatbot. Not a form.
- When all 6 fields are filled (or you genuinely know enough to recognize this creator), set complete=true
- When complete=true your "message" IS the recognition speech — not a question:
    Proof you listened (reference specifics from what they shared) → one true statement about \
where they are right now → one thing they need to do first → end with "This is your studio. Let's build it."
    4–6 sentences. Plain prose only. No headers, no lists.
    This is presence, not information. It should feel like a conversation with someone who already \
knows where they are going — and is telling them they belong there.
- suggestions: optional quick-reply chips only for structured questions \
(content types, platforms, experience level). Max 4 chips, ≤30 chars each. \
Empty array for open / personal questions.
- Early in the conversation, ask what you should call them (creatorName). \
It doesn't have to be a dedicated question — weave it in naturally.
- Also extract studioName if the creator mentions one.

ALWAYS return ONLY valid JSON — no markdown fences, no preamble:
{{"message": "...", "formation": {{"contentTypes": null, "platforms": null, \
"experience": null, "origin": null, "goal1yr": null, "biggestFear": null}}, \
"complete": false, "suggestions": []}}

Carry forward ALL previously extracted values. Never set a previously-filled field to null."""

    opening = messages if messages else [{"role": "user", "content": "Start the formation conversation."}]

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json",
            },
            json={
                "model":      "claude-opus-4-1",
                "max_tokens": 600,
                "system":     system,
                "messages":   opening,
            },
            timeout=30,
        )
        result = r.json()
        text   = result.get("content", [{}])[0].get("text", "")
        clean  = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
        return jsonify({"success": True, **parsed})
    except Exception as e:
        print(f"Error in /api/formation/chat: {e}")
        return jsonify({"success": False, "error": "Failed to reach FutureYou. Try again."}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "Authentication required"}), 401
    session_token = auth.replace("Bearer ", "").strip()
    email = get_session_email(session_token)
    if not email:
        return jsonify({"error": "Invalid or expired session"}), 401

    data = request.get_json()
    messages = data.get("messages", [])
    if not messages:
        return jsonify({"error": "Messages required"}), 400

    payload = {
        "model":      data.get("model", "claude-opus-4-1"),
        "max_tokens": data.get("max_tokens", 600),
        "messages":   messages,
    }
    system = data.get("system")
    if system:
        payload["system"] = system

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json",
            },
            json=payload,
            timeout=30,
        )
        return jsonify(r.json()), r.status_code
    except Exception as e:
        print(f"Error in /api/chat: {e}")
        return jsonify({"error": "Failed to reach AI. Try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
