# StudioYou — Claude Session Reference

## Session Start Protocol (non-negotiable)
Every session begins by reading both uploaded files in full before any strategy or code:
1. The handoff doc (HANDOFF_SESSION_[X]_[DATE].md)
2. claude.md — ALWAYS read the uploaded claude.md from Lee. Never read the project copy at /mnt/project/claude.md — it is stale.

No exceptions. Do not strategize, do not touch code until both are read.

## Session End Protocol (non-negotiable — codified Session Q)
At the close of every session (or whenever Lee asks for a handoff), Claude produces all three of the following without being asked individually:
1. **Handoff doc** — `HANDOFF_SESSION_[X]_[DATE].md`, covering what happened, files changed, bugs found/fixed, open items, and a Session [X+1] agenda. Presented via `present_files`.
2. **Notion log** — the handoff doc content created as a new page under the Handoff Docs folder (`366b963047e5801795d0ec513406ac55`), titled "Session [X] Handoff."
3. **Updated claude.md** — header (Last Updated / Next Session), Current Build State entries for any files touched, any new locked decisions or corrections, consolidated open-items list for the next session, and a new Notion Reference row for this session's handoff. Presented via `present_files`.

---
**Last Updated:** July 3, 2026 — Session AC
**Next Session:** Session AD — Avatar session rotation (Runway hard-caps every Characters session at 5 minutes; nothing renews it, so any conversation running past ~5 min drops the avatar with no recovery — root cause of the "random" drops, confirmed via Runway docs). Voice/pronunciation work alongside it (Cartesia pronunciation dictionary + speed tuning — already on sonic-3, `pronunciation_dict_id` just unused). Then Vault/metadata-capture spec — new, scoped as its own spec like PLAN (see Session AC Open Items). Then PLAN sub-agent spec. Then Tier 2 orchestrator spec. Then wire IDEATE into live agent. Then Super Somebody benchmark.

---

## Current Build State

**index.html — Session L, R**
Session R: Babel pinned to `@babel/standalone@7.23.10`.

