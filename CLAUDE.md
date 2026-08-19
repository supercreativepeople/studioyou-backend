# StudioYou — CLAUDE.md

> This file is the project bible. Same sections every session, same order. No agenda items, no carry-forwards — those live in the handoff doc. Read this to understand what StudioYou is and how to work on it. For strategy, positioning, and current build-status narrative (not code), see the **StudioYou Project HQ** in Notion — https://app.notion.com/p/3bfb963047e5814f9398d9f53aaf0c13 (rebuilt 2026-08-17, canonical strategic source of truth, distinct from this file's technical/deploy scope).

**Changelog (most recent 3-5, older entries live in git history):**
- **2026-08-19:** Security fixes 1-3 applied and deployed. (1) All three `/api/chat` callsites in studio.html now send `context/email/building_id/mode` instead of client-side system prompt — server builds prompt via `build_fy_system_prompt()` pulling creator data from Supabase. (2) `ADMIN_KEY` moved to `os.environ.get("SY_ADMIN_KEY")` — rotated, added to Cloud Run env vars. (3) `SY_DEBUG` env var gates all 6 debug endpoints (return 404 when false/unset). netlify-cli installed globally on Mac. `netlify.toml` added to studioyou-app repo. GitHub auto-deploy connected to `studioyou-app` (id `4a365723`) via Netlify UI — every push to `main` now deploys to `studioyou.app`. Wrong orphan site (`heroic-torrone-abeb92`) unlinked. Backend: `954007a`. Frontend: `2b8ad0b`, `6ab3ac5`.
- **2026-08-18:** Canonical per-building JSON schema built for all 12 buildings (`tools/build_schema.py` → `knowledge/schemas/<id>.json` + `_drift_report.json`) — see Locked Decisions. New research-driven Layer 3 authoring philosophy locked into `FY_LAYER2_SCHEMA.md` (4 additions this session: model-feedback addendum, skeleton-authoring rule, Layer 3 sourcing model + two-tier retrieval + generic sixth-track + v1 ceiling, and THE LOCK CALCULUS universal rule). IDEATE fully integrated (5 of 8 steps now carry a verified, sourced Layer 3 injection). DEVELOP batch 1 integrated (3 track-opening steps + all 5 lock steps reference the new Lock Calculus). 8 commits, all pushed. See `handoffs/2026-08-18-canonical-schema-and-layer3-research.md` for full detail.
- **2026-08-17:** No code changed this session (Notion/knowledge-base work only). Corrected two long-standing drift points: (1) subscription tier table below was wrong (missing Player tier, stale numbers) — corrected against live `subscribe.html` code; (2) studioyou.studio role fully resolved — confirmed via code grep as the Resend-verified magic-link auth email sending domain only, not a second product surface. Built new **StudioYou Project HQ** in Notion (7 pages) as the project's single source of truth for strategy and current state. Confirmed build status: IDEATE ~50% built, DEVELOP ~20% built, remaining 10 buildings unbuilt, FY orchestrator (Sprint S2) unbuilt and confirmed as top build priority.
- **2026-08-16:** Frontend workflow retired (Lee confirmed manual handoff no longer applies). Supabase pause resolved (was `INACTIVE`, restored by Lee, confirmed `ACTIVE_HEALTHY`). Google Drive documentation split into cloud Google Drive vs. physical G-DRIVE SSD. `lee@frisson.digital` confirmed reachable via Fastmail/Zapier connection.

---

## 1. What This Is

