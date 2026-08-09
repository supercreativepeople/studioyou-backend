# SERVICES.md - StudioYou Backend

Every external platform/service this project depends on. Update at session close whenever something changes. Credentials are NEVER stored here, pointer only. Mirrored into the cross-project Notion Platform & Service Registry (`https://app.notion.com/p/dd60c5c5ccda496eb10d58f8db0bc8b6`) at session close per the `dev-session-protocol` skill; that Notion database is the cross-project view, this file is the source of truth for this repo specifically.

Rows marked "(shared)" are used across the StudioYou family, see `studioyou-fy-agent`'s and `studioyou-app`'s own `SERVICES.md` for their repo-specific rows.

## Corporate / billing structure (recorded 2026-08-09)

**Frisson Digital, Inc. is the parent company and owns both StudioYou and SCREENBot.** This supersedes the earlier plan, still described in this repo's `CLAUDE.md` business-track section, of forming a separate per-product newco (StudioYou Inc., Delaware C-corp) with SCP Inc. as venture studio. The holdco structure was chosen because a single parent owning both products aligns with incubator programs, Anthropic's programs, and fundraising/incubator fund opportunities that a scattered set of per-product entities does not.

**Every billing instance is to be established through Frisson Digital, Inc.**

The `Billing Entity` column below records which entity each account *actually* bills to today, which is not the same question as which entity it *should* bill to. Accounts created before the Frisson structure may still sit on a personal card or an SCP Inc. instrument. Those are marked `Unconfirmed` rather than assumed, and migrating them is tracked as an open item, not silently backfilled.

## Schema note (2026-08-09)

Four columns added this session: `Billing Entity`, `Account Standing`, `Cost / Balance`, and `Blocks Alpha`. Before this, the format had nowhere to record that an account was unpaid, exhausted, or not yet activated, so a service with a balance due read identically to one in good standing. That gap is why an unpaid LiveKit balance and exhausted Runway credits were both showing as plain "Active." The same four columns were added to the Notion registry so the sync stays row-for-row.

`Account Standing` values: `Paid / current`, `Balance due`, `Credits exhausted`, `Free tier`, `Not yet activated`, `Unconfirmed`.

## Services

