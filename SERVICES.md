# SERVICES.md - StudioYou Backend

Every external platform/service this project depends on. Update at session close whenever something changes. Credentials are NEVER stored here, pointer only. Mirrored into the cross-project Notion Platform & Service Registry (`https://app.notion.com/p/dd60c5c5ccda496eb10d58f8db0bc8b6`) at session close per the `dev-session-protocol` skill; that Notion database is the cross-project view, this file is the source of truth for this repo specifically.

Rows marked "(shared)" are used across the StudioYou family, see `studioyou-fy-agent`'s and `studioyou-app`'s own `SERVICES.md` for their repo-specific rows.

## Corporate / billing structure (recorded 2026-08-09)

**Frisson Digital, Inc. is the parent company and owns both StudioYou and SCREENBot.** This supersedes the earlier plan, still described in this repo's `CLAUDE.md` business-track section, of forming a separate per-product newco (StudioYou Inc., Delaware C-corp) with SCP Inc. as venture studio. The holdco structure was chosen because a single parent owning both products aligns with incubator programs, Anthropic's programs, and fundraising/incubator fund opportunities that a scattered set of per-product entities does not.

**Every billing instance is to be established through Frisson Digital, Inc.**

### How to read the Billing Entity column (corrected 2026-08-09)

An earlier version of this section treated `Lee (personal)` as a defect on every row. That was too broad and has been corrected.

**Lee operates as an independent builder.** His personal accounts and cards fund his own activities and have never been commingled with SCP Inc. or any other company. His personal tooling account is exactly that: a personal account used for strategy, product, and material builds that feed whichever entity he is working with. SCP Inc. is a client like any other, with no structural, billing, or naming connection to it. Personal tooling on a personal card is correct and stays that way.

The real question is not commingling. It is **asset control**: which accounts does a Frisson-owned product *depend on to operate*, while being held in Lee's personal name. Those are marked `Company-dependent` in the `Asset Class` column. Everything else drops out of the finding.

- **`Company-dependent`** — StudioYou cannot run without it. Frisson owns the product; the account is personal. These need an answer.
- **`Personal tooling`** — Lee's own working accounts. Correct as-is, no action.
- **`Prospective`** — not yet opened. Open under Frisson Digital, Inc. from day one.
- **`Unclassified`** — pending the load-bearing walkthrough.

The IP assignment moved StudioYou and SCREENBot to Frisson. It did **not** move the accounts those products run on: domain registrations, platform accounts, API keys. That is a completeness gap in the assignment, not a hygiene failure, and the standard fix is an asset schedule with either transfer or license. Attorney and accountant question, not a dev task, and nothing here is legal or tax advice.

### The SuperCreativePeople naming problem (found 2026-08-09)

Every software and platform account was signed up via `supercreativepeople@gmail.com` **with the company name listed as "SuperCreativePeople."** Name only: no EIN, no entity linkage, all accounts tied to Lee personally.

This matters because SCP Inc. is a real corporation whose founding date sits outside the Anthropic four-year and Google five-year eligibility windows, and it was deliberately kept out of every program application. Meanwhile the vendor accounts running StudioYou's infrastructure name it as the operator. Reviewers and diligence read what is written, not the legal substance.

**Decision (2026-08-09): remove the SuperCreativePeople name from vendor accounts. Do not replace it with Frisson yet.** Blank or Lee's own name is the only value that matches reality today. Renaming to Frisson before Frisson has a bank account and payment instrument recreates the same mismatch pointed the other way, and that version is harder to explain. Move the name and the payment instrument together, at switchover.

**On the login email (decided 2026-08-09).** Every account also logs in under `supercreativepeople@gmail.com`, which is itself an SCP reference. Lee holds a neutral personal address, `nyclaabq@gmail.com`, and proposed switching globally. Agreed in principle, but split by asset class rather than done globally:

- **Personal tooling** → move to `nyclaabq@gmail.com`. One hop, correct final destination.
- **Company-dependent** → do **not** route through a second personal gmail. These are going to `lee@frisson.digital` at switchover; two migrations doubles the chance of breaking an API key or OAuth grant. Blank the company-name field now, move the login once, later.
- **Anything used as a contact address on a live application** → leave alone until that application resolves. Five are in review and Alibaba notifies on or around 2026-08-10.

