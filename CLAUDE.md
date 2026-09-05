# StudioYou — CLAUDE.md

> This file is the project bible. Same sections every session, same order. No agenda items, no carry-forwards — those live in the handoff doc. Read this to understand what StudioYou is and how to work on it. For strategy, positioning, and current build-status narrative (not code), see the **StudioYou Project HQ** in Notion — https://app.notion.com/p/3bfb963047e5814f9398d9f53aaf0c13 (rebuilt 2026-08-17, canonical strategic source of truth, distinct from this file's technical/deploy scope).

**Changelog (most recent 3-5, older entries live in git history):**
- **2026-09-05:** CLAUDE.md corrections only — no code changes. (1) Live State updated: HEAD now `d4e2f19`, Cloud Run revision now `00460-jdg`. (2) Subscription tier pricing corrected against Revenue & Pricing Model v2 (authoritative): Independent is $199/mo monthly / $129/mo annual + $149 onboarding; Operator is $149/mo monthly / $99/mo annual; Founding tier added (first 500, annual only); "Player" tier removed (never existed in the revenue model). Prior CLAUDE.md had wrong prices and a phantom tier.
- **2026-09-04 (session 4):** Runway credit drain fixed via `test_mode`. Eager avatar start was spending credits on every job before any user interaction (Runway bills 2 credits up front + 2 per 6s of ACTIVE session). `test_mode` in `formation_context` skips `start_avatar()` and falls through to Cartesia audio only. Dual activation: backend `TEST_EMAILS` auto-detect plus explicit frontend flag. `nyclaabq@gmail.com` is the confirmed E2E test account; manual avatar disabling is retired. Agent docstring drift corrected (claimed a sonic-3.5/Jameson switch that was never made; Corey on sonic-3 confirmed and kept). Custom FutureYou avatar groundwork shipped: `public.creator_avatars` table, per-creator avatar resolution in the agent, backend injection, and `future_you_brief.py`. **Two CLAUDE.md errors corrected this session: RLS was documented as disabled when it is enabled and forced, and the `lk agent delete && create` requirement is obsolete.** Backend HEAD: `c96422f`. Agent: `CA_Mnhkjj3mUr7T` version `Fqxg6JLvSBb8`.
- **2026-09-04 (session 3):** Two bug fixes committed and auto-deployed. (1) `formation_initialize()` fix (`ac24113`): added `creator_type` and `formation_data` (jsonb with briefing/answers) to Supabase patch — `build_fy_system_prompt()` was always getting empty values because these fields were never written. (2) S2 orchestrator three-bug fix (`2a8ccde`): primary bug was `FY_ORCHESTRATION_MODEL=claude-fable-5` is an invalid Anthropic API model name — `evaluate_success_state()` was silently throwing on every call and always returning `satisfied: False`, so steps never advanced. Fixed with model fallback to `SURFACE_MODEL` + robust JSON parsing (regex fallback). Secondary fix: seed condition now fires for both `"untouched"` and `"active"` building states. `FY_ORCHESTRATION_MODEL` env var updated to `claude-haiku-4-5-20251001` (revision 00434-lpn). Backend HEAD: `2a8ccde`.
- **2026-09-04 (session 2):** Cloud Build GitHub trigger created (`studioyou-backend-main`, us-east1, push to main → cloudbuild.yaml → Cloud Run auto-deploy). Manual `gcloud builds submit` retired — Claude pushes, Cloud Build handles the rest. STEP_MAP completed for all 12 buildings (10 new entries, 34 total steps). Backend HEAD: `6f22873`.
- **2026-09-04:** Tool wiring sprint — LTX Studio (ltx-2-5-pro) + Alibaba DashScope (Qwen LLM + WAN 3.0) integration code written and deployed. 7 new endpoints: `/api/tools/ltx/text-to-video`, `/api/tools/ltx/image-to-video`, `/api/tools/ltx/job-status`, `/api/tools/qwen/chat`, `/api/tools/wan/text-to-video`, `/api/tools/wan/task-status`. All session-gated; return 503 when key absent — activate automatically when env vars added to Cloud Run. formation_briefing `anthropic_client.messages.create` bug confirmed already fixed (prior handoff was stale). Backend HEAD: `c8cc2d1`.
- **2026-08-19:** Security fixes 1-3 applied and deployed. (1) All three `/api/chat` callsites in studio.html now send `context/email/building_id/mode` instead of client-side system prompt — server builds prompt via `build_fy_system_prompt()` pulling creator data from Supabase. (2) `ADMIN_KEY` moved to `os.environ.get("SY_ADMIN_KEY")` — rotated, added to Cloud Run env vars. (3) `SY_DEBUG` env var gates all 6 debug endpoints (return 404 when false/unset). netlify-cli installed globally on Mac. `netlify.toml` added to studioyou-app repo. GitHub auto-deploy connected to `studioyou-app` (id `4a365723`) via Netlify UI — every push to `main` now deploys to `studioyou.app`. Wrong orphan site (`heroic-torrone-abeb92`) unlinked. Backend: `954007a`. Frontend: `2b8ad0b`, `6ab3ac5`.