| Service | Category | Purpose | Billing Entity | Account Standing | Cost / Balance | Blocks Alpha | Account / Org ID | Console URL | Subscription / Tier | Renewal | Credential Location | Status | Last Verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GitHub - studioyou-backend | Other | Source code, CLAUDE.md, handoffs/ | Free / no billing | Free tier | $0 | no | github.com/supercreativepeople | https://github.com/supercreativepeople/studioyou-backend | free | n/a | git credential helper (osxkeychain, remote URL de-tokenized 2026-08-07) | Active | 2026-08-07 |
| Cloud Run - studioyou-api | Hosting | Backend API (main.py) | Unconfirmed | Unconfirmed | usage-based | no | neat-tangent-474222-m9, us-east1 | console.cloud.google.com/run | pay-as-you-go | n/a | Cloud Run env vars, set via GitHub Actions from GitHub Secrets | Active | not independently re-verified |
| GitHub Actions (shared) | CI/CD | Push to main, build Docker, push GCR, deploy Cloud Run | Free / no billing | Free tier | $0 | no | supercreativepeople/studioyou-backend | github.com/supercreativepeople/studioyou-backend/actions | free | n/a | GitHub Secrets | Active | not independently re-verified |
| Anthropic API (shared) | AI/API | Claude, FY session logic and chat. `FY_ORCHESTRATION_MODEL` / `FY_SURFACE_MODEL` | Unconfirmed | Unconfirmed | $212.62 credit balance on Lee's console org as of 2026-08-09 | no | see note below | platform.claude.com | pay-as-you-go | n/a | ANTHROPIC_API_KEY in Cloud Run env | Active | 2026-08-09 |
| Fal.ai | AI/API | **Live video generation.** `video_generate` to `fal-ai/seedance-v1-lite`, `video_generate_pro` to `fal-ai/seedance-v1-pro`, `video_generate_kling` to `fal-ai/kling-video/v2/master` | Unconfirmed | Unconfirmed | usage-based, per generation | unknown | - | https://fal.ai | usage-based | n/a | FAL_API_KEY in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Reactor | AI/API | Backend exchanges the key for a short-lived Reactor JWT at `/api/reactor/token` | Unconfirmed | Unconfirmed | unconfirmed | unknown | - | https://api.reactor.inc | unconfirmed | n/a | REACTOR_API_KEY in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Adobe Express (embed SDK) | Design | Client ID served to the frontend at `/api/integrations/adobe/config` | Unconfirmed | Unconfirmed | unconfirmed | no | - | developer.adobe.com/express | unconfirmed | n/a | ADOBE_EXPRESS_CLIENT_ID in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Adobe PDF Services | AI/API | PDF generation/conversion via `pdf-services-ue1.adobe.io` | Unconfirmed | Unconfirmed | unconfirmed | no | - | developer.adobe.com/document-services | unconfirmed | n/a | ADOBE_PDF_CLIENT_ID / ADOBE_PDF_CLIENT_SECRET in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Frame.io | Storage/Database | OAuth via Adobe IMS, callback `https://studioyou.app/auth/frameio/callback`. Route `/api/integrations/frameio/auth` | Unconfirmed | Unconfirmed | unconfirmed | no | - | https://frame.io | unconfirmed | n/a | FRAMEIO_CLIENT_ID / FRAMEIO_CLIENT_SECRET in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Supabase (shared) | Storage/Database | `fy_vault_entries` table (creator answer capture) | Unconfirmed | Unconfirmed | unconfirmed | no | unconfirmed project ref | app.supabase.com | unconfirmed | n/a | SUPABASE_URL / SUPABASE_KEY in .env and Cloud Run env | Active | not independently re-verified |
| Resend (shared) | Email | Transactional email (`api.resend.com`). Primary owner is studioyou-site; backend also holds a key | Unconfirmed | Unconfirmed | unconfirmed | no | - | resend.com | unconfirmed | n/a | RESEND_API_KEY in Cloud Run env | Needs Verification | 2026-08-09 |
| LiveKit Cloud (shared) | Hosting | Backend mints room tokens for the FY agent. Runtime owner is studioyou-fy-agent | Unconfirmed | **Balance due** | **$50 outstanding, unpaid** | **YES** | studioyou-futureyou-avatar-749nqz32.livekit.cloud | cloud.livekit.io | unconfirmed tier | n/a | LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET | Active | 2026-08-09 |
| Netlify - studioyou.app (shared) | Distribution/Deploy | Frontend host (studioyou-app repo) | Unconfirmed | Unconfirmed | unconfirmed | no | app.netlify.com | app.netlify.com | unconfirmed tier | n/a | Netlify login | Active | not independently re-verified |
| Domain - studioyou.app | Domain/DNS | Primary product domain | Unconfirmed | Unconfirmed | unconfirmed | no | - | - | unconfirmed | **unknown** | registrar login | Needs Verification | 2026-08-09 (added) |
| Domain - studioyou.studio | Domain/DNS | Second domain referenced in backend CORS/allowed origins | Unconfirmed | Unconfirmed | unconfirmed | no | - | - | unconfirmed | **unknown** | registrar login | Needs Verification | 2026-08-09 (added) |
| Notion (shared) | Other | Session handoffs, sprint tracker, product docs, Platform & Service Registry | Unconfirmed | Unconfirmed | unconfirmed | no | app.notion.com | https://www.notion.so/a5ff3efa50c24545b07eb1a7c6763438 | workspace plan | n/a | Notion login | Active | not independently re-verified |
| Tavus | AI/API | **Deprecated.** Former avatar provider, superseded by Runway (Session AA) | Unconfirmed | Unconfirmed | unconfirmed | no | tavusapi.com | tavusapi.com | unconfirmed | n/a | TAVUS_API_KEY / TAVUS_LIVEKIT_PERSONA_ID in Cloud Run env | Deprecated | 2026-08-09 |
| Seedance (direct / enterprise) | AI/API | Prospective direct route, bypassing the Fal.ai reseller margin | Frisson Digital, Inc. (to be established) | Not yet activated | not established | no | - | - | not established | n/a | n/a | Sandbox | 2026-08-09 (added) |
| ByteDance | AI/API | Prospective partner account. Parent of Seedance | Frisson Digital, Inc. (to be established) | Not yet activated | not established | no | - | - | not established | n/a | n/a | Sandbox | 2026-08-09 (added) |
| Alibaba Cloud | AI/API | Prospective partner account (presumed Wan / Qwen family) | Frisson Digital, Inc. (to be established) | Not yet activated | not established | no | - | - | not established | n/a | n/a | Sandbox | 2026-08-09 (added) |