Calibration: a personally-owned gmail address is a weaker signal than a field that reads "Company: SuperCreativePeople." The field edit is the high-value, low-risk move. The email migration is optional cleanup.

**Carve-out, time-sensitive:** do **not** touch GCP billing account `019309-BEB782-398472`. The Google for Startups Start tier application is pending against it, that program has domain-matching requirements across website, email, and billing account, and `lee@frisson.digital` was added as billing admin specifically for it. Leave it until Google responds, then handle it with everything else.

### Where things actually stand (confirmed by Lee 2026-08-09)

- **Every paid resource is personally funded by Lee on personal cards.** Not one platform account bills to a company instrument today. The `Billing Entity` column below reads `Lee (personal)` throughout because that is the fact, not because it is unverified.
- **SCP Inc. owns nothing.** It is a real corporation, but no IP has ever been formally assigned to it.
- **StudioYou and SCREENBot each have actual executed IP assignment documentation to Frisson Digital, Inc.** They are the two assigned products. Lee's other products remain his personally, unassigned.
- **StudioYou and SCREENBot are independent products** under a common parent. Frisson owning both is a corporate fact, not a shared-codebase or shared-runtime fact, and tooling should not assume otherwise.

**The gap this creates:** Frisson Digital, Inc. owns the StudioYou IP, while the infrastructure that IP runs on is bought on Lee's personal cards. For incubator, accelerator, and fund diligence, company-owned assets running on personally-funded infrastructure is the kind of thing that gets raised. Worth putting to counsel and an accountant, since the fix is likely some combination of a Frisson payment instrument, expense reimbursement, and a record of what was spent. This note is a flag, not legal or tax advice.

**Target state:** every billing instance established through Frisson Digital, Inc. Migrating each account is tracked as an open item below.

## Schema note (2026-08-09)

Four columns added this session: `Billing Entity`, `Account Standing`, `Cost / Balance`, and `Blocks Alpha`. Before this, the format had nowhere to record that an account was unpaid, exhausted, or not yet activated, so a service with a balance due read identically to one in good standing. That gap is why an unpaid LiveKit balance and exhausted Runway credits were both showing as plain "Active." The same four columns were added to the Notion registry so the sync stays row-for-row.

`Account Standing` values: `Paid / current`, `Balance due`, `Credits exhausted`, `Free tier`, `Not yet activated`, `Unconfirmed`.

## Services

