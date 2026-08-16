# StudioYou — CLAUDE.md

> This file is the project bible. Same sections every session, same order. No agenda items, no carry-forwards — those live in the handoff doc. Read this to understand what StudioYou is and how to work on it.

**Changelog (most recent 3-5, older entries live in git history):**
- **2026-08-16:** Frontend workflow retired (Lee confirmed manual handoff no longer applies — see Locked Decisions and How to Deploy). Supabase pause resolved (was `INACTIVE`, restored by Lee, confirmed `ACTIVE_HEALTHY`). Netlify confirmed as full read/write interface, no CLI needed. Google Drive documentation split into cloud Google Drive vs. physical G-DRIVE SSD. `lee@frisson.digital` confirmed reachable via the existing Fastmail/Zapier connection (alias on the same account, no new connection needed) — see `dev-session-protocol` skill.
- **2026-08-15:** Runway topped up (fy-agent), Tavus dead code stripped from `main.py` (commit `5172736`).
- **2026-08-09:** Full 8-section CLAUDE.md rebuild (session AH). GCP/Cloud Run, Google Drive, Fastmail documented. Partnership tracker integrated.

---

## 1. What This Is

StudioYou (studioyou.app) is a creator studio OS powered by FutureYou (FY), an AI advisor built on Claude. It serves prosumer creators and independent filmmakers through a spatial studio metaphor ("The Lot") with 12 buildings (IDEATE, DEVELOP, FUND, CAST, PLAN, PRODUCE, POST, LEGAL, DISTRIBUTE, BRAND, MARKET, MONETIZE). FY is the platform's core engine — not a feature — positioned as the creator's "future self" advisor guiding them through a structured building → section → step methodology. Currently in alpha development under sprint S1.

**Legal entity:** Frisson Digital, Inc. (Delaware C-Corp). StudioYou and SCREENBot IP formally assigned to Frisson Digital. SuperCreativePeople (SCP) is kept entirely separate — not commingled with SY/SB projects. For all funding and partnership applications, Frisson Digital, Inc. is the entity of record. Lee operates as the individual bootstrapper, claiming projects personally, not DBA-ing SCP.

**StudioYou subscription tiers:**

| Tier | Monthly | Annual/mo | Annual total | Savings |
|---|---|---|---|---|
| Independent | $199/mo | $149/mo | $1,788/yr | 25% |
| Studio / Heavy Gen-AI | $299/mo | TBD | TBD | — |
| Operator (BYOK) | $129/mo | $99/mo | $1,188/yr | 23% |
| Enterprise | White-label | TBD | TBD | — |

---

## 2. Repos & Access

| Repo | Local Mac Path | GitHub | Purpose |
|---|---|---|---|
| studioyou-backend | /Users/supercreativepeople/Projects/studioyou-backend | github.com/supercreativepeople/studioyou-backend | Flask backend, CLAUDE.md, SERVICES.md, handoffs/, knowledge/ |
| studioyou-fy-agent | /Users/supercreativepeople/Projects/studioyou-fy-agent | github.com/supercreativepeople/studioyou-fy-agent | LiveKit agent service |
| studioyou-app | ~/Downloads/studioyou-app | github.com/supercreativepeople/studioyou-app | Frontend client (dashboard.html, studio.html). Confirmed 2026-08-16: real git repo, clean, in sync — see Locked Decisions, frontend now goes through git like every other repo. |
| studioyou-site | ~/Downloads/studioyou-site | github.com/supercreativepeople/studioyou-site | Marketing site. Confirmed 2026-08-16: real git repo, clean, in sync. |