---

## 1. What This Is

StudioYou (studioyou.app) is a creator studio OS powered by FutureYou (FY), an AI advisor built on Claude. It serves prosumer creators and independent filmmakers through a spatial studio metaphor ("The Lot") with 12 buildings (IDEATE, DEVELOP, FUND, CAST, PLAN, PRODUCE, POST, LEGAL, DISTRIBUTE, BRAND, MARKET, MONETIZE) — this 12-building layer is routing/journey plumbing, not the functional pipeline itself. FY is the platform's core engine — not a feature — positioned as the creator's "future self" advisor guiding them through a structured building → section → step methodology, enforcing the same disciplined creative-production pipeline professional physical production has used for decades (see Project HQ, page 01 and 05, for the full thesis). Currently in alpha development. Confirmed build status (2026-08-17): IDEATE ~50% built, DEVELOP ~20% built, the other 10 buildings unbuilt, and the FY orchestrator/step-state machine (Sprint S2) — the mechanism that makes FY actually follow the pipeline reliably — is unbuilt. That orchestrator is the top build priority. (2026-08-18 note: those percentages are Lee's own field-testing estimate and haven't been re-issued since — see Live State for what actually changed this session, which was content depth within IDEATE/DEVELOP, not orchestrator progress.)

**Legal entity:** Frisson Digital, Inc. (Delaware C-Corp). StudioYou and SCREENBot IP formally assigned to Frisson Digital. SuperCreativePeople (SCP) is kept entirely separate — not commingled with SY/SB projects. For all funding and partnership applications, Frisson Digital, Inc. is the entity of record. Lee operates as the individual bootstrapper, claiming projects personally, not DBA-ing SCP.

**StudioYou subscription tiers — corrected 2026-09-05 against Revenue & Pricing Model v2 (authoritative). CLAUDE.md had stale prices and a "Player" tier that does not exist.**

| Tier | Monthly | Quarterly/mo | Annual/mo | Annual total | Notes |
|---|---|---|---|---|---|
| Independent | $199/mo | $159/mo | $129/mo | $1,548/yr | + $149 one-time onboarding fee |
| Operator | $149/mo | $119/mo | $99/mo | $1,188/yr | No onboarding fee |
| Founding | — | — | $149/mo (Ind) / $99/mo (Op) | — | First 500 creators, annual only |
| Scholarship | $0 | — | — | — | Phase 2, 25/yr |

All-in subscription, single price per tier, modules unlock by journey necessity not price tier. Ecosystem pays (tool providers, brands, agencies); creator never pays a cut of earnings. No "Player" tier exists — that name was stale from a prior naming iteration.

---
## 2. Repos & Access

| Repo | Local Mac Path | GitHub | Purpose |
|---|---|---|---|
| studioyou-backend | /Users/supercreativepeople/Projects/studioyou-backend | github.com/supercreativepeople/studioyou-backend | Flask backend, CLAUDE.md, SERVICES.md, handoffs/, knowledge/ |
| studioyou-fy-agent | /Users/supercreativepeople/Projects/studioyou-fy-agent | github.com/supercreativepeople/studioyou-fy-agent | LiveKit agent service |
| studioyou-app | ~/Downloads/studioyou-app | github.com/supercreativepeople/studioyou-app | Frontend client (dashboard.html, studio.html). Real git repo, clean, in sync. |
| studioyou-site | ~/Downloads/studioyou-site | github.com/supercreativepeople/studioyou-site | Marketing site. Real git repo, clean, in sync. |