| Service | Category | Purpose | Billing Entity | Account Standing | Cost / Balance | Blocks Alpha | Account / Org ID | Console URL | Subscription / Tier | Renewal | Credential Location | Status | Last Verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GitHub - studioyou-backend | Other | Source code, CLAUDE.md, handoffs/ | Free / no billing | Free tier | $0 | no | github.com/supercreativepeople | https://github.com/supercreativepeople/studioyou-backend | free | n/a | git credential helper (osxkeychain, remote URL de-tokenized 2026-08-07) | Active | 2026-08-07 |
| Cloud Run - studioyou-api | Hosting | Backend API (main.py) | Lee (personal) | Unconfirmed | usage-based | no | neat-tangent-474222-m9, us-east1 | console.cloud.google.com/run | pay-as-you-go | n/a | Cloud Run env vars, set via GitHub Actions from GitHub Secrets | Active | not independently re-verified |
| GitHub Actions (shared) | CI/CD | Push to main, build Docker, push GCR, deploy Cloud Run | Free / no billing | Free tier | $0 | no | supercreativepeople/studioyou-backend | github.com/supercreativepeople/studioyou-backend/actions | free | n/a | GitHub Secrets | Active | not independently re-verified |
| Anthropic API (shared) | AI/API | Claude, FY session logic and chat. `FY_ORCHESTRATION_MODEL` / `FY_SURFACE_MODEL` | Lee (personal) | Unconfirmed | $212.62 credit balance on Lee's console org as of 2026-08-09 | no | see note below | platform.claude.com | pay-as-you-go | n/a | ANTHROPIC_API_KEY in Cloud Run env | Active | 2026-08-09 |
| Fal.ai | AI/API | **Live video generation.** `video_generate` to `fal-ai/seedance-v1-lite`, `video_generate_pro` to `fal-ai/seedance-v1-pro`, `video_generate_kling` to `fal-ai/kling-video/v2/master` | Lee (personal) | Unconfirmed | usage-based, per generation | unknown | - | https://fal.ai | usage-based | n/a | FAL_API_KEY in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Reactor (Helios world model) | AI/API | **Live world generation.** FutureYou selects an archetype during onboarding/briefing; Helios generates the world from it. Backend exchanges the key for a short-lived JWT at `/api/reactor/token` | Lee (personal) | Free tier (dev credits) | **token burn rate unsustainable for live calls** | see note | - | https://api.reactor.inc | dev credits, relationship cold | n/a | REACTOR_API_KEY in Cloud Run env | Needs Verification | 2026-08-09 |
| Adobe Express (embed SDK) | Design | Client ID served to the frontend at `/api/integrations/adobe/config` | Lee (personal) | Unconfirmed | unconfirmed | no | - | developer.adobe.com/express | unconfirmed | n/a | ADOBE_EXPRESS_CLIENT_ID in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Adobe PDF Services | AI/API | PDF generation/conversion via `pdf-services-ue1.adobe.io` | Lee (personal) | Unconfirmed | unconfirmed | no | - | developer.adobe.com/document-services | unconfirmed | n/a | ADOBE_PDF_CLIENT_ID / ADOBE_PDF_CLIENT_SECRET in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Frame.io | Storage/Database | OAuth via Adobe IMS, callback `https://studioyou.app/auth/frameio/callback`. Route `/api/integrations/frameio/auth` | Lee (personal) | Unconfirmed | unconfirmed | no | - | https://frame.io | unconfirmed | n/a | FRAMEIO_CLIENT_ID / FRAMEIO_CLIENT_SECRET in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Supabase (shared) | Storage/Database | `fy_vault_entries` table (creator answer capture) | Lee (personal) | Unconfirmed | unconfirmed | no | unconfirmed project ref | app.supabase.com | unconfirmed | n/a | SUPABASE_URL / SUPABASE_KEY in .env and Cloud Run env | Active | not independently re-verified |
| Resend (shared) | Email | Transactional email (`api.resend.com`). Primary owner is studioyou-site; backend also holds a key | Lee (personal) | Unconfirmed | unconfirmed | no | - | resend.com | unconfirmed | n/a | RESEND_API_KEY in Cloud Run env | Needs Verification | 2026-08-09 |
| LiveKit Cloud (shared) | Hosting | Backend mints room tokens for the FY agent. Runtime owner is studioyou-fy-agent | Lee (personal) | **Balance due** | **$50 outstanding, unpaid** | **YES** | studioyou-futureyou-avatar-749nqz32.livekit.cloud | cloud.livekit.io | unconfirmed tier | n/a | LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET | Active | 2026-08-09 |
| Netlify - studioyou.app (shared) | Distribution/Deploy | Frontend host (studioyou-app repo) | Lee (personal) | Unconfirmed | unconfirmed | no | app.netlify.com | app.netlify.com | unconfirmed tier | n/a | Netlify login | Active | not independently re-verified |
| Domain - studioyou.app | Domain/DNS | Primary product domain | Lee (personal) | Unconfirmed | unconfirmed | no | - | - | unconfirmed | **unknown** | registrar login | Needs Verification | 2026-08-09 (added) |
| Domain - studioyou.studio | Domain/DNS | **LIVE. Part of the livelink user sign-in engine.** Also in backend CORS/allowed origins | Lee (personal) | Unconfirmed | unconfirmed | **YES** | - | - | unconfirmed | **unknown** | registrar login | Active | 2026-08-09 |
| Notion (shared) | Other | Session handoffs, sprint tracker, product docs, Platform & Service Registry | Lee (personal) | Unconfirmed | unconfirmed | no | app.notion.com | https://www.notion.so/a5ff3efa50c24545b07eb1a7c6763438 | workspace plan | n/a | Notion login | Active | not independently re-verified |
| Tavus | AI/API | **Deprecated.** Former avatar provider, superseded by Runway (Session AA) | Lee (personal) | Unconfirmed | unconfirmed | no | tavusapi.com | tavusapi.com | unconfirmed | n/a | TAVUS_API_KEY / TAVUS_LIVEKIT_PERSONA_ID in Cloud Run env | Deprecated | 2026-08-09 |
| Seedance (direct / enterprise) | AI/API | Prospective direct route, bypassing the Fal.ai reseller margin | Frisson Digital, Inc. (to be established) | Not yet activated | not established | no | - | - | not established | n/a | n/a | Sandbox | 2026-08-09 (added) |
| ByteDance | AI/API | Prospective partner account. Parent of Seedance | Frisson Digital, Inc. (to be established) | Not yet activated | not established | no | - | - | not established | n/a | n/a | Sandbox | 2026-08-09 (added) |
| Alibaba Cloud | AI/API | Prospective partner account (presumed Wan / Qwen family) | Frisson Digital, Inc. (to be established) | Not yet activated | not established | no | - | - | not established | n/a | n/a | Sandbox | 2026-08-09 (added) |

