"""
routes_avatars.py — FutureYou Custom Avatar Pipeline
Flask Blueprint registered in main.py via: app.register_blueprint(avatars_bp)

Status lifecycle: draft → brief_ready → portrait_ready → approved → provisioning → ready

Endpoints:
  POST /api/avatars/upload        — photo → Supabase AVATARS bucket
  POST /api/avatars/upload-voice  — voice sample → AVATARS bucket
  POST /api/avatars/brief         — generate brief + image_prompt
  POST /api/avatars/portrait      — Runway Gen-4 Image → portrait
  POST /api/avatars/approve       — creator approves/rejects portrait
  POST /api/avatars/provision     — Runway avatar + Cartesia voice clone → ready
  GET  /api/avatars/status        — pipeline state for frontend polling

Required new env var:
  RUNWAY_IMAGE_CONFIG_ID — slug from Model Router configs (check startup logs)

Already in Cloud Run:
  RUNWAYML_API_SECRET, CARTESIA_API_KEY, ANTHROPIC_API_KEY,
  SUPABASE_URL, SUPABASE_KEY
"""

import os
import uuid
import logging
import requests as req_lib
from datetime import datetime, timezone
from io import BytesIO

from flask import Blueprint, request, jsonify
from anthropic import Anthropic

from future_you_brief import generate_future_you_brief

logger = logging.getLogger(__name__)
avatars_bp = Blueprint("avatars", __name__)

RUNWAY_API_BASE = "https://api.dev.runwayml.com/v1"
CARTESIA_API_BASE = "https://api.cartesia.ai"
AVATARS_BUCKET = "AVATARS"
RUNWAY_DEFAULT_VOICE = {"type": "runway-live-preset", "presetId": "zach"}
RUNWAY_API_VERSION = "2024-11-06"


# ---------------------------------------------------------------------------
# Supabase helpers (self-contained — mirrors main.py pattern, no circular import)
# ---------------------------------------------------------------------------

def _sb_url():
    return os.environ.get("SUPABASE_URL", "").rstrip("/")

def _sb_headers():
    key = os.environ.get("SUPABASE_KEY", "")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def _sb_get(table, params=None):
    r = req_lib.get(f"{_sb_url()}/rest/v1/{table}", headers=_sb_headers(), params=params)
    r.raise_for_status()
    return r.json() if r.text else []

def _sb_post(table, data):
    r = req_lib.post(f"{_sb_url()}/rest/v1/{table}", headers=_sb_headers(), json=data)
    r.raise_for_status()
    return r.json() if r.text else {}

def _sb_patch(table, match, data):
    r = req_lib.patch(f"{_sb_url()}/rest/v1/{table}", headers=_sb_headers(), params=match, json=data)
    r.raise_for_status()
    return r.json() if r.text else {}

def _sb_storage_upload(bucket, path, file_bytes, content_type):
    key = os.environ.get("SUPABASE_KEY", "")
    url = f"{_sb_url()}/storage/v1/object/{bucket}/{path}"
    r = req_lib.post(url, headers={
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": content_type,
    }, data=file_bytes, timeout=60)
    r.raise_for_status()

def _storage_url(path):
    return f"{_sb_url()}/storage/v1/object/public/{AVATARS_BUCKET}/{path}"

def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Auth + row helpers
# ---------------------------------------------------------------------------

def _require_email():
    """Validate session, return email or abort 401."""
    token = (request.headers.get("X-Session-Token") or "").strip()
    if not token:
        body = request.get_json(force=True, silent=True) or {}
        token = (body.get("session_token") or "").strip()
    if not token:
        return None
    rows = _sb_get("formations", {"session_token": f"eq.{token}"})
    if not rows:
        return None
    row = rows[0]
    expires = row.get("session_expires_at")
    if expires:
        exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > exp_dt:
            return None
    return (row.get("email") or "").lower()