All repos are private. Credentials via macOS Keychain (`osxkeychain`). Push via Desktop Commander is reliable. Never use device_bash for git — no network access in that sandbox.

**File access priority:** Desktop Commander (git/CLI/network) → filesystem MCP (plain reads) → never device_bash for anything requiring network

---

## 3. Tech Stack & Architecture

**Frontend:** Netlify — two projects:
- `studioyou-app` (site id `4a365723-1d16-4fab-a88c-8d71851fe5c8`, serves `studioyou.app`) — the real product. **Deploy method (confirmed 2026-08-19):** GitHub auto-deploy. Push to `main` on `studioyou-app` repo → Netlify deploys to `studioyou.app` automatically. GitHub connection established 2026-08-19 via Netlify UI (Lee linked repo through Netlify project settings). netlify-cli installed globally on Mac as fallback: `cd ~/Downloads/studioyou-app && netlify deploy --prod --dir=.`. Site id `4a365723` confirmed; was previously incorrectly linked to `heroic-torrone-abeb92` (orphan, no domain). Note: `thriving-conkies-31dad5` is a pre-existing orphan Netlify site also connected to this repo — it has no custom domain and can be deleted or repurposed as a staging preview.
- `studioyou` (site id `9a3000fb-dbf1-4922-b72c-20600a4e2bf4`, serves `studioyou.studio`) — NOT a second product surface. Resend-verified magic-link auth email sending domain only (`from: studio@studioyou.studio`). Also in CORS allow-list.

Cloudflare is the front door to `studioyou.app` — alpha, invited reviewers only, not publicly live.

Files: dashboard.html, studio.html, index.html, subscribe.html.

**Backend:** Flask on Google Cloud Run (`studioyou-api`, project `neat-tangent-474222-m9`, `us-east1`). Endpoint: `studioyou-api-198959034459.us-east1.run.app`. Deploy via Cloud Build trigger (`studioyou-backend-main`, us-east1). Push to `main` → Cloud Build → Cloud Run auto-deploy.

**Database:** Supabase (`rubwhfjwqonqhfbkhren`). **RLS ENABLED and FORCED** on all public tables (security fix 6, 2026-08-26; re-confirmed live 2026-09-04). Default deny for anon; service role unaffected. Any doc or memory claiming RLS is disabled is stale.

**FY Agent:** LiveKit cloud agent. Deployed with `lk agent deploy` from the repo root, NOT via GitHub Actions. `lk agent deploy` rebuilds the image and **preserves the agent ID**, issuing a new version string each deploy (verified twice on 2026-09-04). The old `delete && create` procedure is retired. See Live State for current ID and version.

---
**AI stack:**
- Tier 1 (surface): `claude-sonnet-4-6` via env var `FY_SURFACE_MODEL`
- Tier 2 (orchestration): `claude-haiku-4-5-20251001` via env var `FY_ORCHESTRATION_MODEL` (updated 2026-09-04 — was `claude-fable-5`, an invalid model name). `evaluate_success_state()` still has sonnet fallback as safety net.
- STT: Deepgram nova-2
- TTS: Cartesia sonic-3
- Avatar: Runway Characters

**Knowledge base:** `studioyou-backend/knowledge/` — static spec files read by the agent at runtime via raw GitHub URL. They do NOT auto-deploy to Cloud Run. As of 2026-08-18 this also includes a canonical per-building JSON schema layer (`knowledge/schemas/<building_id>.json`) generated from the `.md` specs — see Locked Decisions for what's canonical.

---

## 4. Services

Full registry: `SERVICES.md` in this repo + Notion Platform & Service Registry (`collection://5bee6001-b8a8-44dd-ba05-192cee0492c2`).

Key dependencies (pointers only — credentials never in this file):