All repos are private. Credentials via macOS Keychain (`osxkeychain`). Push via Desktop Commander is reliable (corrected 2026-08-16 — a prior finding that push "fails inconsistently from sandboxed sessions" was actually a wrong-tool bug, not a real limitation; see dev-session-protocol skill's "Push works" section).

**File access priority:** filesystem MCP → Desktop Commander → git clone (last resort, may fail auth)

---

## 3. Tech Stack & Architecture

**Frontend:** Netlify (`studioyou-app` project, serves studioyou.app) and a second Netlify project (`studioyou`, serves studioyou.studio — the live sign-in path, see SERVICES.md). Deploy via GitHub Actions on push to main, same as backend (corrected 2026-08-16 — retired the old manual-file-handoff workflow, see Locked Decisions). Files: dashboard.html, studio.html, index.html, subscribe.html.

**Backend:** Flask on Google Cloud Run (`studioyou-api`, project `neat-tangent-474222-m9`, `us-east1`). Endpoint: `studioyou-api-198959034459.us-east1.run.app`. Deploy via GitHub Actions on push to main.

**Database:** Supabase (`rubwhfjwqonqhfbkhren`). RLS disabled.

**FY Agent:** LiveKit cloud agent. Runs off local disk via `lk agent create` — NOT deployed via GitHub Actions. Agent ID changes on every `lk agent delete && create`. See Live State for current ID.

**AI stack:**
- Tier 1 (surface): `claude-sonnet-4-6` via env var `FY_SURFACE_MODEL`
- Tier 2 (orchestration): `claude-fable-5` via env var `FY_ORCHESTRATION_MODEL`
- STT: Deepgram nova-2
- TTS: Cartesia sonic-3
- Avatar: Runway Characters

**Knowledge base:** `studioyou-backend/knowledge/` — static spec files read by the agent at runtime via raw GitHub URL. They do NOT auto-deploy to Cloud Run.

---

## 4. Services

Full registry: `SERVICES.md` in this repo + Notion Platform & Service Registry (`collection://5bee6001-b8a8-44dd-ba05-192cee0492c2`).

Key dependencies (pointers only — credentials never in this file):

| Service | Purpose | Credential Location |
|---|---|---|
| Supabase | Database | Cloud Run env vars |
| Resend | Email | Cloud Run env vars |
| Cloudflare | DNS/CDN/Zero Trust | Cloudflare dashboard |
| LiveKit | Voice rooms | Agent `.env` + Cloud Run env vars |
| Cartesia | TTS | Agent `.env` |
| Deepgram | STT | Agent `.env` |
| Runway | Avatar | Agent `.env` (`RUNWAYML_API_SECRET`, `RUNWAY_AVATAR_ID`) |
| Anthropic | Claude API | Cloud Run env vars |
| Fal.ai | Image/video generation | Cloud Run env vars |
| Adobe Express / PDF Services / Frame.io | Creative tools | Cloud Run env vars |
| Netlify | Frontend hosting | Netlify dashboard |
| GCP Cloud Run | Backend hosting | GCP console (`neat-tangent-474222-m9`, `us-east1`, service `studioyou-api`). Do not touch billing account 019309-BEB782-398472 — Google for Startups application pending. `gcloud` CLI authenticated on Mac — use via Desktop Commander. |
| Google Drive | Document storage / shared assets | Google Drive MCP (pre-authenticated) |
| Fastmail | Email (`lee@supercreativepeople.com`, `lee@frisson.digital`, aliases) | Zapier MCP — call `inspect_zapier_actions` before any read/write |

---

## 5. How to Deploy

**Backend (main.py):**
Code edit → `git commit` on Mac → `git push` → GitHub Actions → Cloud Run auto-deploy. Claude owns this pipeline. Lee does not push.
- Use `--update-env-vars` (not `--set-env-vars`) for manual CLI env var updates.

**FY Agent (agent.py, prompts.py):**
Code edit → `git commit && git push` (for record) → `lk agent delete [ID] && lk agent create` from Mac Terminal. Deploy runs off local disk. `lk agent update` does NOT force a Docker rebuild — only `delete && create` produces a fresh image. Update Live State with new agent ID immediately after recreate.

**Frontend (dashboard.html, studio.html, etc.) — corrected 2026-08-16:**
Code edit via Desktop Commander → `git commit` → `git push` → Netlify auto-deploys from `studioyou-app`/`studioyou-site` repos, same pipeline as backend. The old manual "Lee provides → Claude modifies → Claude presents → Lee drag-and-drops into Netlify" flow is retired — see Locked Decisions.

**Knowledge base (knowledge/*.md):**
Edit file → `git commit && git push` to studioyou-backend. Files are read at agent runtime via raw GitHub URL. No Cloud Run redeploy needed.

---

## 6. Live State

| Component | Current Value |
|---|---|
| Backend HEAD | commit `bd6b306` — Phase 10.26 |
| FY Agent ID | **CA_Mnhkjj3mUr7T** (region us-east) |
| TTS Voice | Corey (`630ed21c-2c5c-41cf-9d82-10a7fd668370`), sonic-3, pronunciation dict wired |
| Surface model | claude-sonnet-4-6 |
| Orchestration model | claude-fable-5 |
| dashboard.html | Session AE deployed |
| studio.html | Session AE deployed |
| Supabase | rubwhfjwqonqhfbkhren — `fy_vault_entries` table live |
| Sprint | S1 — Canvas/Vault/Details (target Jul 6–12, past date — confirm alpha timeline with Lee) |

---

## 7. Locked Decisions

- **Runway and Reactor are independent credit pools.** Never infer one from the other. (P0 confirmed Session AG.)
- **`lk agent update` does not rebuild.** Only `delete && create` produces a fresh image. Agent ID changes every recreate.
- **`--update-env-vars`** for manual Cloud Run CLI updates, not `--set-env-vars`.
- **Frontend file workflow (corrected 2026-08-16):** the manual "Lee provides → Claude modifies → Claude presents" flow is retired. It predates the dev-session-protocol and had a real problem: files only ever lived on Lee's local Mac with no running record of session activity once delivered. `studioyou-app` and `studioyou-site` are live git repos (confirmed 2026-08-16, both clean and in sync with origin/main) — frontend work now goes through the same git workflow as backend/agent: edit via Desktop Commander, commit, push. Never present-and-wait-for-manual-deploy as the default path.
- **Claude owns the full deployment pipeline.** Lee does not push.
- **GCP billing account 019309-BEB782-398472:** do not touch while Google for Startups application is pending.
- **Anthropic program applications** filed under Frisson Digital, Inc. Credits non-transferable between Console orgs.
- **Tavus is deprecated.** Replaced by Runway Characters. `main.py.tavus` is a backup file in `.gitignore`, not deployed.
- **Account rule:** All Notion, Zapier, and connected tool builds go through `supercreativepeople@gmail.com` ONLY. `hiliimag.com` is retired — never use it for new integrations.
- **Anthropic CPN:** Agreement accepted under Frisson Digital, Inc. (Apr 2026). CCAF Learning Path open — 10-person requirement, Sep 7 deadline. Exception request strategy in partnership tracker.
- **ImagineArt obligation:** 2 posts per month (X + LinkedIn) using ImagineArt-generated assets, due by the 8th to trigger credit refills. Claude should flag if approaching the 8th with no confirmation.

---

## 8. Key Contacts

| Person | Role | Relevance |
|---|---|---|
| Alberto | Reactor CEO | FY avatar/video partner ($59M funded) |
| Ahmed | Reactor GTM | Commercial lead. Rescheduled Jul 2 pre-talk — no follow-up since. |
| Ben Relles | Make Believe | Partner |
| Adolfo | FilmPro | Partner |
| Alex | FilmPro | Technical contact — missed late June call, reschedule pending |
| Khachatur | FinalBit | Has alpha access. Need: pre-release API docs + enterprise rate structure |
| Arlin | Orkes/AgentSpan | Demo offered Jul 7 — unreplied. Orchestration layer evaluation. |
| Michèle | Seedance | Partnership brief complete. Need: ModelArc console invite + API keys |
| Stanly | Airbyte | AIEWF contact. Data/action layer evaluation. |
| Carson | LiveKit | AIEWF contact. Shared voice agent demos/docs. Unreplied. |
| Ruiyan | OpenArt | Partnership door opened Jun 29. Meeting never scheduled. |
| Apple Hao | Alibaba BD (Singapore) | AIEWF connection — introduced Yifeng |
| Yifeng Zhang | Alibaba Cloud AI | On-site AIEWF rep. AI infrastructure supply evaluation. |