def _get_row(email, expected_status=None):
    """Return (row, error_msg). error_msg is None if OK."""
    rows = _sb_get("creator_avatars", {
        "email": f"eq.{email}",
        "order": "created_at.desc",
        "limit": "1",
    })
    if not rows:
        return None, "No avatar found. Start with /upload."
    row = rows[0]
    if expected_status and row["status"] != expected_status:
        return row, f"Expected status={expected_status!r}, got {row['status']!r}."
    return row, None

def _set_error(email, message):
    try:
        _sb_patch("creator_avatars", {"email": f"eq.{email}"}, {
            "error_message": message, "updated_at": _now()
        })
    except Exception:
        pass

def _runway_image_config():
    config_id = os.environ.get("RUNWAY_IMAGE_CONFIG_ID", "")
    if not config_id:
        return None, "Portrait generation not configured. Set RUNWAY_IMAGE_CONFIG_ID in Cloud Run — check startup logs for available slug values."
    return config_id, None

def startup_log_runway_configs():
    """Call once after app starts to log available Runway Model Router config slugs."""
    api_key = os.environ.get("RUNWAYML_API_SECRET", "")
    config_id = os.environ.get("RUNWAY_IMAGE_CONFIG_ID", "")
    if not api_key:
        logger.error("[avatar] RUNWAYML_API_SECRET not set — portrait generation disabled")
        return
    if config_id:
        logger.info(f"[avatar] RUNWAY_IMAGE_CONFIG_ID = {config_id!r} ✓")
        return
    logger.warning(
        "[avatar] RUNWAY_IMAGE_CONFIG_ID not set — portrait generation will fail. "
        "Create a config at app.dev.runwayml.com > Model Routers, then set "
        "RUNWAY_IMAGE_CONFIG_ID=<your-config-slug> in Cloud Run env vars."
    )


# ---------------------------------------------------------------------------
# POST /api/avatars/upload
# ---------------------------------------------------------------------------

@avatars_bp.route("/api/avatars/upload", methods=["POST"])
def upload_photo():
    email = _require_email()
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    photo = request.files.get("photo")
    if not photo:
        return jsonify({"error": "No photo file provided."}), 400

    ext = (photo.filename or "photo.jpg").rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp"):
        return jsonify({"error": "Unsupported format. Use JPG, PNG, or WEBP."}), 400

    photo_bytes = photo.read()
    if len(photo_bytes) > 20 * 1024 * 1024:
        return jsonify({"error": "Photo must be under 20MB."}), 400

    file_key = f"{email}/source/{uuid.uuid4()}.{ext}"
    try:
        _sb_storage_upload(AVATARS_BUCKET, file_key, photo_bytes,
                           photo.content_type or "image/jpeg")
    except Exception as e:
        logger.error(f"[avatar] Photo upload failed: {e}")
        return jsonify({"error": "Photo upload failed."}), 500

    photo_url = _storage_url(file_key)

    existing = _sb_get("creator_avatars", {"email": f"eq.{email}", "limit": "1"})
    row_data = {
        "email": email, "source_image_url": photo_url, "status": "draft",
        "is_active": False, "future_you_brief": None, "image_prompt": None,
        "generated_portrait_url": None, "runway_generation_id": None,
        "runway_avatar_id": None, "cartesia_voice_id": None,
        "error_message": None, "updated_at": _now(),
    }
    if existing:
        avatar_id = existing[0]["id"]
        _sb_patch("creator_avatars", {"id": f"eq.{avatar_id}"}, row_data)
    else:
        row_data["created_at"] = _now()
        result = _sb_post("creator_avatars", row_data)
        avatar_id = result[0]["id"] if isinstance(result, list) else result.get("id")

    logger.info(f"[avatar] Photo uploaded for {email}, avatar_id={avatar_id}")
    return jsonify({"avatar_id": str(avatar_id), "photo_url": photo_url, "status": "draft"})


# ---------------------------------------------------------------------------
# POST /api/avatars/upload-voice
# ---------------------------------------------------------------------------