| Service | Purpose | Credential Location |
|---|---|---|
| Supabase | Database | Cloud Run env vars |
| Resend | Email (incl. magic-link auth, sent from studioyou.studio domain) | Cloud Run env vars |
| Cloudflare | DNS/CDN/Zero Trust (front door to studioyou.app — alpha only) | Cloudflare dashboard |
| LiveKit | Voice rooms | Agent `.env` + Cloud Run env vars |
| Cartesia | TTS | Agent `.env` |
| Deepgram | STT | Agent `.env` |
| Runway | Avatar | Agent `.env` (`RUNWAYML_API_SECRET`, `RUNWAY_AVATAR_ID`) |
| Anthropic | Claude API | Cloud Run env vars |
| Fal.ai | Image/video generation | Cloud Run env vars |
| Adobe Express / PDF Services / Frame.io | Creative tools | Cloud Run env vars |
| LTX Studio | Text-to-video + image-to-video (ltx-2-5-pro). 7 endpoints wired 2026-09-04. | Cloud Run env var `LTX_API_KEY` — **ACTIVE** as of 2026-09-04, revision 00425-t2b. |
| Alibaba DashScope | Qwen LLM + WAN 3.0 video gen. Endpoints wired 2026-09-04. | Cloud Run env var `DASHSCOPE_API_KEY` — enterprise verification pending at myaccount.console.alibabacloud.com; key from modelstudio.console.alibabacloud.com/ap-southeast-1 when approved. Endpoints return 503 until key present. |
| Netlify | Frontend hosting (two projects — see Tech Stack & Architecture) | Netlify dashboard |
| GCP Cloud Run | Backend hosting | GCP console (`neat-tangent-474222-m9`, `us-east1`, service `studioyou-api`). Do not touch billing account 019309-BEB782-398472 — Google for Startups application pending. `gcloud` CLI authenticated on Mac — use via Desktop Commander. |
| Google Drive | Document storage / shared assets | Google Drive MCP (pre-authenticated) |
| Fastmail | Email (`lee@supercreativepeople.com`, `lee@frisson.digital`, aliases) | Zapier MCP — call `inspect_zapier_actions` before any read/write |

---
## 5. How to Deploy

**Backend (main.py):**
Code edit → `git commit` on Mac via Desktop Commander → `git push origin main` → Cloud Build trigger fires → Cloud Run auto-deploy. Claude owns this pipeline. Lee does not push. No manual `gcloud builds submit` needed.
- Use `--update-env-vars` (not `--set-env-vars`) for manual CLI env var updates.
- SY_ADMIN_KEY and SY_DEBUG are Cloud Run env vars — never hardcode, never echo in chat.

**FY Agent (agent.py, prompts.py):**
Code edit → `git commit && git push` (for record) → `lk agent deploy` from the repo root. Deploy runs off local disk and takes a few minutes (Docker build); run it detached and poll rather than blocking on a 60s tool timeout. The agent ID is preserved across deploys; only the version string changes. Confirm with `lk agent list`. Update the version in Live State after deploying.

**Frontend (dashboard.html, studio.html, etc.):**
Code edit via Desktop Commander → `git commit` → `git push` → Netlify auto-deploys to `studioyou.app`. GitHub auto-deploy confirmed connected (2026-08-19). Fallback CLI deploy:
```bash
cd ~/Downloads/studioyou-app
netlify deploy --prod --dir=.
```
Netlify CLI is installed globally on Mac. Local folder linked to site `4a365723-1d16-4fab-a88c-8d71851fe5c8`.