## What this audit found (2026-08-09)

The previous version of this file listed 8 services. A line-by-line audit of every API key and external host the running backend actually touches found **6 paid or credentialed services that were entirely absent from the tracker**: Fal.ai, Reactor, Adobe Express, Adobe PDF Services, Frame.io, and both domains. Fal.ai is the most consequential omission, it is the live video generation path for the product.

Two further corrections:

- **Seedance already ships.** `main.py` routes `video_generate` and `video_generate_pro` to `fal-ai/seedance-v1-lite` and `-pro` today, via Fal.ai as reseller. The partner-direct routing registry (`main.py` ~line 2224) carries a commented-out stub: `# "seedance_video": {"provider": "seedance", "endpoint": "TBD"}`, labelled "direct when enterprise terms apply." Activating a direct ByteDance/Seedance relationship is therefore a **margin decision on an already-live path**, not a new capability.
- **Tavus is not just unused env vars.** `main.py` (~lines 1223-1460) still contains live route handlers posting to `tavusapi.com/v2/replicas` and `/v2/conversations`. This is dead code in a running service pointed at a provider that is no longer part of the stack. Separately, `studioyou-app/dashboard.html:2234` still shows real users the string "Tavus Phoenix is aging your photo. ~2-5 min."

## Reactor / Helios: live world generation is an open architecture question (2026-08-09)

Context from Lee. Reactor is a worldbuilding model company he explored a dev relationship with; **the relationship went cold**. They still supply dev credits for StudioYou, but there is no forward path with them.

In the product, Helios powers **live world generation**: FutureYou selects an archetype during user onboarding/briefing, and the world is generated from that selection. This is a real feature, not an experiment.

Two problems:

1. **Cost.** Reactor's usage/billing token model consumes tokens at an alarming rate. Lee's assessment is that it is **not practical to sustain as a live call** in a shipping product.
2. **Who they actually are.** Lee's revised read is that Reactor is likely a **retail reseller of other companies' world models**, not the model builder he originally understood them to be. Worth confirming before any further investment of time.

Two candidate paths, both Lee's:

- **Pre-render a video per archetype** instead of generating live. Removes the per-session cost entirely and was already being explored.
- **Find a more realistic world-model resource**, including direct relationships: NVIDIA, Alibaba, ByteDance. This is the same conversation as the Seedance-direct row, so a single partner negotiation could plausibly cover both video generation and world generation.

This belongs in the alpha scope decision, not just the tracker. If live world generation cannot be afforded, alpha needs to ship the pre-rendered path.

## Anthropic API credits note (2026-08-09)

Lee's console org shows **$212.62**, of which **$200 is the Claude Impact Lab hackathon perk** (Los Angeles, 2026-08-08; the event's published perks confirm "$200 in Anthropic API credits per attendee"). Two things are **not** verified and should not be planned around until they are:

1. **Expiry.** The event materials state no expiration date. The figure of Aug 15 came from recollection, not from the console. Check the Credits page in the console for the real date.
2. **Which org holds the key.** It is not confirmed that the `ANTHROPIC_API_KEY` in Cloud Run and in `studioyou-fy-agent/.env` belongs to the same org holding those credits. If it does not, alpha testing spends real money and the $200 sits untouched.