@avatars_bp.route("/api/avatars/upload-voice", methods=["POST"])
def upload_voice():
    email = _require_email()
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    voice = request.files.get("voice")
    if not voice:
        return jsonify({"error": "No voice file provided."}), 400

    audio_bytes = voice.read()
    if len(audio_bytes) > 50 * 1024 * 1024:
        return jsonify({"error": "Voice sample must be under 50MB."}), 400

    ext = (voice.filename or "voice.wav").rsplit(".", 1)[-1].lower()
    voice_key = f"{email}/voice/{uuid.uuid4()}.{ext}"
    try:
        _sb_storage_upload(AVATARS_BUCKET, voice_key, audio_bytes,
                           voice.content_type or "audio/wav")
    except Exception as e:
        logger.error(f"[avatar] Voice upload failed: {e}")
        return jsonify({"error": "Voice upload failed."}), 500

    voice_url = _storage_url(voice_key)
    _sb_patch("creator_avatars", {"email": f"eq.{email}"},
              {"source_audio_url": voice_url, "updated_at": _now()})
    return jsonify({"voice_sample_url": voice_url})


# ---------------------------------------------------------------------------
# POST /api/avatars/brief
# ---------------------------------------------------------------------------

@avatars_bp.route("/api/avatars/brief", methods=["POST"])
def generate_avatar_brief():
    email = _require_email()
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    row, err = _get_row(email, expected_status="draft")
    if err:
        return jsonify({"error": err}), 404 if "No avatar" in err else 409

    formation_rows = _sb_get("formations", {"email": f"eq.{email}", "limit": "1"})
    formation_data = formation_rows[0] if formation_rows else {}

    try:
        anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        model = os.environ.get("FY_SURFACE_MODEL", "claude-sonnet-4-6")
        result = generate_future_you_brief(formation_data, anthropic_client, model)
    except Exception as e:
        logger.error(f"[avatar] Brief generation failed for {email}: {e}")
        _set_error(email, f"Brief generation failed: {e}")
        return jsonify({"error": "Brief generation failed."}), 500

    _sb_patch("creator_avatars", {"email": f"eq.{email}"}, {
        "future_you_brief": result["brief"],
        "image_prompt": result["image_prompt"],
        "status": "brief_ready",
        "error_message": None,
        "updated_at": _now(),
    })

    return jsonify({"brief": result["brief"], "image_prompt": result["image_prompt"],
                    "status": "brief_ready"})


# ---------------------------------------------------------------------------
# POST /api/avatars/portrait
# ---------------------------------------------------------------------------