StudioYou (studioyou.app) is a creator studio OS powered by FutureYou (FY), an AI advisor built on Claude. It serves prosumer creators and independent filmmakers through a spatial studio metaphor ("The Lot") with 12 buildings (IDEATE, DEVELOP, FUND, CAST, PLAN, PRODUCE, POST, LEGAL, DISTRIBUTE, BRAND, MARKET, MONETIZE) — this 12-building layer is routing/journey plumbing, not the functional pipeline itself. FY is the platform's core engine — not a feature — positioned as the creator's "future self" advisor guiding them through a structured building → section → step methodology, enforcing the same disciplined creative-production pipeline professional physical production has used for decades (see Project HQ, page 01 and 05, for the full thesis). Currently in alpha development. Confirmed build status (2026-08-17): IDEATE ~50% built, DEVELOP ~20% built, the other 10 buildings unbuilt, and the FY orchestrator/step-state machine (Sprint S2) — the mechanism that makes FY actually follow the pipeline reliably — is unbuilt. That orchestrator is the top build priority. (2026-08-18 note: those percentages are Lee's own field-testing estimate and haven't been re-issued since — see Live State for what actually changed this session, which was content depth within IDEATE/DEVELOP, not orchestrator progress.)

**Legal entity:** Frisson Digital, Inc. (Delaware C-Corp). StudioYou and SCREENBot IP formally assigned to Frisson Digital. SuperCreativePeople (SCP) is kept entirely separate — not commingled with SY/SB projects. For all funding and partnership applications, Frisson Digital, Inc. is the entity of record. Lee operates as the individual bootstrapper, claiming projects personally, not DBA-ing SCP.

**StudioYou subscription tiers — corrected 2026-08-17, verified against live `subscribe.html` code:**

| Tier | Monthly | Annual/mo | Annual total |
|---|---|---|---|
| Operator | $129/mo | $99/mo | $1,188/yr |
| Independent | $199/mo | $149/mo | $1,788/yr |
| Player | $299/mo | $225/mo | $2,700/yr |

"Player" is the correct, live tier name — not "Studio." All-in subscription, single price per tier, modules unlock by journey necessity not price tier. Ecosystem pays (tool providers, brands, agencies); creator never pays a cut of earnings.

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

**Backend:** Flask on Google Cloud Run (`studioyou-api`, project `neat-tangent-474222-m9`, `us-east1`). Endpoint: `studioyou-api-198959034459.us-east1.run.app`. Deploy via GitHub Actions on push to main.

**Database:** Supabase (`rubwhfjwqonqhfbkhren`). RLS disabled.

**FY Agent:** LiveKit cloud agent. Runs off local disk via `lk agent create` — NOT deployed via GitHub Actions. Agent ID changes on every `lk agent delete && create`. See Live State for current ID.

---
**AI stack:**
- Tier 1 (surface): `claude-sonnet-4-6` via env var `FY_SURFACE_MODEL`
- Tier 2 (orchestration): `claude-fable-5` via env var `FY_ORCHESTRATION_MODEL`
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
| Netlify | Frontend hosting (two projects — see Tech Stack & Architecture) | Netlify dashboard |
| GCP Cloud Run | Backend hosting | GCP console (`neat-tangent-474222-m9`, `us-east1`, service `studioyou-api`). Do not touch billing account 019309-BEB782-398472 — Google for Startups application pending. `gcloud` CLI authenticated on Mac — use via Desktop Commander. |
| Google Drive | Document storage / shared assets | Google Drive MCP (pre-authenticated) |
| Fastmail | Email (`lee@supercreativepeople.com`, `lee@frisson.digital`, aliases) | Zapier MCP — call `inspect_zapier_actions` before any read/write |

---
## 5. How to Deploy

**Backend (main.py):**
Code edit → `git commit` on Mac via Desktop Commander → `git push` → GitHub Actions → Cloud Run auto-deploy. Claude owns this pipeline. Lee does not push.
- Use `--update-env-vars` (not `--set-env-vars`) for manual CLI env var updates.
- SY_ADMIN_KEY and SY_DEBUG are Cloud Run env vars — never hardcode, never echo in chat.