**dashboard.html — Session N, Q, R, S, U, V, W, X, AA, AB, AC, AD**
Session AD (presented, needs Netlify redeploy):
- Archetype stills filename fix: `FY_AVATAR_STILLS` array pointed at `_youtube_creator.jpg`/`_short_form_creator.jpg`/`_live_action_filmmaker.jpg`/`_content_creator.jpg`/`_multi_format.jpg` — LittleBird delivered them as `_youtube2.jpeg`/`_shortform2.jpeg`/`_filmmaker2.jpeg`/`_content2.jpeg`/`_multiform2.jpeg` (different naming convention AND extension, `.jpeg` not `.jpg`). Not missing assets, a stale array. Fixed.
- Triage pill timing + architecture: pills were rendering the instant `triageStage` flipped to `q1`, same tick as the message and `speakLine()` call — appeared alongside FY's question, not after. New `pillsVisible` state gates render behind an estimated post-speech delay (4000ms avatar-live, 1600ms text-only), same pattern as the existing pre-nav delay. Also pulled hardcoded global `TRIAGE_PILLS` into `ARCHETYPE_TRIAGE_PILLS`, keyed by archetype via `getTriagePills()` — all six current archetypes still share identical placeholder content (idea/treatment/script), real per-archetype differentiation needs Lee's methodology transfer, same pattern as PLAN/Vault.
- "Arriving"/"Reconnecting" copy: `FYLiveKitRoom`'s post-connection spawning cover (separate from the Session AC archetype-cycling redesign, which only covers the PRE-connection wait) had a generic "FutureYou is spawning" cover regardless of context. Added `hasBeenLiveRef` tracking — shows "arriving" on first landing, "reconnecting" if video drops mid-conversation (rotation swap or a real blip).
- Video element leak fix (real bug, confirmed via live-test agent logs): `TrackSubscribed` appended a new `<video>` element every time without removing prior ones; `TrackUnsubscribed` only called `track.detach()`, which detaches the stream but never removes the DOM element. Every avatar rotation (Session AD's 270s swap) stacked another stale `<video>` in the container — DOM-order-dependent which one rendered, could show a frozen frame from the old element. This is the actual cause of "second reset never completed" reported after a live test with two rotations. Fixed: clear all `<video>` children before attaching the new one; `TrackUnsubscribed` now explicitly removes attached elements from the DOM and resets `spawned` to `false` (this was also required for the Arriving/Reconnecting fix above to ever show on a rotation — `spawned` never went false on unsubscribe before this).
- `speakLine` scope bug (confirmed root cause of BOTH "FY didn't speak the handoff line" and "FY didn't route to studio" in the same live test, via browser console — `Uncaught ReferenceError: speakLine is not defined`): the function was defined inside `FYPanel`'s local scope, but called from `handlePlanReady` in the outer `App` component. The ReferenceError threw before entering the function body — no try/catch inside `speakLine` could protect against it — which aborted the rest of that `setTimeout` callback, including the `handleOpenBuilding(b)` call right after it. One bug, two symptoms. Fixed: `speakLine` moved to top-level module scope (its only dependency is the global `window._fyRoom`), callable from any component.
- Browser autoplay-block recovery: dashboard.html had no handling for browsers silently blocking audio playback pre-user-gesture, unlike studio.html which got this fix in Session AB. Ported the same `AudioPlaybackStatusChanged` / `room.startAudio()` retry-on-click pattern. Turned out NOT to be the cause of a later "FY still not speaking" report that session (that was Cartesia account credits exhausted, a billing issue, not code — see agent.py), but this is still correct defensive code and stays in.
- `localFallbackRoute()` redundancy fix — see main.py Session AD entry for the full context (Fable 5 routing was landing creators on a step that re-asks the same one-sentence logline triage just captured). idea branch: Raw Idea/"One Sentence" → Gut Check/"Does This Have Legs?". treatment branch: Story & Structure/"What's the Premise?" → Story & Structure/"Who's It For?". script branch unchanged.
Session AC (deployed by Lee, confirmed working via live test):
- `sy_avatar_start` event added — the "Want to see who's talking to you?" chat nudge previously only fired `sy_avatar_reset` (cleared localStorage, dropped mode to idle) with no visible effect when already idle. Dead click. Now dispatches `sy_avatar_start`, which `FYAvatarSlot` listens for and calls `startStock()` directly — actually launches the avatar.
- Spawning state redesigned: archetype-cycling background (`av-cycle-wrap`) now runs continuously through both `idle` and `uploading` modes instead of cutting to a separate blank screen with a gif. Click only swaps the overlay content — CTA text becomes a flashing "Spawning FutureYou…" (`av-spawning-flash` / `avFlash` keyframe). No gif needed for this state anymore.
- `speakLine()` now publishes `fy_say_verbatim` instead of the old `[SPOKEN LINE]` `fy_chat` wrapper hack (see agent.py Session AC entry for the corresponding fix — this is the half that lives in dashboard.html).
- Added a second closing line, "See you there.", spoken via `speakLine()` right before the disconnect+navigate to studio.html — only when the avatar is actually live and speaking. Covers the unavoidable respawn gap (studio spins up a fresh Runway worker on load) narratively instead of going silent mid-cut.
- **Found, not fixed:** 5 of 11 `FY_AVATAR_STILLS` archetype images 404 (`youtube_creator`, `short_form_creator`, `live_action_filmmaker`, `content_creator`, `multi_format`) — checked alternate extensions, files genuinely don't exist at those paths. Lee is locating/providing replacements.
- **Left alone per Lee's call:** the dead avatar-setup link in the FY chat box region is getting rewritten wholesale later — flagged, not touched further this session.

Session AB (final version presented at close — MUST be redeployed to Netlify):
- All 17 `[TRIAGE]` debug statements stripped (one converted to a legitimate `[FY] session close failed` warn)
- Spoken handoff: when routing succeeds and avatar room is live, the exact handoff line is published to the agent as a say-verbatim instruction over `fy_chat` — spoken via normal TTS path, no agent.py change. Text still renders instantly. Pre-nav delay: 5000ms when avatar live, 2200ms otherwise.
- Routing retry re-arm: `closerOffered` resets on any close failure (`!d.success` or fetch throw). Previously one failed close permanently disabled routing for the session — this is what made FY question indefinitely in Lee's second AB test, compounding the backend Fable crash (see main.py).


Session AA (not git-tracked — Lee provides/downloads via chat, deploys via Netlify):
- Fixed avatar video-track bug: removed hardcoded `participant.identity === 'tavus-avatar-agent'` gate on video attach — Runway's worker publishes under a different identity, track was subscribing but never rendering
- Triage routing fix: removed `fy_route` self-signal entirely (sysPrompt + regex detector both stripped — architecturally unreliable, confirmed in production). Replaced 5-exchange soft closer (`__CLOSER__` card, manual click) with hard 2-exchange automatic `closeSession()` call, no opt-out
- Removed avatar-live navigation suppression from `handlePlanReady` — FY at triage stage is a router, not a conversation, per Lee's explicit call. Confirmed via grep this guard had exactly one call path before removing.
- Added explicit `window._fyRoom.disconnect()` before `handleOpenBuilding`'s hard navigation — don't rely on browser unload behavior alone for Runway session cleanup (no `max_duration` set as backstop)
- Added verbal handoff line ("Let's move into [BUILDING] and work this through") injected into chat when routing succeeds, before navigation. Pre-nav delay extended 600ms → 2200ms so it's readable.
- `[TRIAGE]` console logging added mid-session for debugging, **still present at session close** — strip once Session AA's last two fixes are confirmed stable, don't ship debug logs indefinitely.

**studio.html — Session P, R, V, X, AA, AB, AD**
Session AD (presented, needs Netlify redeploy):
- "Arriving"/"Reconnecting" copy: same fix as dashboard.html, `FYAvatarSlot`'s placeholder said generic "Spawning — one moment" regardless of context (deliberately left plain last session, only a sizing pass per Session AC). Added `hasBeenLiveRef` — "Arriving" first landing, "Reconnecting" if video drops. Unlike dashboard.html, studio.html attaches to one persistent React-ref'd `<video>` element rather than creating new ones, so it didn't have the element-stacking leak dashboard.html had.
- Scripted building-arrival line: existing `initFY()`/`openingPrompt` mechanism is LLM-generated and text-display-only via `fy_directive` — not guaranteed to actually be spoken, same class of unreliability as the old pre-Session-AC `[SPOKEN LINE]` handoff hack. Added `ARRIVAL_LINES` (one hand-written line per building, "Welcome to X. This is where Y. Let's Z.") and a `speakLine()` helper (new to studio.html, mirrors dashboard.html's, publishes `fy_say_verbatim`) — fires on first landing and on building switch, guaranteed spoken + displayed, runs before the LLM opening prompt rather than replacing it (LLM prompt still handles the smarter section-specific routing nudge). Gated by `hasVisitedBuilding()`/`markBuildingVisited()` — Lee wants this a true first-time-only occurrence per building, not every visit. No backend persistence exists yet (Vault gap), so this is localStorage (`sy_visited_buildings`) — move to Vault once built.
Session AB (deployed mid-session by Lee; avatar-on retest pending):
- Audio track attach: `TrackSubscribed` + late-join catch-up loop now attach audio (mirrors dashboard — this was the entire studio-silence bug). `AudioPlaybackStatusChanged` handler added: studio loads via navigation with no user gesture, so `room.startAudio()` fires on first click if the browser blocks autoplay.
- Hidden-reply guard: confirm/BUILD IT card only fires on agent replies to VISIBLE creator messages (`lastSendHiddenRef`) — previously fired on the reply to the hidden task-activation prompt, before the creator answered anything. LiveKit path now matches the REST path's `!hidden` guard.
- Conversation-derived generation prompts: `buildConversationPrompt()` distills last 12 messages into a real prompt via `/api/chat` on BUILD IT; fallback chain: creator's verbatim recent answers → static step template (last resort). `buildModelParams(toolTask, task, visualDesc)` gained the override param. Fixes fal generating from `task.level1` (the static step description) — the random-street-scene bug.


Session AA (not git-tracked — same workflow as dashboard.html):
- Same avatar video-track identity-gate fix as dashboard.html (two call sites: `TrackSubscribed` handler + late-join catch-up loop)
- Hardened section/step flash-matching (`recommendedSection`/`recommendedStep`) against exact-string mismatch between backend-returned `section_name`/`step_title` and hardcoded `BUILDING_TASKS` titles — now case/punctuation-insensitive with substring fallback, defaults to first section rather than silently matching nothing. Note: the pulse animation itself (`sectionPulse` keyframe) was already fully built and correctly wired on both section and step level — this was a matching-reliability fix, not a missing feature.
- **Not yet confirmed working** — deployed at session close, not re-tested by Lee.

**subscribe.html — Session L, R**
Session R: Babel pinned. No changes since.

**knowledge/ — Session Y (commit 8490490) + Session Z (commit ad9ca3b) + Session AA (commits 7cbb241, 0d9544b, 4a287a7, 61d8e1e)**
Layer 2 knowledge base. Files in studioyou-backend/knowledge/:
- `knowledge/FY_LAYER2_SCHEMA.md` — governing template for all 12 building sub-agents. **Session AA addition: Section 6.1, "Success State as Dispatch Trigger"** (commit `7cbb241`) — SUCCESS STATE is a literal, checkable condition Tier 2 evaluates to decide dispatch timing, not narrative tone guidance. Includes the creator-facing litmus test (commit `4a287a7`, added second, weighted higher than the Tier 2 checkability test): does the creator understand exactly what they're being asked, clearly enough that they never guess the "right" answer? No right or wrong answer at any step — the creator is building a structure, and structural presence is checked, never performance. Also adds `active_step_progress`/`satisfied` field to the `orchestrator_context` object.
- `knowledge/buildings/FY_IDEATE_SUBAGENT_SPEC.md` — COMPLETE. **Session AA: audited against Section 6.1 (commit `61d8e1e`)** — 6 of 8 steps required fixes (1 missing SUCCESS STATE filled in, 6 rewritten to remove "true"/"honest" as the literal standard — the exact right-answer-guessing trap the litmus test targets). Also fixed the same pattern in the Ignition Sequence's Result line.
- `knowledge/buildings/FY_DEVELOP_SUBAGENT_SPEC.md` — COMPLETE v1.2 (commit ad9ca3b). **Session AA: audited against Section 6.1 (commit `0d9544b`)** — 13 of 31 SUCCESS STATE entries required fixes (2 missing fields filled — P-5, B-5 — 11 rewritten to remove subjective/psychological standards). Handoff-continuity verified field-clean into and out of this spec (IDEATE→DEVELOP: `seed.idea_type`, `concept_line`, `anchors` all match exactly; DEVELOP→PLAN: outbound handoff package confirmed complete and ready).

**Knowledge base read protocol:**
At session open, Claude reads the relevant building spec(s) via raw GitHub URL:
`curl -s "https://raw.githubusercontent.com/supercreativepeople/studioyou-backend/main/knowledge/buildings/[FILENAME].md"`
These are the source of truth. Desktop Commander is NOT required to read them.

**Knowledge base workflow (non-negotiable — corrected Session Z):**
The GitHub repo IS the permanent store. The Mac local copy is transit only.
Workflow: git pull on Mac → Desktop Commander writes file to Mac → git push from Mac → file lives in GitHub permanently.
The Mac local copy expires each session. The GitHub repo does not.
Knowledge files do NOT auto-deploy to Cloud Run. They are static specs read via raw GitHub URL.

**main.py — Session AD (current HEAD — commit `3f15ea7`; was 36bcc3b through AB)**
Session AD — `SESSION_CLOSER_PROMPT` rule against re-asking triage-captured logline:
- Live test surfaced: dashboard triage captures a one-sentence logline (Q2), then routes into a building whose first step asks for the same thing again — ideate's "One Sentence" step (idea branch) and develop's "What's the Premise?" step (treatment branch) both duplicate it. Audited all 12 buildings' step lists — only these two overlap, every other building asks domain-specific questions triage never touches (budget, crew, rights, platform, campaign, revenue), so this isn't systemic.
- Added explicit rule to `SESSION_CLOSER_PROMPT`: don't route to a step whose core question duplicates what triage already captured, route to the next step in the same section instead.
- Companion fix in dashboard.html's `localFallbackRoute()` (deterministic backstop when the orchestrator fails twice) — idea branch now lands on Gut Check/"Does This Have Legs?" instead of Raw Idea/"One Sentence"; treatment branch lands on Story & Structure/"Who's It For?" instead of "What's the Premise?"; script branch unchanged (its landing step was already clean).
- Push triggers GitHub Actions → Cloud Run auto-deploy, no manual redeploy needed.

Session AB — Fable 5 flip implemented + compat fix, both LIVE and verified:
- Commit `a4f3eae`: env-var model tiers. `SURFACE_MODEL` (FY_SURFACE_MODEL, default sonnet-4-6) and `ORCHESTRATION_MODEL` (FY_ORCHESTRATION_MODEL, default opus-4-8). The documented "single env var swap" had never actually been implemented — code had six hardcoded `claude-opus-4-7` calls and inverted tiers (`/api/chat` on opus, routing on sonnet). Now: `/api/chat` → SURFACE_MODEL; `/api/session/close` routing + 4 formation endpoints + debug → ORCHESTRATION_MODEL. `deploy-cloudrun.yml` sets `FY_ORCHESTRATION_MODEL=claude-fable-5`, `FY_SURFACE_MODEL=claude-sonnet-4-6` (plaintext env vars, not secrets). Rollback = one workflow line + push.
- Commit `36bcc3b`: `claude_text(response)` helper — Fable 5 returns reasoning blocks before text blocks, so `content[0].text` is None and crashed `session_close` (found via Cloud Run logs: AttributeError mid-Lee's-test). All 7 `content[0].text` sites converted. Verified live post-deploy.
- Latent bug logged, NOT fixed: `/api/chat` with no system prompt 500s (`system=None` passed explicitly to SDK). All real callers pass a system prompt. Fix when convenient.

**studioyou-fy-agent repo — Session W, AA**
Session AA (commit `79dbb03`): Avatar provider swap, Tavus → Runway Characters.
- `agent.py`: `tavus` plugin → `runway`; `TAVUS_REPLICA_ID`/`TAVUS_LIVEKIT_PERSONA_ID` → `RUNWAY_AVATAR_ID` (env lookup); `RoomOutputOptions(audio_enabled=True)` → `False` (Runway muxes audio+video, avoid doubling); docstring corrected.
- `requirements.txt`: `livekit-plugins-tavus` → `livekit-plugins-runway`. Pip also bumped `livekit-agents` 1.6.0→1.6.4 and `livekit` 1.1.8→1.1.12 as dependency resolution — not requested, worth a smoke test if anything unrelated behaves oddly.
- `.env`: added `RUNWAYML_API_SECRET` and `RUNWAY_AVATAR_ID` (Lee entered directly, never passed through chat). **These live in the agent's own `.env`, NOT Cloud Run env vars** — avatar rendering happens in the LiveKit agent process, not `main.py`.
- Agent recreated: `CA_eESBzjexFe9C` deleted → `CA_hJH2hG3UdrR3` created (worker `CAW_XZ5ohXyCBSGe`, region US East B). Confirmed live and lip-syncing correctly via screenshot.
- **New workflow rule, locked Session AA:** `studioyou-fy-agent` now gets the same git discipline as `main.py`/`knowledge/` — pull before edit, commit+push after, even though deploy runs off local disk via `lk agent create` rather than GitHub Actions. GitHub stays the record of what's actually running. See FILE WORKFLOW section below.
- **Flagged, unresolved:** pre-existing uncommitted `Dockerfile` changes and untracked `.dockerignore`/`livekit.toml` found in this repo, predating Session AA. Not touched. `lk agent create` builds from local disk — review before next recreate. Still present as of Session AC recreate — only `agent.py` was staged/committed, Dockerfile drift untouched again.

**Session AC (commit `aff7c1b`):** Avatar toggle now actually stops Runway billing instead of just muting client-side audio. Runway Characters bills 2 credits upfront + 2 credits per 6s of active avatar-session time (confirmed via Runway docs) — not per utterance, so muting does nothing to the charge. `agent.py` now tracks the live `runway.AvatarSession` in `avatar_state`; `stop_avatar()` calls `av.aclose()` (same teardown path the plugin runs on normal job shutdown per Runway's own docs) on `fy_avatar_control` topic with `on:false`; `start_avatar()` creates a fresh `AvatarSession` on `on:true`. Lock guards double-toggle races. `studio.html` (Session AC, deployed and confirmed by Lee) publishes the toggle state on that topic in addition to muting local audio elements immediately.
Unverified: whether `runway.AvatarSession.aclose()` actually exists on this plugin version and actually stops Runway billing — inferred from the shared `BaseAvatarSession` pattern (other providers expose it) and Runway's docs language, not confirmed against Runway's own usage snippet. Needs a live test: toggle off, check agent logs for "Avatar session closed" with no exception, check Runway credit ledger for the meter actually stopping.
Agent recreated for this code change: `CA_hJH2hG3UdrR3` deleted → `CA_gHcpYouSmW6Y` created, region us-east. Confirmed build succeeded, deploy completed.

**Session AC, second recreate (commit `8b37e1f`):** Live-test surfaced the handoff line not being spoken in full. Root cause: `speakLine()` in dashboard.html asked the LLM to comply with a `[SPOKEN LINE] Say this exact line and nothing else: "..."` text convention via `session.generate_reply(user_input=text)` — the model's system prompt had zero awareness of that convention, so it would truncate or paraphrase instead of reciting verbatim. Fixed by adding a `fy_say_verbatim` message type in agent.py that calls `session.say(text, allow_interruptions=False)` directly — bypasses the LLM turn entirely, guaranteed verbatim. dashboard.html's `speakLine()` now publishes `fy_say_verbatim` instead of the old `fy_chat` wrapper hack.
Agent recreated again: `CA_gHcpYouSmW6Y` deleted → `CA_HLJDfBDvSj8E` created, region us-east. Session AD: `CA_HLJDfBDvSj8E` deleted → `CA_VyEg7PNceKBc` created, region us-east — avatar rotation fix (`dae3ea8`). Session AD (second recreate): `CA_VyEg7PNceKBc` deleted → `CA_2P82mL8o4yn5` created, region us-east — pronunciation dict wiring, sonic-3.5 + Jameson voice switch, acronym-spacing prompt rule (`1c52654`). Session AD (third recreate): `CA_2P82mL8o4yn5` deleted → `CA_bfB2ATWADGC2` created, region us-east — voice swap Jameson → Nolan (`46e6c2a`), Jameson read as unintended accent/ethnicity coding on this voice. Session AD (fourth recreate): `CA_bfB2ATWADGC2` deleted → `CA_uqgwZctcttb9` created, region us-east — voice swap Nolan → Corey (`630ed21c-2c5c-41cf-9d82-10a7fd668370`, "Corey - Supportive Buddy," en-US masculine, `63a6faa`), Nolan read as "too breathy and a little creepy." Session AD (fifth recreate): `CA_uqgwZctcttb9` deleted → `CA_TJpDATHwLRkE` created, region us-east — dropped `pronunciation_dict_id` (`48b6462`) to test sonic-3.5's native pronunciation. Session AD (sixth recreate): `CA_TJpDATHwLRkE` deleted → **`CA_QcasXGFg5U4m`** created, region us-east — dropping the dict on sonic-3.5 did NOT fix pronunciation ("ideate" still wrong natively), confirming the dict likely wasn't honored on 3.5 in the first place. Reverted model sonic-3.5 → sonic-3 with `pronunciation_dict_id` restored (`2a705be`) — only documented-supported combination. Bonus: speed/volume controls also functional again, they were disabled specifically on sonic-3.5 per Cartesia's migration notes.

**Session AC finding, not yet fixed — root cause of the "avatar dropped randomly" reports (occurred twice, live tests both times):** Runway's Characters API hard-caps every realtime session at a maximum of 5 minutes, platform-side (confirmed via Runway's own docs — this is a Session concept boundary, not something `max_duration` can extend past, only shorten). `agent.py` never set `max_duration` and has no rotation/renewal logic — so any conversation running past ~5 minutes since the avatar joined WILL drop it, deterministically, every time, with zero auto-recovery in either the old code or the Session AC changes. Not random. Queued for Session AD: build proactive rotation (close + reopen the `AvatarSession` a few seconds before the 5-minute mark) so it never dies mid-conversation. Will cause a brief visible respawn on rotation — worth deciding whether to try to hide it or treat it as an expected beat, same design question as the dashboard→studio handoff respawn.

---

## FY ARCHITECTURE — Locked Session T (canonical, do not override without explicit session decision)

### Three-Tier Brain Stack

**Tier 1 — FY Conversational Surface**
Model: `claude-sonnet-4-6`
Role: Creator-facing. Voice loop, real-time chat, in-character FY delivery. Stays thin.

**Tier 2 — FY Orchestration Brain**
Model: `claude-opus-4-8` (interim) → `claude-fable-5` (when restored)
Role: Full creator journey context, formation data, project state, building history, cross-session memory. Decides what to dispatch, to which sub-agent. Synthesizes results before returning to Tier 1. Runs async.
**Session AA addition:** `orchestrator_context` now includes `active_step_progress` (building/section/step/success_state_condition/satisfied/satisfied_by) — dispatch fires when `satisfied: True`, evaluated deterministically against the active step's SUCCESS STATE, not FY's independent judgment. See Section 6.1 in `FY_LAYER2_SCHEMA.md`.

**Tier 3 — Building Sub-Agents**
Framework: Claude Agent SDK
Model: `claude-sonnet-4-6` per execution
Role: Building-specific execution. Tool API calls. Canvas card production.

**Fable swap — single env var, no code change:**
```python
ORCHESTRATION_MODEL = os.environ.get("FY_ORCHESTRATION_MODEL", "claude-opus-4-8")
# When Fable returns: set FY_ORCHESTRATION_MODEL=claude-fable-5
```

**Fable 5 status:** Suspended June 12, 2026 via US government export control directive, restored July 1, 2026. **Swap EXECUTED Session AB — claude-fable-5 is the LIVE Tier 2 brain in production** (verified via /api/debug/claude-test). Opus 4.8 is the code-level default fallback; rollback = one line in deploy-cloudrun.yml. Lee reports Fable hits session/usage limits quickly — if 429s bite production routing, add fallback-to-opus on rate-limit errors (not built, watch first).

### FY Avatar Mode Architecture (locked Session U, provider updated Session AA)

**Mode 1 — Chat only (avatar off):** LiveKit + Deepgram only when mic active.
**Mode 2 — Full avatar (avatar on):** Full pipeline: LiveKit + Deepgram + Cartesia + **Runway Characters** (was Tavus through Session Z; swapped Session AA — see studioyou-fy-agent entry above).

### FY Agent — LiveKit Cloud Deploy

**Agent ID:** `CA_QcasXGFg5U4m` — RUNNING, us-east (LiveKit Cloud). **Changed Session AD (sixth recreate)** — reverted model sonic-3.5 → sonic-3, `pronunciation_dict_id` restored (`CARTESIA_PRONUNCIATION_DICT_ID=pdict_EFg3YUoQfZfzyupNVwiFL9`, `2a705be`). Dropping the dict on sonic-3.5 last recreate did NOT fix pronunciation — "ideate" still wrong on sonic-3.5's native pronunciation alone — confirming the dict likely wasn't honored on 3.5 to begin with, and Cartesia's own docs only officially support pronunciation dictionaries on sonic-3. sonic-3 + dict is the only combination with documented support. Bonus: speed/volume controls are functional again on sonic-3 (were disabled specifically on sonic-3.5 per Cartesia's migration notes). Was `CA_TJpDATHwLRkE` (dropped dict to test sonic-3.5 native, `48b6462`), before that `CA_uqgwZctcttb9` (voice swap Nolan → Corey, `630ed21c-2c5c-41cf-9d82-10a7fd668370`, `63a6faa` — Nolan read as too breathy and creepy), before that `CA_bfB2ATWADGC2` (voice swap Jameson → Nolan, `46e6c2a` — Jameson read as unintended accent/ethnicity coding), before that `CA_2P82mL8o4yn5` (pronunciation dict wired, model switched sonic-3 → sonic-3.5, acronym-spacing rule added to FY_OPERATIONAL_RULES; `1c52654`). Before that `CA_VyEg7PNceKBc` (avatar rotation fix, `dae3ea8`), before that `CA_HLJDfBDvSj8E` (Session AC twice — avatar-billing-stop fix, then the say-verbatim handoff-line fix), before that `CA_gHcpYouSmW6Y`, before that `CA_hJH2hG3UdrR3` (Session AA before that: `CA_eESBzjexFe9C`, deleted and recreated for the Runway swap).
**Update command:** `lk agent update CA_QcasXGFg5U4m` — for config-only changes.
**Open issue, not yet diagnosed:** avatar could not restart after first studio landing on the sonic-3.5-native test. No agent logs captured for that failure yet — need `lk agent logs` for the window it happened before this can be investigated further.
**CONFIRMED Session W, reconfirmed Session AA:** `lk agent update` does NOT trigger a real rebuild. To deploy new agent code: `lk agent delete --id <ID> && lk agent create`. Agent ID changes on recreate — update claude.md.

### Dashboard→Studio Handoff
Write (dashboard): `{role:'user'|'fy', text}` array to `localStorage.sy_fy_conversation` after every exchange.
Read (studio): `connectLiveKit` sends last 10 messages to `/api/avatar/livekit-session`. `initFY` injects last 6 inline.
**RESOLVED Session AB:** keep the warm-room handoff. Studio reuses the dashboard's LiveKit token (<50 min) and the agent + Runway worker survive navigation (proven in Lee's test — video rendered, agent replied via data channel; the agent retains the dashboard conversation in its own session memory). The ONLY gap was studio never attaching audio tracks — fixed. Residual flagged: if a creator closes the tab instead of navigating, agent + Runway idle in the room burning credits until timeout — agent-side max_duration/idle-timeout item, post-AIEWF.

### ADMIN Layer — Canonical State

| Component | Status | Role |
|---|---|---|
| Claude Agent SDK | Active | Sub-agent framework (Tier 3) |
| Opus 4.8 | Active — fallback default | Tier 2 code-level default; rollback target |
| Fable 5 | **ACTIVE — LIVE Tier 2 brain (flipped Session AB)** | Orchestration: routing + formation endpoints |
| Sonnet 4.6 | Active | Tier 1 + Tier 3 execution |
| Runway Characters | Active — live | Avatar rendering (was Tavus through Session Z) |
| Twin | Active — specific function | Browser automation for no-API tools (FilmPro, Styleframe, storyboard tools) |
| OpenClaw | RETIRED | OpenAI acquisition = vendor conflict. Replaced by Claude Agent SDK. |
| Emergent Labs | RECLASSIFIED OUT | Vibe coding tool, not SY infrastructure. |
| Kindo | RECLASSIFIED OUT | OMNIShield only. |
| Filmustage | REMOVED | No relationship. FinalBit covers same ground. |

### Tier 3 — Building Sub-Agent Domain Map

| Building | Type | Primary Tools | Canvas Output |
|---|---|---|---|
| IDEATE | Execution | Perplexity, Midjourney (Twin), Firefly, FAL.ai | Concept brief |
| DEVELOP | Execution | Screenplayer.ai → FilmPro Co-Writer (Twin) → FinalBit → Quilty + Storyboard (Direct/FAL/Twin) + Suno/AIVA/LALAL.AI (music) | Script, storyboard, demo, visual direction, content framework |
| FUND | Execution | Startup Science, Raisi, FinalBit, Line Budgeter | Budget, investor brief, pitch deck |
| CAST | Advisory only | StudioBinder (tracking only) | Talent brief, character breakdown |
| PLAN | Execution | FinalBit (filmmaker) / FilmPro via Twin (content creator), Saturation.io, Wrapbook | Schedule, crew list, call sheet, budget |
| PRODUCE | Advisory | None active | Daily report, production note |
| POST | Execution | Descript, Runway, Suno/Udio/AIVA, ElevenLabs, LALAL.AI | Edit, music, VFX, VO |
| LEGAL & LICENSING | Hybrid | CLIPClear, YouScored, Harvey AI, Spellbook | Contract, clearance report, IP brief |
| DISTRIBUTE | Advisory + assist | Feedhive, Beacons.ai | Distribution strategy, release timeline |
| BRAND | Execution | Canva (MCP), Air Canvas, Firefly (MCP), Kittl | Logo, brand kit, style guide |
| MARKET | Execution | Feedhive, Palo, CreatorIQ, HeyGen, Canva (MCP) | Campaign brief, content calendar |
| MONETIZE | Execution | CreatorIQ, Beacons.ai, RollCredits.io, Quilty, Startup Science | Brand deal brief, revenue dashboard |
| ANALYZE | Infrastructure | Mixpanel (candidate), CreatorIQ | FY routing signals |
| ADMIN | Infrastructure | Claude Agent SDK, Twin, Airtable, Notion, Perplexity | Orchestration, Supabase writes |

### DEVELOP Tool Sequence — Locked (Session Z)
1. Screenplayer.ai — concept to first draft
2. FilmPro Co-Writer (Twin) — interactive revision agent (partner agent deference applies)
3. FinalBit — script lock, breakdown, coverage, storyboard, production pipeline
4. Quilty — coverage + commercial viability scoring
5. Storyboard: Direct API (Styleframe if confirmed) → FAL.ai → Twin → Midjourney/Firefly/Leonardo
6. Music: Suno / Udio / AIVA → ElevenLabs (vocal) → LALAL.AI (stems)
7. Video generation (animatic/generative AI mode): Runway ML / Kling / Hailuo / Wan — routed by documented success context

### PLAN Tool Routing — Locked
- **Independent filmmaker** → FinalBit via exclusive API (breakdown → schedule → budget as connected workflow)
- **Content creator / entry-level** → FilmPro via Twin
- Both tiers: Saturation.io (crew hire), Wrapbook (payroll + contracts)

---

## LOCKED DECISIONS — Session AA

### Success State as Literal Dispatch Trigger (Section 6.1, FY_LAYER2_SCHEMA.md)
SUCCESS STATE is not narrative tone guidance — it is the literal, checkable condition Tier 2 evaluates against creator input to decide the moment a step is satisfied and dispatch (to Tier 3, or the next step) should fire. Same principle as the triage fix, applied at step granularity: don't trust the model to self-determine "I have enough," replace that judgment with a deterministic check. Binding on every building spec, retroactive audit required for pre-existing specs (IDEATE and DEVELOP both completed this session).

### Creator-Facing Litmus Test — Outweighs Tier 2 Checkability
Added second, weighted higher than the Tier 2 test above: does the creator understand exactly what they're being asked, clearly enough that they never try to guess the "right" answer instead of giving their real one? There is no right or wrong answer at any step in any building — the creator is building a structure, and every structure has a foundation, then floors, regardless of creative type. A foundation is either poured or it isn't — never judged for quality, only presence. A condition can be perfectly checkable by code and still fail this test if it makes the creator feel evaluated.

### Triage-Stage FY Is a Router, Not a Conversationalist
FY's job during dashboard triage is solely to gather enough intel to make a concrete routing decision — not to have a creative conversation. Confirmed as the reasoning behind two decisions: (1) the hard 2-exchange cutoff has no "not yet" opt-out, because whatever's said persists via `sy_fy_conversation` regardless of how routing terminates, so nothing is lost; (2) routing navigates immediately regardless of avatar session state, because there's no in-progress creative dialogue at this stage worth protecting.

### `studioyou-fy-agent` Git Workflow — Same Discipline as main.py/knowledge/
See FILE WORKFLOW section below and the studioyou-fy-agent entry in Current Build State.

---

## LOCKED DECISIONS — Session AB

### Warm-Room Handoff Is the Dashboard→Studio Architecture
Fresh-session-on-studio-load rejected on evidence: the LiveKit room, agent, and Runway worker survive navigation; studio's token reuse gives instant avatar plus agent-side conversation continuity. The audio gap was a missing track attach, not a lifecycle problem. (See Dashboard→Studio Handoff.)

### Model Tiers Are Env-Var Driven, Enforced in Code
`FY_SURFACE_MODEL` / `FY_ORCHESTRATION_MODEL` in deploy-cloudrun.yml are the single source of model assignment. Never hardcode a model string in main.py again — new Claude calls use SURFACE_MODEL or ORCHESTRATION_MODEL.

### PLAN Spec Inputs (Lee, Session AB)
1. FinalBit API not confirmed (custom API in discussion) — FilmPro/Twin primary for BOTH tiers for now; FinalBit primary-pending with documented cutover.
2. FY owns planning methodology and tool dispatch: FY leads, decides what tool fits the task, deploys based on the answer it just received. Canvas shows live results; left rail shows activity so the creator follows and learns. Saturation.io + Wrapbook are FY territory.
3. PLAN Ignition branches on archetype/format (filmmaking→live/generative; animation→2D/3D; YouTube→talking head/series; vertical series→live action?/length; podcast→elements/subject/frequency), converging on a universal spine: schedule, budget, team/resources, production calendar.
4. Neil (FinalBit) deference boundary — researched from FinalBit docs: Neil owns stripboard/scheduling MECHANICS only (stripboard reorganization, constraint optimization, day-out-of-days, auto day-breaks, DOOD exports). Budgeting/breakdown/shot lists are FinalBit platform features, not Neil. FY keeps methodology, budgeting philosophy, team, resources.

---

## DEPLOY PIPELINE

**Single pipeline: GitHub Actions only.** Every push to `main` on `supercreativepeople/studioyou-backend` triggers: authenticate → build Docker → push GCR → deploy Cloud Run with `--set-env-vars` from GitHub Secrets → verify.

**Never manually trigger Cloud Build** — it no longer exists.

**Note:** this pipeline covers `main.py` only. `studioyou-fy-agent` deploys separately via `lk agent create`/`lk agent update`, off local disk — see below.

---

## FILE WORKFLOW (non-negotiable)

**Frontend files (dashboard.html, studio.html, index.html, etc.):**
Lee provides in chat → Claude modifies in container → `present_files` → Lee downloads → Netlify drag-and-drop.
Never fetch frontend files from GitHub. Never assume they are current.

**Backend main.py:**
1. `git -C /Users/supercreativepeople/Projects/studioyou-backend pull origin main`
2. Desktop Commander Python script modifies main.py on Mac
3. `git add main.py && git commit && git push origin main`
4. GitHub Actions auto-deploys to Cloud Run.

**Knowledge/ files (specs, schemas):**
1. `git -C /Users/supercreativepeople/Projects/studioyou-backend pull origin main`
2. Desktop Commander writes .md file to Mac at knowledge/ path
3. `git add knowledge/... && git commit && git push origin main`
4. No auto-deploy. Files read via raw GitHub URL at session open.
5. Claude reads at session open: `curl -s "https://raw.githubusercontent.com/supercreativepeople/studioyou-backend/main/knowledge/buildings/[FILENAME].md"`

**studioyou-fy-agent (agent.py, requirements.txt, etc.) — locked Session AA:**
Same discipline as main.py/knowledge/, despite deploying differently:
1. `git -C /Users/supercreativepeople/Projects/studioyou-fy-agent pull origin main`
2. Desktop Commander edits files on Mac
3. `git add ... && git commit && git push origin main`
4. Deploy separately: `lk agent update` (config-only) or `lk agent delete --id <ID> && lk agent create` (code changes — see LiveKit / FY Agent Reference)
5. GitHub push does NOT trigger deploy here — it's still required so GitHub remains the record of what's actually running, matching the same principle already locked for knowledge/ files.

**claude.md — locked Session AD:**
Version-controlled at the root of `studioyou-backend` (same repo as `knowledge/`), not just a local Mac file.
1. Claude updates the working copy each session as before.
2. `present_files` to Lee — unchanged, Lee still gets it every session the same way.
3. Claude commits and pushes `claude.md` to `studioyou-backend` root as the last step of session close.
4. Gives version history and a remote copy independent of Lee's local disk. Lee separately backs up every file to a historical repo on local Mac, mirrored to two Google Drive accounts — this is a third, independent, diffable copy, not a replacement for those.

Rules applying to all backend work:
- Never surface the GitHub PAT in chat output; strip it from any remote URL immediately after use
- **Locked Session AD — supersedes prior rule:** Claude has direct push access to `studioyou-fy-agent` and `studioyou-backend` via a fine-grained PAT (Contents: Read/write, 90-day expiration) supplied fresh each session by Lee, since the sandbox holds no persistent credentials. Claude clones, edits, commits, and pushes directly from the container for these two repos. The old "never clone backend into container for push purposes / container never pushes, only reads via raw URL" rule is gone — that assumed no credential path existed. It still applies to any repo Claude does NOT hold a PAT for.

---

## CLOUD RUN ENV VARS — Session V State

**Confirmed live (16 vars, studioyou-api, us-east1):**
`GITLAB_TOKEN`, `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `SY_SECRET_KEY`, `FRONTEND_URL`, `REACTOR_API_KEY` (rotated Session V → gmail account), `FAL_API_KEY`, `TAVUS_API_KEY`, `FUTUREYOU_PERSONA_ID`, `TAVUS_LIVEKIT_PERSONA_ID`, `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

**Session AB additions:** `FY_ORCHESTRATION_MODEL=claude-fable-5`, `FY_SURFACE_MODEL=claude-sonnet-4-6` (plaintext in deploy-cloudrun.yml, not GitHub Secrets — 18 vars total now).

**Note, Session AA:** the `TAVUS_*` vars above are unused now that the LiveKit agent uses Runway (see studioyou-fy-agent entry) — left in place, not cleaned up, low priority. Runway's credentials (`RUNWAYML_API_SECRET`, `RUNWAY_AVATAR_ID`) do NOT live here — they're in the LiveKit agent's own `.env` on the Mac, since avatar rendering happens in that separate process, not `main.py`/Cloud Run.

---

## LiveKit / FY Agent Reference

**Agent ID:** `CA_QcasXGFg5U4m` — RUNNING, us-east (LiveKit Cloud). Changed Session AD (sixth recreate) — reverted sonic-3.5 → sonic-3, restored pronunciation_dict_id. Was `CA_TJpDATHwLRkE` (dropped dict, tested sonic-3.5 native), before that `CA_uqgwZctcttb9` (voice swap Nolan → Corey), before that `CA_bfB2ATWADGC2` (voice swap Jameson → Nolan), before that `CA_2P82mL8o4yn5` (pronunciation dict, sonic-3.5, acronym rule), before that `CA_VyEg7PNceKBc` (avatar rotation fix), before that `CA_HLJDfBDvSj8E` (Session AC twice), before that `CA_gHcpYouSmW6Y`, before that `CA_hJH2hG3UdrR3` (Session AA before that: `CA_eESBzjexFe9C`).
**Local run (debug only):**
```bash
cd /Users/supercreativepeople/Projects/studioyou-fy-agent
source .venv/bin/activate
python agent.py dev
```

**Stale LiveKit state** — clear when rooms die between sessions:
```javascript
['sy_lk_token','sy_lk_url','sy_lk_room','sy_lk_ts','sy_avatar_status'].forEach(k => localStorage.removeItem(k));
```

---

## FY Behavioral Rules — Locked

- FY is project manager and puzzle keeper — buildings/sections/steps IS the project
- Stick to active project intent until creator explicitly signals otherwise
- Wandering into another building = piece of current project — connect it, do not redirect
- Stops asking when it has enough to act; synthesizes after three exchanges without direction
- Never performs enthusiasm. Never recaps. Acts.
- Never evaluates creator output — additive language only: "let's build on this / let this breathe"
- Language principle: "tell me in your own words" — open field first, pills as anchors
- Under 40 words unless creator explicitly asks for depth
- Never start with "I" — start with the insight
- End with question or directive, never a summary
- No bullet points, no lists
- DIRECTIVE MODE (Independent tier): FY initiates, always proposes next concrete action
- PEER MODE (Operator tier): Creator drives, FY responds when called
- **Session AA addition, triage stage specifically:** FY is a router at this stage, not a conversationalist. Its entire job is gathering enough intel to make a concrete building/section/step decision — not creative development. See LOCKED DECISIONS — Session AA above.

---

## Critical Technical Rules

**Code editing:** `grep -n` for exact line numbers. Python replace for complex multi-line blocks. Never use `sed` for JS function bodies.

**JSX syntax:** `forwardRef` closes with `});`. JSX comments in closing tags break Babel.

**Apostrophes in JSX single-quoted strings:** Use double quotes for strings containing apostrophes.

**React flex layouts:** Always add `min-height:0` to flex children that need to scroll.

**Python replace scripts:** Always verify old string exists before replacing. Print result status. Always write file back after replace.

**`--set-env-vars`:** Permanently moved to `--set-env-vars` from GitHub Secrets. Never use `--update-env-vars`.

**Git divergent branches:** `git pull origin main --rebase` then push.

**Supabase URL empty = MissingSchema errors.** Always verify env vars post-deploy.

**backdrop-filter stacking context rule:** Modals inside a backdrop-filter parent must use `ReactDOM.createPortal` to `document.body`.

**GitHub token security:** Never surface in chat. Lives in Mac's local git remote URL.

**Babel CDN:** Always use pinned `@babel/standalone@7.23.10`. Never unpinned.

**livekit-client in Babel pages:** Load dynamically inside component code, never as a static `<script>` tag. Pin to `livekit-client@2.9.9`.

**livekit-agents Python version:** Use Python 3.11. Python 3.13+ has asyncio subprocess compatibility issues.

**LiveKitAPI init:** Must be inside async context with running event loop.

**Supabase column queries:** Always verify against `information_schema.columns WHERE table_name = 'X'` before assuming.

**Claude response parsing (Session AB):** NEVER use `response.content[0].text` — reasoning-class models (Fable 5) return thinking blocks before text blocks. Always use main.py's `claude_text(response)` helper (returns first block with type=="text" and non-empty text).

**Python regex substitution writing JS strings:** Use `String.fromCharCode(10)` for newlines and lambda functions in `re.sub()` calls. Never write literal newlines inside JS single-quoted strings — causes Babel syntax errors.

**Desktop Commander MCP reliability, noted Session AA:** occasionally times out (observed: 4-minute timeout, tool call had actually succeeded server-side despite the error returned to Claude). If a call times out, verify actual file state via `read_file`/`grep` before assuming it failed and retrying blind — retrying a call that already succeeded can produce confusing "closest match" fuzzy-search errors on the next attempt.

---

## Strategic

**Make Believe — Ben Relles** — Meeting June 1, 2026. Pitch: StudioYou as sovereign production infrastructure. White-label enterprise tier.

**Reactor Partnership** — Alberto (CEO), $59M funding. Meeting originally planned for July 1 — **pushed. Now meeting at AIEWF, July 2, before Ahmed's speaker session.**
Accounts: `lee@supercreativepeople.com` (OUT OF CREDITS, confirmed again Session AA — degrading gracefully to static mode, not blocking chat/avatar/routing); `supercreativepeople@gmail.com` (has active tokens — use this for LingBot wiring).
PIVOT (Session W, in progress): Pre-generate 30-60s archetype background videos offline. Lee building replacement videos directly as of Session AA, to fire until after the AIEWF meeting. Live Reactor reserved for production content inside buildings only.

**FilmPro** — NDA signed 05/06/2026. No API near-term per CEO. Twin-mediated. Co-Writer in DEVELOP, entry-level PLAN. Partner agent deference applies.
**FinalBit** — Exclusive API partnership discussions; custom API build in discussion (Session AB — NOT confirmed). FilmPro/Twin is PLAN primary for BOTH tiers until the API lands; FinalBit primary-pending with documented cutover. Neil = stripboard/scheduling mechanics only (deference boundary defined Session AB from FinalBit docs).
**Styleframe** — Storyboard tool in partnership discussions. May be API viable. If confirmed: slots into Direct API position in storyboard routing priority order.
**Quilty** — Three-building presence: DEVELOP (coverage), FUND (viability), MONETIZE (representation). High priority partnership.
**OpenArt Creator Program** — Accepted, unlimited tier. Primary competitive benchmark (DIRECTOR feature).

---

## Session AD Open Items

### Priority 1 — Avatar Session Rotation (Runway 5-minute hard cap)
Root cause confirmed Session AC: Runway Characters sessions hard-cap at 5 minutes platform-side, no client-side override past that ceiling, no renewal logic exists in agent.py. Build proactive close+reopen of the `AvatarSession` before the cap hits (e.g. schedule at ~270s from `start_avatar()`), reusing the same `avatar_state`/`stop_avatar()`/`start_avatar()` plumbing from the Session AC billing-stop fix. Decide whether the visible respawn on rotation should be masked (harder, may not be fully possible given a new Runway worker = new track) or treated as an acceptable beat, same as the dashboard→studio handoff gap. Do alongside Priority 2 — both touch agent.py, worth one recreate instead of two.

### Priority 2 — Voice / Pronunciation Work
Cartesia plugin already defaults to `sonic-3` and already supports `pronunciation_dict_id` — currently unused. Build a pronunciation dictionary in Cartesia's dashboard covering FY's recurring vocabulary (building names — "ideate" was the reported failure — plus StudioYou/FutureYou), wire `pronunciation_dict_id` into `cartesia.TTS()` in agent.py. Also test the `speed` param (currently unset) for the reported cadence/emphasis issue. Independent of Priority 1's cause but same file — bundle into the same recreate.

### Priority 3 — Vault / Metadata Capture Spec (new, scoped as its own spec per Lee)
Lee's framing: this is the first critical user-provided information architecture, not a small patch. Every answer a creator gives inside a canvas step (logline, scene beats, superpower details, etc.) currently exists only as ephemeral chat state — never persisted, never structured, nothing feeds forward as deterministic metadata to later steps/sections/tool calls. Checked existing Vault system (studio.html `_cdState.vaultAssets`/`vaultAdd()`): it only captures generated TOOL outputs (images, video) via 2 call sites, isn't Supabase-persisted at all, has zero hook into conversational Q&A.
Needs, before writing code: (a) data model — Supabase table, `fy_` prefixed per convention, what fields per captured snippet (step_id, building, question, answer, timestamp, type); (b) capture trigger — does the agent decide via a tool call when something is vault-worthy, or does the frontend heuristically capture on every step/section completion; (c) visual representation on canvas — Lee's proposal: sticky note / 3x5 index card graphic, pinboard-style, not unlike pre-computer story structuring (cards on a corkboard, moved around as scenarios were discussed). Scope and spec this the same way PLAN was specced — Lee's methodology/requirements transfer needed before writing the schema.

### Priority 4 — PLAN Sub-Agent Spec (skeleton proposed Session AB — awaiting Lee's confirm + methodology transfer)
Inputs locked (see LOCKED DECISIONS — Session AB): FilmPro/Twin primary both tiers, FY owns methodology + dispatch, archetype/format-branched Ignition converging on universal spine (schedule, budget, team/resources, production calendar). Neil boundary defined. Methodology transfer needed from Lee: schedule sequencing/lock order, budgeting philosophy for under-resourced productions, planning-stage failure patterns, one-person-with-AI vs. physical-set planning. Voice-memo style, raw, out of order — same as DEVELOP.
Now on a validated foundation — IDEATE and DEVELOP both audited against Section 6.1, handoff chain confirmed field-clean end to end (IDEATE→DEVELOP→PLAN). Third "naked on stage" building. FY shifts from creative director to executive producer.
Lee's production planning methodology to encode: scheduling, budgeting, team, resources.
FinalBit's breakdown agent is primary tool — partner agent deference applies. Neil (FinalBit's embedded scheduling agent) is the Co-Writer equivalent for PLAN — scope of what Neil handles vs. what FY covers directly still undefined, needs answering during spec writing.
Handoff from DEVELOP: receives production_mode, development_lock, visual_package, casting_brief — all confirmed present and correctly structured.
**Every step's SUCCESS STATE must be written to Section 6.1 standard from the start** — checkable by Tier 2, and passes the creator-facing litmus test. Use IDEATE/DEVELOP's now-fixed entries as the model, especially the "specific sentence, not vague — [example]" pattern from M-1/V-1/B-1.