## What this audit found (2026-08-09)

The previous version of this file listed 8 services. A line-by-line audit of every API key and external host the running backend actually touches found **6 paid or credentialed services that were entirely absent from the tracker**: Fal.ai, Reactor, Adobe Express, Adobe PDF Services, Frame.io, and both domains. Fal.ai is the most consequential omission, it is the live video generation path for the product.

Two further corrections:

- **Seedance already ships.** `main.py` routes `video_generate` and `video_generate_pro` to `fal-ai/seedance-v1-lite` and `-pro` today, via Fal.ai as reseller. The partner-direct routing registry (`main.py` ~line 2224) carries a commented-out stub: `# "seedance_video": {"provider": "seedance", "endpoint": "TBD"}`, labelled "direct when enterprise terms apply." Activating a direct ByteDance/Seedance relationship is therefore a **margin decision on an already-live path**, not a new capability.
- **Tavus is not just unused env vars.** `main.py` (~lines 1223-1460) still contains live route handlers posting to `tavusapi.com/v2/replicas` and `/v2/conversations`. This is dead code in a running service pointed at a provider that is no longer part of the stack. Separately, `studioyou-app/dashboard.html:2234` still shows real users the string "Tavus Phoenix is aging your photo. ~2-5 min."

## Anthropic API credits note (2026-08-09)

Lee's console org shows **$212.62**, of which **$200 is the Claude Impact Lab hackathon perk** (Los Angeles, 2026-08-08; the event's published perks confirm "$200 in Anthropic API credits per attendee"). Two things are **not** verified and should not be planned around until they are:

1. **Expiry.** The event materials state no expiration date. The figure of Aug 15 came from recollection, not from the console. Check the Credits page in the console for the real date.
2. **Which org holds the key.** It is not confirmed that the `ANTHROPIC_API_KEY` in Cloud Run and in `studioyou-fy-agent/.env` belongs to the same org holding those credits. If it does not, alpha testing spends real money and the $200 sits untouched.

Note also that these are **API credits**, so they cannot pay for Claude Code / Cowork build sessions (those run on the Max subscription). The only StudioYou activity that draws them down is the product itself calling Claude.

## Open items

- [ ] **Billing entity audit.** Every existing account is marked `Unconfirmed` because it is not known which of them bill to Frisson Digital, Inc. versus a personal card or SCP Inc. instrument. Going through each console and confirming (then migrating where needed) is the single highest-value follow-up here.
- [ ] Confirm what Reactor does in the product and whether it is still needed.
- [ ] Confirm registrar, renewal date, and billing owner for both domains. A lapse takes the product down.
- [ ] Strip the dead Tavus code paths from `main.py`, and decide whether to close the Tavus account.
- [ ] Verify Fal.ai account standing. If its credits are also out, video generation is down and the tracker should say so.
- [ ] Re-verify every row still marked "not independently re-verified" against its live console.

Note (2026-08-07, still open): existing `CLAUDE.md` in this repo is long (~590 lines) and predates the protocol's "keep it under ~200 lines" guidance. Not restructured yet.