@avatars_bp.route("/api/avatars/portrait", methods=["POST"])
def generate_portrait():
    email = _require_email()
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    config_id, config_err = _runway_image_config()
    if config_err:
        return jsonify({"error": config_err}), 503

    row, err = _get_row(email, expected_status="brief_ready")
    if err:
        return jsonify({"error": err}), 404 if "No avatar" in err else 409

    if not row.get("image_prompt"):
        return jsonify({"error": "image_prompt missing — re-run /brief."}), 409
    if not row.get("source_image_url"):
        return jsonify({"error": "source_image_url missing — re-run /upload."}), 409

    api_key = os.environ.get("RUNWAYML_API_SECRET", "")
    if not api_key:
        return jsonify({"error": "RUNWAYML_API_SECRET not configured."}), 503

    payload = {
        "configId": config_id,
        "input": {
            "promptText": row["image_prompt"],
            "aspectRatio": "3:4",
            "resolution": "1k",
            "outputCount": 1,
            "referenceImages": [{"uri": row["source_image_url"]}],
        },
    }

    logger.info(f"[avatar] Generating portrait for {email} via Runway Gen-4 Image")
    try:
        r = req_lib.post(
            f"{RUNWAY_API_BASE}/generate/image",
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json",
                     "X-Runway-Version": RUNWAY_API_VERSION},
            json=payload, timeout=120,
        )
        r.raise_for_status()
        runway_result = r.json()
    except req_lib.exceptions.HTTPError as e:
        body = e.response.text if e.response else ""
        logger.error(f"[avatar] Runway image error {e.response.status_code}: {body}")
        _set_error(email, f"Runway {e.response.status_code}: {body[:200]}")
        return jsonify({"error": f"Runway error: {e.response.status_code}"}), 502
    except Exception as e:
        logger.error(f"[avatar] Runway request failed: {e}")
        _set_error(email, str(e))
        return jsonify({"error": "Portrait generation failed."}), 502


    # Runway response: {"id": "...", "output": ["https://..."]} — adjust if shape differs
    output = runway_result.get("output") or runway_result.get("artifacts") or []
    if not output:
        logger.error(f"[avatar] Unexpected Runway response: {runway_result}")
        _set_error(email, f"No output in Runway response: {str(runway_result)[:300]}")
        return jsonify({"error": "No portrait returned from Runway."}), 502

    portrait_src = output[0] if isinstance(output[0], str) else output[0].get("url", "")

    # Re-upload to AVATARS bucket (Runway output URLs expire)
    portrait_key = f"{email}/portrait/{uuid.uuid4()}.jpg"
    try:
        img_r = req_lib.get(portrait_src, timeout=60)
        img_r.raise_for_status()
        _sb_storage_upload(AVATARS_BUCKET, portrait_key, img_r.content, "image/jpeg")
    except Exception as e:
        logger.error(f"[avatar] Portrait re-upload failed: {e}")
        _set_error(email, f"Portrait storage failed: {e}")
        return jsonify({"error": "Failed to store portrait."}), 500

    portrait_url = _storage_url(portrait_key)
    _sb_patch("creator_avatars", {"email": f"eq.{email}"}, {
        "generated_portrait_url": portrait_url,
        "runway_generation_id": runway_result.get("id"),
        "status": "portrait_ready",
        "error_message": None,
        "updated_at": _now(),
    })

    logger.info(f"[avatar] Portrait ready for {email}: {portrait_url}")
    return jsonify({"portrait_url": portrait_url, "status": "portrait_ready"})


# ---------------------------------------------------------------------------
# POST /api/avatars/approve
# ---------------------------------------------------------------------------

@avatars_bp.route("/api/avatars/approve", methods=["POST"])
def approve_portrait():
    email = _require_email()
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    row, err = _get_row(email, expected_status="portrait_ready")
    if err:
        return jsonify({"error": err}), 404 if "No avatar" in err else 409

    body = request.get_json(force=True, silent=True) or {}
    approved = body.get("approved", True)
    new_status = "approved" if approved else "brief_ready"

    _sb_patch("creator_avatars", {"email": f"eq.{email}"},
              {"status": new_status, "updated_at": _now()})

    return jsonify({"approved": approved, "status": new_status})



# ---------------------------------------------------------------------------
# POST /api/avatars/provision
# ---------------------------------------------------------------------------