Note also that these are **API credits**, so they cannot pay for Claude Code / Cowork build sessions (those run on the Max subscription). The only StudioYou activity that draws them down is the product itself calling Claude.

## Company-dependent assets: the actual finding (2026-08-09)

These are the accounts a Frisson-owned product cannot operate without, currently held in Lee's personal name. This is the list that needs an answer. Everything else in the table above is either Lee's own tooling (correct as-is) or not yet opened.

| Asset | Why it's company-dependent | Named company on account | Action |
|---|---|---|---|
| LiveKit Cloud | FY agent runtime | SuperCreativePeople | Remove SCP name. **$50 due.** |
| Runway | Avatar rendering | SuperCreativePeople | Remove SCP name. **Credits exhausted.** |
| Fal.ai | Live video generation | SuperCreativePeople | Remove SCP name. Verify standing. |
| Reactor / Helios | Live world generation | SuperCreativePeople | Remove SCP name, or retire the service entirely. |
| Deepgram | FY speech-to-text | SuperCreativePeople | Remove SCP name. Verify standing. |
| Cartesia | FY text-to-speech | SuperCreativePeople | Remove SCP name. Verify standing. |
| Supabase | Vault data + magic-link auth | SuperCreativePeople | Remove SCP name. |
| Netlify | Frontend host | SuperCreativePeople | Remove SCP name. |
| Resend | Magic-link sign-in email | SuperCreativePeople | Remove SCP name. |
| GCP / Cloud Run | Backend runtime | SuperCreativePeople | **DO NOT TOUCH** until Google for Startups responds. |
| Domain studioyou.app | Primary product domain | unknown | Identify registrar first. |
| Domain studioyou.studio | **Live sign-in path** | unknown | Identify registrar first. Highest exposure on this list. |
| Anthropic API key | Product runtime calls Claude | n/a | Rotate to the Frisson Console org. |

Adobe Express, Adobe PDF Services, and Frame.io are deliberately **not** on this list. They may belong here or may be abandoned experiments; the load-bearing walkthrough decides.

## Open items

- [ ] **Strip the "SuperCreativePeople" company name from every vendor account** except GCP. Cheap, low risk, and removes a false association with the one entity deliberately excluded from every program application.
- [ ] **Identify the registrar and renewal date for both domains.** `studioyou.studio` is in the live sign-in path with an unknown holder and unknown expiry. That is the single largest operational exposure on the list.
- [ ] **Rotate the production Anthropic key to the Frisson Console org** (UUID `5fbbfc0c-01c1-4466-926c-81041be7a0a8`, `lee@frisson.digital`), which is the applicant of record for Claude for Startups. Product runtime is the entity's cost, and any granted credits land in that org. Lee's personal Console org stays personal, correctly, and keeps the hackathon credit.
- [ ] **Load-bearing walkthrough.** Lee to go service by service and mark each as load-bearing versus an experiment never removed. Adobe Express, Adobe PDF Services, and Frame.io are least clear from the code. Until then, "Unclassified" means genuinely unknown, not merely unchecked.
- [ ] **Asset schedule for the company-dependent list.** The IP assignment moved the products to Frisson; it did not move the accounts they run on. Standard fix is a schedule with transfer or license. Attorney question.
- [ ] **Expense treatment for prior spend.** Reimbursement, shareholder loan, or capital contribution. Accountant question. Cheap to paper as you go, expensive to reconstruct later.
- [ ] **Decide the world-generation path** (pre-rendered archetype videos vs. a new model partner). See the Reactor section above. This is an alpha scope decision.
- [ ] Confirm registrar, renewal date, and billing owner for both domains. `studioyou.studio` is in the sign-in path, so a lapse breaks login, not just a redirect.
- [ ] Strip the dead Tavus code paths from `main.py`, and decide whether to close the Tavus account.
- [ ] Verify Fal.ai account standing. If its credits are also out, video generation is down and the tracker should say so.
- [ ] Re-verify every row still marked "not independently re-verified" against its live console.

Note (2026-08-07, still open): existing `CLAUDE.md` in this repo is long (~590 lines) and predates the protocol's "keep it under ~200 lines" guidance. Not restructured yet.
