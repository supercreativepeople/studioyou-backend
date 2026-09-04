# Session Log — 2026-09-04
Session type: repo
Repo: studioyou-backend
Tokens at open: 14,982,269
Tasks in scope: TBD — awaiting Lee's direction after session open protocol

Notes: Previous session compacted at context limit (prior session end, not this session).
Skills loaded: session-length-guide, dev-session-protocol.
Desktop Commander confirmed: supercreativepeople@MacBookPro.lan

---

[OPEN] — Session protocol complete. Services verified:
- Git repos: studioyou-backend, studioyou-fy-agent, studioyou-app — all clean, in sync with origin/main
- Supabase: ACTIVE_HEALTHY (rubwhfjwqonqhfbkhren, us-east-2, Postgres 17.6.1)
- Supabase RLS: enabled on all 9 public tables (confirmed live)
- Cloud Run: last 3 deploys completed/success — latest 2026-08-27 (chore: CLAUDE.md + handoff)
- CLAUDE.md read: confirmed. Live state current to e8e3625.
- Handoff read: 2026-08-26-security-hardening-and-schema-fixes.md

Context reconciliation: Session summary (from prior compacted session) was stale vs. actual state.
Security fixes 1-6: ALL COMPLETE (summary said 4-6 not started — incorrect).
FY stuck-dots: FIXED (18s loadingSafetyRef watchdog).
S2 orchestrator frontend wiring: COMPLETE (step completion indicators in CanvasCol).
CI gap (SY_ADMIN_KEY): FIXED.
formations schema columns: FIXED.

Platform status per handoff: alpha-hardened, no open security items.

[CHECKPOINT] — tokens remaining: 14,970,181

---

---
[CHECKPOINT] 2026-09-04
- formation_briefing bug: confirmed already fixed in prior session — all 8 call sites use anthropic_client. Handoff was stale.
- Added LTX_API_KEY + DASHSCOPE_API_KEY + DASHSCOPE_BASE_URL env vars to main.py
- Added 7 new endpoints:
  - POST /api/tools/ltx/text-to-video (ltx-2-5-pro, 503 when key absent)
  - POST /api/tools/ltx/image-to-video (ltx-2-5-pro, 503 when key absent)
  - GET  /api/tools/ltx/job-status (poll by job_id)
  - POST /api/tools/qwen/chat (Qwen LLM via DashScope, 503 when key absent)
  - POST /api/tools/wan/text-to-video (WAN 3.0 async task, 503 when key absent)
  - GET  /api/tools/wan/task-status (poll by task_id)
- All endpoints session-token gated, return 503 (not 500) when key not yet present
- Syntax verified: SYNTAX OK
- Activation blocked on: Lee generating LTX key (console.ltx.io) + Alibaba enterprise identity verification


---
[CHECKPOINT] 2026-09-04 — post-compaction. Entries below reconstructed from git
history and live tool results at session close, not from context. Continuous
logging lapsed across the compaction boundary; this is the gap the protocol
exists to prevent and it is recorded here rather than silently backfilled.

## Runway credit-drain audit -> test_mode

[FOUND] — studioyou-fy-agent/agent.py: root cause of Runway credit drain is EAGER
  avatar start. `if RUNWAY_AVATAR_ID: await start_avatar()` runs on every job before
  any user interaction, so every test session, reload, and error-recovery burns
  credits immediately. Runway bills 2 credits up front + 2 per 6s of ACTIVE session.
[DECISION] — lazy start rejected as the fix: RoomOutputOptions(audio_enabled=False)
  must be set AT session.start() and cannot be flipped after init, so whether the
  avatar is used has to be known before the session starts.
[FIX] — agent.py: added test_mode gate before the eager-start block. test_mode=True
  skips start_avatar() entirely and falls through to Cartesia audio-only. Full
  conversation still works, zero Runway spend. Commit c998625, deployed 16:36 UTC.
[FIX] — studioyou-backend/main.py: TEST_EMAILS = {"nyclaabq@gmail.com"} auto-detect
  plus explicit {"test_mode": true} POST body support. Commits 70cb447, 566b422.
[FIX] — studioyou-app/studio.html: livekit-session call now sends
  test_mode: email === 'nyclaabq@gmail.com'. Commit 8e7b755.
[RESULT] — nyclaabq@gmail.com is the confirmed E2E test account. Dual-layer:
  backend auto-detects (no frontend change needed) AND frontend sends it explicitly.
  Manual avatar disabling during testing is no longer required.

## Cartesia voice code/comment drift

[FOUND] — agent.py Session AD docstring claimed "Switched model sonic-3 -> sonic-3.5
  and voice Parker -> Jameson (a5136bf9-...)". Deployed code is sonic-3 + Corey
  (630ed21c-4c5c...). The switch was documented but never made. CLAUDE.md Live State
  was CORRECT (Corey/sonic-3) — the docstring was the sole wrong artifact.
[DECISION] — Lee: keep Corey on sonic-3, revisit later if needed.
[FIX] — agent.py: removed the false sonic-3.5/Jameson claim from the docstring and
  recorded the active voice inline. Comment-only, no behavior change. Commit ee22229.

## Custom FutureYou avatar — architecture + groundwork

[FOUND] — Runway docs contradict themselves on programmatic avatar creation
  (create-your-own page is UI-only; concepts page claims avatars.create()).
  Resolved by probing the live dev API directly rather than trusting either.
[FOUND] — POST /v1/avatars is real. Required: name, referenceImage, personality,
  voice (object, discriminated on .type). NO TRAINING STEP — status returns READY
  immediately. This removes async training, status polling, and the "preparing your
  FutureYou" wait state from the plan entirely.