**FY Agent (agent.py, prompts.py):**
Code edit → `git commit && git push` (for record) → `lk agent delete [ID] && lk agent create` from Mac Terminal. Deploy runs off local disk. `lk agent update` does NOT force a Docker rebuild — only `delete && create` produces a fresh image. Update Live State with new agent ID immediately after recreate.

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
| Backend HEAD | commit `954007a` — security fixes 1-3 |
| FY Agent ID | **CA_Mnhkjj3mUr7T** (region us-east) |
| TTS Voice | Corey (`630ed21c-2c5c-41cf-9d82-10a7fd668370`), sonic-3, pronunciation dict wired |
| Surface model | claude-sonnet-4-6 |
| Orchestration model | claude-fable-5 |
| dashboard.html | Session AE deployed |
| studio.html | Security fixes deployed. GitHub auto-deploy now connected to `studioyou-app` (id `4a365723`). Current HEAD: `6ab3ac5` (netlify.toml). |
| Supabase | rubwhfjwqonqhfbkhren — `fy_vault_entries` table live |
| Build status (Lee's field-test estimate, 2026-08-17) | IDEATE ~50%, DEVELOP ~20%, PLAN/PRODUCE/POST/LEGAL/DISTRIBUTE/BRAND/MARKET/MONETIZE/FUND/CAST unbuilt. No new estimate issued since. |
| Content depth (2026-08-18) | Canonical schema exists for all 12 buildings (`knowledge/schemas/*.json`). IDEATE: 5 of 8 steps carry a verified, sourced Layer 3 injection (Steps 1,2,4,7,8; Step 3 shorter nuance; Steps 5,6 Lee's own material, untouched). DEVELOP: 3 track-opening steps (N-5, M-1, V-1) carry injections, all 5 lock steps reference new Lock Calculus; P-1 and B-1 researched, not yet cleared; most other DEVELOP steps not yet reviewed. |
| Sprint | S1 nominally active but stale target dates (Jul 6–12, past). Orchestrator (S2, unbuilt) is the presumed top build priority but not yet formally confirmed. |
| Pending bugs | `/api/formation/briefing` — `client.messages.create` should be `anthropic_client.messages.create`. FY stuck-dots after sidebar open during chat — not yet investigated. |

---
## 7. Locked Decisions

- **Runway and Reactor are independent credit pools.** Never infer one from the other. (P0 confirmed Session AG.)
- **`lk agent update` does not rebuild.** Only `delete && create` produces a fresh image. Agent ID changes every recreate.
- **`--update-env-vars`** for manual Cloud Run CLI updates, not `--set-env-vars`.
- **Frontend git workflow (confirmed 2026-08-19):** edit via Desktop Commander, `git commit`, `git push` → Netlify auto-deploys to `studioyou.app`. GitHub auto-deploy now connected. Fallback: `netlify deploy --prod --dir=.` from `~/Downloads/studioyou-app`. The manual drag-drop flow is retired.
- **studioyou-app Netlify site id is `4a365723-1d16-4fab-a88c-8d71851fe5c8` (studioyou.app).** The local folder `~/Downloads/studioyou-app` must be linked to this site, not `heroic-torrone-abeb92` (wrong site, corrected 2026-08-19). Verify with `netlify status` before deploying.
- **Claude owns the full deployment pipeline.** Lee does not push.
- **SY_ADMIN_KEY is a Cloud Run env var.** Never hardcode, never echo in chat or docs. Value was rotated 2026-08-19 (old value was compromised — visible in GitHub repo). Pointer only in all docs.
- **SY_DEBUG gates all debug/admin endpoints.** Not set in prod → endpoints return 404. Do not set SY_DEBUG=true in prod without explicit Lee direction.
- **Security fixes 1-3 applied (2026-08-19):** client-side system prompt removed from all `/api/chat` callsites, admin key in env var, debug endpoints gated. Fixes 4-6 (session token auth, vault ownership, Supabase RLS) not yet started.
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
| Yifeng Zhang | Alibaba Cloud AI | On-site AIEWF rep. AI infrastructure supply evaluation. |
