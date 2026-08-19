# StudioYou Handoff — 2026-08-19

## Session Summary
Security fixes 1-3 applied and deployed. Netlify deploy workflow corrected. Session protocol gaps identified and partially fixed.

---

## What Was Done

### Security Fixes (triggered by Khachatur seeing system prompt in Network tab)

**Fix 1 — Client-sent system prompt removed from all three `/api/chat` callsites in studio.html:**
- `sendViaRest` (fixed prior session): now sends `context: 'fy_chat', email, building_id, mode`
- `restInit` (line 2436): was `system: buildSystemPrompt()` → now `context: 'fy_chat', email, building_id, mode`
- `buildConversationPrompt` (line 2508): was `system: 'You convert creative conversations...'` → now `context: 'prompt_synth'`
- `buildSystemPrompt()` still exists in studio.html as dead code — not removed, just not called anywhere

**Fix 1 (server side) — `build_fy_system_prompt()` in main.py:**
- New function pulls creator data from Supabase (email → formations row → name, tagline, arsenal, creator_type, roadblock, building_id, mode)
- Falls back to minimal "You are FutureYou" prompt on error
- `PROMPT_SYNTH_SYSTEM` constant handles `context: 'prompt_synth'` requests
- `/api/chat` endpoint now routes by `context` field, builds prompt server-side

**Fix 2 — ADMIN_KEY moved to env var:**
- `ADMIN_KEY = os.environ.get("SY_ADMIN_KEY", "")` in main.py
- SY_ADMIN_KEY added to Cloud Run env vars (rotated value — old value "SY-ADMIN-2026" was compromised as Khachatur could see the repo)
- **DO NOT expose SY_ADMIN_KEY value in chat, docs, or handoffs — pointer only**

**Fix 3 — Debug endpoints gated:**
- `SY_DEBUG = os.environ.get("SY_DEBUG", "false").lower() == "true"`
- All 6 debug/admin endpoints return 404 when SY_DEBUG is false
- SY_DEBUG is not set in Cloud Run env vars → endpoints are currently disabled in prod

**Commits:**
- Backend: `954007a` — "Security fixes 1-3: server-side prompt, env var admin key, debug gate"
- Frontend: `2b8ad0b` — "Security fix: remove client-sent system prompt from all /api/chat calls"
- Frontend: `6ab3ac5` — "Add netlify.toml for auto-deploy config; gitignore .netlify/ folder"

### Netlify Deploy Workflow

**Current state:** studioyou-app deploys via `netlify-cli` from Desktop Commander.

```bash
cd /Users/supercreativepeople/Downloads/studioyou-app
netlify deploy --prod --dir=.
```

netlify-cli is installed globally on Mac (`npm install -g netlify-cli`, 2026-08-19).

**`netlify.toml` added to studioyou-app repo** (commit `6ab3ac5`):
```toml
[build]
  publish = "."
  command = ""
```

**GitHub auto-deploy is NOT yet connected.** One step remaining for Lee:
→ app.netlify.com → heroic-torrone-abeb92 site → Site configuration → Build & deploy → Continuous deployment → Link repository → GitHub → supercreativepeople/studioyou-app
After that: git push = deploy. No CLI needed.

**CLAUDE.md was wrong** (said "GitHub Actions auto-deploys from studioyou-app" — not true). Corrected this session.

---

## What's Still Pending

- **GitHub auto-deploy connection** — Lee needs to do one-time OAuth in Netlify UI (see above)
- **`/api/formation/briefing` bug** — `client.messages.create` should be `anthropic_client.messages.create` — noticed prior session, still not fixed
- **Security fixes 4-6** — session token auth, vault ownership, Supabase RLS — not started
- **`build_fy_system_prompt()` completeness** — currently pulls name, tagline from formations table but `arsenal`, `roadblock`, `creator_type` are not yet stored there; FY system prompt can't include them until those columns are added and populated
- **FY stuck-dots bug** — FY shows spinner and stops after user opens the tasks/steps sidebar panel during a chat session. Likely a collision between avatar-disabled state + sidebar state change + ongoing request. Not investigated this session.
- **Orchestrator (S2)** — FY step-state machine, top build priority, unbuilt

---

## Session Protocol Notes

The dev-session-protocol skill is correct and comprehensive. The failures this session were:
1. Previous sessions used `device_bash` for git (sandboxed, no network) instead of Desktop Commander (real Mac, real Keychain, real network). This caused push failures and manual-step handoffs to Lee.
2. CLAUDE.md had stale content (wrong Netlify deploy model).
3. Session open protocol (read CLAUDE.md + most recent handoff + check Supabase status) was not being run.

**The fix:** always use Desktop Commander for git and CLI. Always run session open at the start. CLAUDE.md is now updated with accurate deploy model.

---

## Next Session Priority Order

1. Have Lee complete the Netlify GitHub auto-deploy connection (5 min, Netlify UI)
2. Fix `/api/formation/briefing` — `client.messages.create` → `anthropic_client.messages.create`
3. Add `arsenal`, `roadblock`, `creator_type` columns to formations table so `build_fy_system_prompt()` can inject them
4. Investigate FY stuck-dots bug (sidebar collision)
5. Security fixes 4-6
6. Orchestrator (S2)