@avatars_bp.route("/api/avatars/provision", methods=["POST"])
def provision_avatar():
    email = _require_email()
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    row, err = _get_row(email, expected_status="approved")
    if err:
        return jsonify({"error": err}), 404 if "No avatar" in err else 409

    runway_key = os.environ.get("RUNWAYML_API_SECRET", "")
    cartesia_key = os.environ.get("CARTESIA_API_KEY", "")

    if not runway_key:
        return jsonify({"error": "RUNWAYML_API_SECRET not configured"}), 503

    _sb_patch("creator_avatars", {"email": f"eq.{email}"},
              {"status": "provisioning", "updated_at": _now()})

    # --- 5a: Create Runway avatar ---
    runway_avatar_id = None
    try:
        runway_payload = {
            "name": f"FutureYou_{email.split('@')[0][:12]}",
            "referenceImage": row.get("portrait_url") or row.get("generated_portrait_url"),
            "personality": row.get("brief") or "",
            "voice": RUNWAY_DEFAULT_VOICE,
        }
        resp = req_lib.post(
            f"{RUNWAY_API_BASE}/avatars",
            headers={"Authorization": f"Bearer {runway_key}",
                     "Content-Type": "application/json",
                     "X-Runway-Version": RUNWAY_API_VERSION},
            json=runway_payload, timeout=60)
        resp.raise_for_status()
        runway_result = resp.json()
        runway_avatar_id = runway_result.get("id") or runway_result.get("avatarId")
        logger.info(f"[avatar] Runway avatar created: {runway_avatar_id}")
    except Exception as e:
        logger.error(f"[avatar] Runway avatar creation failed: {e}")
        _set_error(email, f"Runway avatar failed: {e}")
        _sb_patch("creator_avatars", {"email": f"eq.{email}"},
                  {"status": "approved", "updated_at": _now()})
        return jsonify({"error": "Runway avatar creation failed", "detail": str(e)}), 502

    # --- 5b: Cartesia voice clone (non-fatal) ---
    cartesia_voice_id = None
    voice_url = row.get("voice_sample_url")
    if voice_url and cartesia_key:
        try:
            audio_resp = req_lib.get(voice_url, timeout=30)
            audio_resp.raise_for_status()
            clone_resp = req_lib.post(
                f"{CARTESIA_API_BASE}/voices/clone",
                headers={"X-API-Key": cartesia_key, "Cartesia-Version": "2024-06-10"},
                files={"clip": ("voice.wav", BytesIO(audio_resp.content), "audio/wav")},
                data={"name": f"FutureYou_{email.split('@')[0][:12]}"},
                timeout=120)
            clone_resp.raise_for_status()
            cartesia_voice_id = clone_resp.json().get("id")
            logger.info(f"[avatar] Cartesia voice cloned: {cartesia_voice_id}")
        except Exception as e:
            logger.warning(f"[avatar] Cartesia clone failed (using default voice): {e}")
    else:
        logger.info(f"[avatar] No voice sample for {email} — skipping Cartesia clone")

    # --- 5c: Deactivate prior ready avatar ---
    try:
        _sb_patch("creator_avatars",
                  {"email": f"eq.{email}", "status": "eq.ready"},
                  {"is_active": False, "updated_at": _now()})
    except Exception:
        pass

    # --- 5d: Mark ready ---
    update = {"runway_avatar_id": runway_avatar_id, "status": "ready",
               "is_active": True, "error_message": None, "updated_at": _now()}
    if cartesia_voice_id:
        update["cartesia_voice_id"] = cartesia_voice_id
    _sb_patch("creator_avatars",
              {"email": f"eq.{email}", "status": "eq.provisioning"}, update)

    logger.info(f"[avatar] FutureYou ready for {email} — runway_avatar_id={runway_avatar_id}")
    return jsonify({"runway_avatar_id": runway_avatar_id,
                    "cartesia_voice_id": cartesia_voice_id,
                    "status": "ready", "is_active": True})


# ---------------------------------------------------------------------------
# GET /api/avatars/status
# ---------------------------------------------------------------------------

@avatars_bp.route("/api/avatars/status", methods=["GET"])
def get_avatar_status():
    email = _require_email()
    if not email:
        return jsonify({"error": "Unauthorized"}), 401

    rows = _sb_get("creator_avatars",
                   {"email": f"eq.{email}", "order": "created_at.desc", "limit": "1",
                    "select": "id,status,is_active,source_photo_url,portrait_url,"
                              "brief,image_prompt,runway_generation_id,runway_avatar_id,"
                              "cartesia_voice_id,error_message,created_at,updated_at"})

    if not rows:
        return jsonify({"has_avatar": False, "status": None, "row": None})

    row = rows[0]
    return jsonify({
        "has_avatar": row.get("status") == "ready" and row.get("is_active"),
        "status": row.get("status"),
        "row": row,
    })