**Knowledge base (knowledge/*.md, knowledge/schemas/*.json):**
Edit file → `git commit && git push` to studioyou-backend. Files are read at agent runtime via raw GitHub URL. No Cloud Run redeploy needed.

---

## 6. Live State

| Component | Current Value |
|---|---|
| Backend HEAD | commit `d4e2f19` — chore: session open protocol only (SESSION_LOG.md) |
| Cloud Run revision | 00460-jdg (deployed 2026-09-05T03:43:25Z) |
| FY Agent ID | **CA_Mnhkjj3mUr7T** (region us-east), version `Fqxg6JLvSBb8`, deployed 2026-09-04T17:43:21Z. ID is stable across deploys. |
| TTS Voice | Corey (`630ed21c-2c5c-41cf-9d82-10a7fd668370`), sonic-3, pronunciation dict wired. Confirmed against code 2026-09-04; a docstring claiming sonic-3.5/Jameson was drift and has been removed. |
| Surface model | claude-sonnet-4-6 |
| Orchestration model | claude-haiku-4-5-20251001 (updated 2026-09-04 — was claude-fable-5, invalid) |
| dashboard.html | Session AE deployed |
| studio.html | Current HEAD: `97e290c` — session token header (syHeaders) on all API calls. GitHub auto-deploy → studioyou.app. |
| Supabase | rubwhfjwqonqhfbkhren — `fy_vault_entries` live; `creator_avatars` added 2026-09-04 (custom FutureYou avatars, empty, RLS enabled) |
| Build status (Lee's field-test estimate, 2026-08-17) | IDEATE ~50%, DEVELOP ~20%, PLAN/PRODUCE/POST/LEGAL/DISTRIBUTE/BRAND/MARKET/MONETIZE/FUND/CAST unbuilt. No new estimate issued since. |
| Content depth (2026-08-18) | Canonical schema exists for all 12 buildings (`knowledge/schemas/*.json`). IDEATE: 5 of 8 steps carry a verified, sourced Layer 3 injection. DEVELOP: 3 track-opening steps + all 5 lock steps reference new Lock Calculus. |
| Sprint | S2 orchestrator fully unblocked (2026-09-04 session 3). formation_initialize() writes creator_type + formation_data. evaluate_success_state() uses haiku for step eval with sonnet fallback. Next: S2 end-to-end test. |
| Pending activations | DASHSCOPE_API_KEY: pending Alibaba enterprise verification. LTX_API_KEY: ACTIVE (revision 00425-t2b). |
| Test mode | `nyclaabq@gmail.com` is the E2E test account. Sessions for it skip the Runway avatar entirely (zero credit spend) via `test_mode` in `formation_context`. Manual avatar disabling is retired. |
| Custom avatars | Groundwork shipped, pipeline unbuilt. `creator_avatars` table + agent resolution + backend injection + `future_you_brief.py` are live. Upload/generate/provision endpoints and frontend are not. |
| Runway credits (Dev) | **3,000 as of 2026-09-04 (live-verified via API).** Topped up $30.00 after silently hitting 0 earlier the same day. **Autobilling now ENABLED** (recharges below 500, Visa saved), closing the silent-zero risk open since July. Live avatar work unblocked. |
| Pending bugs | None critical. |


---
## 7. Locked Decisions

- **Runway and Reactor are independent credit pools.** Never infer one from the other. (P0 confirmed Session AG.)
- **Runway is TWO separate accounts with separate wallets (re-confirmed the hard way 2026-09-04).** Runway **Dev** (`dev.runwayml.com`, org `4b2afb94-a345-4b8a-a2cd-7376a2a4d2dc`, org name SuperCreativePeople) is the product runtime: `RUNWAYML_API_SECRET` in the agent `.env` authenticates here and this is the balance the avatar actually spends. Runway **Platform** (`runway.com`, "SuperCreative, Personal / Free") is Lee's creative workstation with its own separate balance. A healthy Platform balance does NOT unblock the avatar, and the two were briefly conflated on 2026-09-04 when Platform showed 684 credits while Dev was at 0. **Always verify Dev via `GET https://api.dev.runwayml.com/v1/organization`, never by reading the Platform UI.**
- **Runway bills on ACTIVE avatar-session time, not per utterance (2 credits up front + 2 per 6s).** Muting playback client-side does nothing. The only way to stop the charge mid-session is to close the AvatarSession. Never start an avatar speculatively.
- **`test_mode` skips the Runway avatar entirely.** Set via `formation_context["test_mode"]`, activated by `TEST_EMAILS` in main.py or an explicit `{"test_mode": true}` POST body. Falls through to Cartesia audio only, so conversation is fully testable at zero Runway cost. `TEST_EMAILS` must never contain a production creator's address.
- **Runway avatar `personality` and `startScript` are INERT in this architecture (confirmed 2026-09-04).** Per LiveKit's Runway docs, "LiveKit TTS settings will supersede selected voices and personalities configured for the Runway character." Cartesia generates the speech; Runway only renders lip-synced video. Claude's system prompt (`prompts.py`) is the actual brain. Editing The DUDE's personality in the Runway dashboard changes nothing. A Runway-cloned voice would likewise be ignored, which is why custom-avatar voice cloning routes to Cartesia.
- **Custom FutureYou avatars are per-creator via `formation_context["runway_avatar_id"]`**, falling back to the shared default ("The DUDE", `d44bf1d0-c297-4e26-839a-93099a485ca5`). Backend reads the creator's active `ready` row in `public.creator_avatars`. Runway avatar creation is programmatic (`POST /v1/avatars`: name, referenceImage, personality, voice) with **no training step** (returns `READY` immediately), and `referenceImage` is fetched server-side from a URL, so a public Supabase Storage URL suffices.
- **Portrait generation uses Runway Gen-4 Image with References, chosen on technical merit.** The binding constraint is identity preservation from a reference photo, a specific capability that does not correlate with general image quality. Same-stack also means the portrait's output matches what Runway's avatar renderer expects, since that portrait IS the avatar's input.
- **Bundle freely across independent tools; consolidate hard within a chain.** Wherever one feature's output is the next feature's input, seams cost quality. StudioYou's economics are best-of-breed assembly, which is right for discrete tools and wrong inside a chain. Avatar generation is one such chain; script → voice → video is another.
- **Partnership value stays strictly downstream of the technical call.** Tool selection is precisely where the "constitutionally incapable of competing interests with the creator" claim gets tested. If deal flow ever influences which tool is recommended, that principle becomes marketing. Runway's partnership upside is a side benefit of decisions made on merit, never the reason for them.
- **The FutureYou brief must never idealize a creator physically.** Aspiration lives in context and evidence (the room, the work visible around them, their bearing), never appearance. Physical characteristics are left entirely to the reference image. Image models idealize by default, and a feature that quietly tells a creator they should look different inverts the platform's purpose. These constraints live in the prompt in `future_you_brief.py`, not in review.
- **`lk agent deploy` is the deploy command (corrected 2026-09-04).** It rebuilds the image and preserves the agent ID, issuing a new version string. Verified twice on 2026-09-04 (16:36Z and 17:43:21Z), agent ID `CA_Mnhkjj3mUr7T` unchanged across both. The prior guidance that only `delete && create` rebuilds, and that the agent ID changes every deploy, is obsolete: do not delete the agent to ship a change.
- **`--update-env-vars`** for manual Cloud Run CLI updates, not `--set-env-vars`.
- **Frontend git workflow (confirmed 2026-08-19):** edit via Desktop Commander, `git commit`, `git push` → Netlify auto-deploys to `studioyou.app`. GitHub auto-deploy now connected. Fallback: `netlify deploy --prod --dir=.` from `~/Downloads/studioyou-app`. The manual drag-drop flow is retired.
- **studioyou-app Netlify site id is `4a365723-1d16-4fab-a88c-8d71851fe5c8` (studioyou.app).** The local folder `~/Downloads/studioyou-app` must be linked to this site, not `heroic-torrone-abeb92` (wrong site, corrected 2026-08-19). Verify with `netlify status` before deploying.
- **Claude owns the full deployment pipeline.** Lee does not push.
- **SY_ADMIN_KEY is a Cloud Run env var.** Never hardcode, never echo in chat or docs. Value was rotated 2026-08-19 (old value was compromised — visible in GitHub repo). Pointer only in all docs.
- **SY_DEBUG gates all debug/admin endpoints.** Not set in prod → endpoints return 404. Do not set SY_DEBUG=true in prod without explicit Lee direction.
- **Security fixes 1-6 ALL complete:** 1-3 (2026-08-19): system prompt server-side, SY_ADMIN_KEY env var, SY_DEBUG gate. 4-5 (2026-08-26): validate_session() gates all project/vault/chat endpoints, syHeaders() on all frontend fetches, sy_session_token localStorage. 6 (2026-08-26): RLS ENABLED + FORCED on formations, fy_projects, fy_sessions, fy_session_plans, fy_session_actions, fy_vault_entries — default deny for anon, service role unaffected.
- **GCP billing account 019309-BEB782-398472:** do not touch while Google for Startups application is pending.
- **Anthropic program applications** filed under Frisson Digital, Inc. Credits non-transferable between Console orgs.
- **Tavus is deprecated.** Replaced by Runway Characters. `main.py.tavus` is a backup file in `.gitignore`, not deployed.
- **Account rule:** All Notion, Zapier, and connected tool builds go through `supercreativepeople@gmail.com` ONLY. `hiliimag.com` is retired — never use it for new integrations.
- **Anthropic CPN:** Agreement accepted under Frisson Digital, Inc. (Apr 2026). CCAF Learning Path open — 10-person requirement, Sep 7 deadline. Exception request strategy in partnership tracker.
- **ImagineArt obligation:** 2 posts per month (X + LinkedIn) using ImagineArt-generated assets, due by the 8th to trigger credit refills. Claude should flag if approaching the 8th with no confirmation.
- **studioyou.studio is infrastructure, not a decision point (resolved 2026-08-17):** it is the Resend-verified magic-link auth email sending domain only. Do not re-litigate this — see Tech Stack & Architecture.
- **Business Plan v4 is partially stale:** its 61-tool-stack framing, 2-tier Universal/Pro pricing, and 14-stage (IDEATE...ADMIN) architecture are all superseded by the shipped 3-tier/12-building structure above. Not yet formally archived/rewritten — open item, tracked in Project HQ Decision Log (Notion).
- **Strategic source of truth split:** this file (CLAUDE.md) stays scoped to technical/deploy state. Positioning, competitive thesis, build-status narrative, and product-portfolio strategy (CLIPClear, OMNIShield, YouScored) live in the StudioYou Project HQ (Notion, see top of this file) — don't duplicate that content here, link to it.
- **Canonical building content schema (2026-08-18):** `knowledge/schemas/<building_id>.json`, generated/regenerated via `tools/build_schema.py`, is the emerging canonical source of truth for per-building step structure (creator_prompt, fy_rationale, fy_approach, canvas_output, raw_spec, etc.), superseding the `.md` specs and frontend `BUILDING_TASKS` as those two drift. `_drift_report.json` in the same folder tracks where they still disagree. `knowledge/FY_LAYER2_SCHEMA.md` is the authoritative source for all building-authoring rules and architecture decisions — don't duplicate that content here, link to it.
- **LTX + DashScope endpoints (2026-09-04):** All 7 new tool endpoints return 503 (not 500) when their env var key is absent. This is intentional — allows deploy-first, key-add-later workflow. Activate LTX by adding `LTX_API_KEY` to Cloud Run env vars. Activate DashScope by adding `DASHSCOPE_API_KEY`. Use `--update-env-vars` only.
- **S2 orchestrator model fallback (2026-09-04):** `evaluate_success_state()` tries `ORCHESTRATION_MODEL` first, falls back to `SURFACE_MODEL` on any API exception. `FY_ORCHESTRATION_MODEL` is `claude-haiku-4-5-20251001` (valid, active). Fallback to sonnet remains in code as a safety net.

---
## 8. Key Contacts

| Person | Role | Relevance |
|---|---|---|
| Alberto | Reactor CEO | FY avatar/video partner ($59M funded) |
| Ahmed | Reactor GTM | Commercial lead. Rescheduled Jul 2 pre-talk — no follow-up since. |
| Ben Relles | Make Believe | Partner |
| Adolfo | FilmPro | Partner |
| Alex | FilmPro | Technical contact — missed late June call, reschedule pending |
| Khachatur | FinalBit | Has alpha access. Flagged system prompt visible in Network tab (fix applied 2026-08-19). Need: pre-release API docs + enterprise rate structure |
| Arlin | Orkes/AgentSpan | Demo offered Jul 7 — unreplied. Orchestration layer evaluation. |
| Michèle | Seedance | Partnership brief complete. Need: ModelArc console invite + API keys |
| Stanly | Airbyte | AIEWF contact. Data/action layer evaluation. |
| Carson | LiveKit | AIEWF contact. Shared voice agent demos/docs. Unreplied. |
| Ruiyan | OpenArt | Partnership door opened Jun 29. Meeting never scheduled. |
| Apple Hao | Alibaba BD (Singapore) | AIEWF connection — introduced Yifeng |
| Yifeng Zhang | Alibaba Cloud AI | On-site AIEWF rep. AI infrastructure supply evaluation. Alibaba account now open (Frisson Digital). |