### Priority 5 — Tier 2 Orchestrator Spec
What Opus/Fable receives, how it selects sub-agent, what it dispatches, what it returns.
Required before any end-to-end testing is meaningful.
Now has a real mechanical hook: `active_step_progress`/`satisfied` field added to `orchestrator_context` this session — orchestrator spec should define exactly how that field gets evaluated each turn.
PLAN spec should inherit partner agent deference principle explicitly (FinalBit's agent).

### Priority 6 — Wire IDEATE into Live Agent
IDEATE spec complete and now audited → becomes prompts.py system prompt.
Requires orchestrator spec first.

### Priority 7 — Super Somebody Benchmark
FY vs. OpenArt DIRECTOR. Same brief, same scene. Primary model success context data source for IDEATE and DEVELOP simultaneously.

### Lee's Ongoing Work
Organizing AI model testing data to populate model success context entries.
Format: task type → failure mode → which models fail → which succeed → prompt engineering fix. Will provide as data; Claude structures and encodes into sub-agent specs.
Building replacement archetype background videos directly (see Reactor Partnership above).

### Carried, Untouched
- [ ] Archetype background videos (Lee building directly as of Session AA, was assigned to LittleBird)
- [ ] first_words personalized greeting
- [ ] Twin evaluation for no-API tool automation
- [ ] Step completion signal → vault save
- [ ] Trackpad pinch zoom on spatial canvas
- [ ] Bill of Rights throttle disclosure
- [ ] Studio.html tour (first building entry)
- [ ] Vault page
- [ ] Multi-user team architecture
- [ ] MONETIZE building GIF
- [ ] Tavus Custom plan — reverted to Free June 20, 2026 (requires BD follow-up; may be moot now that Runway is the live avatar provider — worth confirming whether Tavus relationship still matters at all)
- [ ] **Tavus Phoenix "aging your photo" personalized-avatar flow — confirmed dead code Session AA, not removed.** `replicaId` state, `'training'` mode render block, `startConversation()` all unreachable from the UI — no file upload input exists, `dragOver` state declared but never wired. Left in place per Lee's explicit choice not to strip mid-demo-day. Revisit whenever a personalized-avatar feature is actually specced, or strip as cleanup.

---

## Infrastructure Reference

**Domain registrar:** Porkbun (studioyou.app)
**DNS / CDN / Zero Trust gate:** Cloudflare
**Frontend host:** Netlify → studioyou.app
**Backend:** Cloud Run → studioyou-api → us-east1 → neat-tangent-474222-m9
**Backend URL:** https://studioyou-api-198959034459.us-east1.run.app
**DB:** Supabase → rubwhfjwqonqhfbkhren. RLS disabled.
**GitHub:** supercreativepeople/studioyou-backend
**GitHub (agent):** supercreativepeople/studioyou-fy-agent
**GCP Service Account:** claude-cloudrun-deployer@neat-tangent-474222-m9.iam.gserviceaccount.com
**LiveKit Cloud:** studioyou-futureyou-avatar-749nqz32.livekit.cloud
**Runway Developer Portal:** dev.runwayml.com — Characters tab holds SCP DUDE avatar, API keys, billing (prepay, $0.01/credit, $10 min purchase). Consumer app (runwayml.com) is a separate registry from the Developer Portal — confirm avatar_id visibility there if ever recreating.

**Local paths:**
- Frontend: /Users/supercreativepeople/Downloads/studioyou-app/
- Backend: /Users/supercreativepeople/Projects/studioyou-backend/main.py
- Agent: /Users/supercreativepeople/Projects/studioyou-fy-agent/
- Knowledge base: /Users/supercreativepeople/Projects/studioyou-backend/knowledge/

---

## Notion Reference

| Resource | ID |
|---|---|
| StudioYou Project Playbook | `34bb963047e581f99956e07953a9d1da` |
| Handoff Docs folder | `366b963047e5801795d0ec513406ac55` |
| Session AC Handoff | `393b963047e58186b307f381ae3d4282` |
| Session AB Handoff | `391b963047e581abb36fc93821363566` |
| Session AA Handoff | `391b963047e58141974dfa70adb93024` |
| Session Z Handoff | TBD — created at session close (not yet confirmed filled) |
| Session Y Handoff | `38bb963047e58102a2bee14efb76be8a` |
| Session X Handoff | `adea028d-5928-4616-b0f9-be47d3d96126` |
| Session W Handoff | `389b963047e581d18f23c185ab94e587` |
| Session U Handoff | `386b963047e58167b649f180c9d16cbb` |
| Session T Handoff | `385b963047e581cf84b0e772a3b5a26f` |
| Session S Handoff | `382b963047e581c5ab50df7ae2999e62` |
| Session Q Handoff | `37fb963047e581fa831be2b1fbfd8688` |
| Session P Handoff | `377b963047e58109a46ce45eb6da308f` |
| Session N Handoff | `376b963047e5813d82c6cd810eac43fd` |
| Session M Handoff | `375b963047e581b1a673fb6ebc41a2e3` |
| Session I Handoff | `36fb963047e58142a6f1e21565534739` |
| Data Room | `339b963047e5804d84ccc130c96d17e5` |
| SY Alpha Build Documents | `357b963047e5808db9c2d55dba5b1921` |

---

## formations table schema (confirmed Session V)
Real columns: `id, email, data, studio_name, creator_type, updated_at, first_name, last_name, magic_token, token_expires_at, formation_data, created_at, verified_at, deleted_at`
- `formation_data` — JSON string containing `{briefing: {arsenal, roadblock, creator_type}, answers: [...]}`
- `data` — JSON object containing `{tier, billing, subscribed_at}`
- `first_words` — does NOT exist as column
- `archetype` — does NOT exist as column. Derived from `creator_type` in briefing at runtime.

---

*Built with Claude. Powered by Claude. June 2026.*