[FOUND] — referenceImage is fetched SERVER-SIDE from a URL, so a publicly readable
  Supabase Storage URL is sufficient. No multipart upload needed.
[FOUND] — Runway does native voice cloning: POST /v1/voices {name, from:{type:"audio"}}.
  "audio" confirmed as a valid discriminator.
[FOUND] — account has exactly one avatar: "The DUDE" d44bf1d0-c297-4e26-839a-93099a485ca5,
  matching RUNWAY_AVATAR_ID in agent .env. voice = {type:"runway-live-preset", presetId:"zach"}.
[FOUND] — BLOCKER on voice consolidation. LiveKit docs: "LiveKit TTS settings will
  supersede selected voices and personalities configured for the Runway character."
  Cartesia generates speech; Runway only renders lip-synced video. A Runway-cloned
  voice would be silently ignored on this path.
[FOUND] — consequence: The DUDE's `personality` and `startScript` configured in the
  Runway dashboard are INERT. Claude's system prompt is the actual brain and Runway
  never sees those fields. Dead config.
[DECISION] — voice cloning goes to Cartesia (POST /voices/clone), already in stack.
  Full Runway consolidation would mean dropping LiveKit for Runway's own live session
  API, i.e. giving up Claude as FutureYou. Off the table — that is the product thesis.
[DECISION] — portrait generation goes to Runway Gen-4 Image with References, chosen on
  technical merit: the binding constraint is identity preservation from a reference
  photo, which is a specific capability, not general image quality. Flux wins general
  aesthetics, which is not what this needs. Second argument: the portrait's output IS
  Runway's avatar input, so same-stack avoids framing/lighting/geometry mismatch.
[DECISION] — general rule adopted: bundle freely across independent tools, consolidate
  hard within a chain (wherever one feature's output is the next feature's input).
[DECISION] — standing rule: partnership value stays strictly downstream of the
  technical call. Tool selection is where the "no competing interests with the creator"
  principle gets tested; if deal flow ever drives it, that principle becomes marketing.
[MIGRATION] — Supabase: created public.creator_avatars (email-keyed, status lifecycle
  draft->brief_ready->portrait_ready->approved->provisioning->ready, history retained,
  partial unique index enforcing one active avatar per email, RLS enabled).
[FIX] — agent.py: per-creator avatar resolution. formation_context["runway_avatar_id"]
  or fallback to default. Module constant renamed RUNWAY_DEFAULT_AVATAR_ID. All
  downstream open/close/rotation uses the resolved avatar_id. Commit a0c9ccf.
[FIX] — main.py: looks up creator's active `ready` creator_avatars row, injects
  runway_avatar_id / runway_voice_id. Skipped under test_mode. Lookup failure falls
  back to default rather than breaking the session. Commit 97224bd.
[NEW] — main.py sidecar future_you_brief.py: brief generation. Static system prompt
  (prompt-cacheable) + creator data in user turn. Returns {brief, image_prompt}.
  Guardrails in the prompt, not in review: aspiration lives in context and evidence,
  never appearance; physical characteristics left entirely to the reference image;
  no predicted outcomes; no assumptions about personal life/finances; present never
  framed as broken; lighting described functionally not evaluatively; face kept
  optically sharp since it feeds a face renderer. Commit c96422f.
[TEST] — future_you_brief.py smoke-tested against a synthetic creator whose roadblock
  named financial pressure (chosen to stress the guardrails). Output held: named the
  specific obstacle, kept aspiration in the edit suite and finished work, promised no
  outcomes, invented no wealth. Two leaks caught on first pass ("flattering" lighting;
  shallow depth of field) and both closed by tightening the image_prompt spec. Re-tested
  clean.
[DEPLOY] — lk agent deploy completed 17:43:21Z. Agent CA_Mnhkjj3mUr7T, version Fqxg6JLvSBb8.

## Protocol-relevant correction

[FOUND] — CLAUDE.md section 3 states "Database: Supabase. RLS disabled." This
  CONTRADICTS section 7 Locked Decisions ("Security fix 6: RLS ENABLED + FORCED")
  and the live state confirmed at session open (RLS on all 9 tables). Section 3 is
  stale and wrong. Corrected in the CLAUDE.md rebuild this close.
[FOUND] — CLAUDE.md / Locked Decisions claim `lk agent update` does not rebuild and
  that only `delete && create` produces a fresh image + new agent ID. VERIFIED FALSE
  this session: `lk agent deploy` rebuilt and shipped twice (16:36Z and 17:43:21Z)
  while PRESERVING agent ID CA_Mnhkjj3mUr7T, with a new version string each time.
  The delete/create dance is no longer necessary. Locked Decision corrected this close.

[CHECKPOINT] — tokens remaining: ~14,980,000

[CRITICAL] — Runway creditBalance = 0, live-verified at session close via
  GET /v1/organization. SERVICES.md recorded 2,500 credits as of 2026-08-17. Balance
  consumed, almost certainly by the eager-avatar-start drain fixed this session.
  Blocks live avatar work; does NOT block E2E testing because test_mode skips the
  avatar. Autobilling still off, no card saved — second silent zero. Propagated to
  both CLAUDE.md files, agent SERVICES.md, and both handoffs.
[VERIFIED] — gen4_image_turbo present in account models, so the Gen-4 image path
  chosen for portrait generation is available on this account.
[VERIFIED] — Cloud Run latest ready revision studioyou-api-00449-7m9 (CLAUDE.md had
  00434-lpn; today's pushes deployed). Supabase ACTIVE_HEALTHY. Agent CA_Mnhkjj3mUr7T
  version Fqxg6JLvSBb8 confirmed live.
