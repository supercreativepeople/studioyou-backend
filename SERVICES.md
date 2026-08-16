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
| Reactor (world models) | AI/API | **Live world generation.** FutureYou selects an archetype during onboarding/briefing; a world model generates from it. Backend exchanges the key for a short-lived JWT at `/api/reactor/token` | Lee (personal) | Free tier (dev credits) | **688,987 credits available.** Burn rate uneconomic at production scale only | no | - | https://api.reactor.inc | dev credits, relationship cold | n/a | REACTOR_API_KEY in Cloud Run env | Needs Verification | 2026-08-09 |
| Adobe Express (embed SDK) | Design | Client ID served to the frontend at `/api/integrations/adobe/config` | Lee (personal) | Unconfirmed | unconfirmed | no | - | developer.adobe.com/express | unconfirmed | n/a | ADOBE_EXPRESS_CLIENT_ID in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Adobe PDF Services | AI/API | PDF generation/conversion via `pdf-services-ue1.adobe.io` | Lee (personal) | Unconfirmed | unconfirmed | no | - | developer.adobe.com/document-services | unconfirmed | n/a | ADOBE_PDF_CLIENT_ID / ADOBE_PDF_CLIENT_SECRET in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Frame.io | Storage/Database | OAuth via Adobe IMS, callback `https://studioyou.app/auth/frameio/callback`. Route `/api/integrations/frameio/auth` | Lee (personal) | Unconfirmed | unconfirmed | no | - | https://frame.io | unconfirmed | n/a | FRAMEIO_CLIENT_ID / FRAMEIO_CLIENT_SECRET in Cloud Run env | Needs Verification | 2026-08-09 (added) |
| Supabase (shared) | Storage/Database | `fy_vault_entries` table (creator answer capture) | Lee (personal) | **Credits exhausted / paused** | $0, project auto-paused | **YES** | project ref `rubwhfjwqonqhfbkhren`, org `yepuslepymluiqycrkfd` | app.supabase.com | unconfirmed (region us-east-2, Postgres 17) | n/a | SUPABASE_URL / SUPABASE_KEY in .env and Cloud Run env | **Needs Verification — see 2026-08-16 section below** | 2026-08-16 |
| Resend (shared) | Email | Transactional email (`api.resend.com`). Primary owner is studioyou-site; backend also holds a key | Lee (personal) | Unconfirmed | unconfirmed | no | - | resend.com | unconfirmed | n/a | RESEND_API_KEY in Cloud Run env | Needs Verification | 2026-08-09 |
| LiveKit Cloud (shared) | Hosting | Backend mints room tokens for the FY agent. Runtime owner is studioyou-fy-agent | Lee (personal) | Paid / current | **$50/mo recurring (Ship plan)** | no | studioyou-futureyou-avatar-749nqz32.livekit.cloud | cloud.livekit.io | unconfirmed tier | n/a | LIVEKIT_URL / LIVEKIT_API_KEY / LIVEKIT_API_SECRET | Active | 2026-08-09 |
| Netlify - studioyou.app (shared) | Distribution/Deploy | Frontend host (studioyou-app repo) | Lee (personal) | Unconfirmed | unconfirmed | no | app.netlify.com | app.netlify.com | unconfirmed tier | n/a | Netlify login | Active | not independently re-verified |
| Domain - studioyou.app | Domain/DNS | Primary product domain | Lee (personal) | Unconfirmed | unconfirmed | no | - | - | unconfirmed | **unknown** | registrar login | Needs Verification | 2026-08-09 (added) |
| Domain - studioyou.studio | Domain/DNS | **LIVE. Part of the livelink user sign-in engine.** Also in backend CORS/allowed origins | Lee (personal) | Unconfirmed | unconfirmed | **YES** | - | - | unconfirmed | **unknown** | registrar login | Active | 2026-08-09 |
| Notion (shared) | Other | Session handoffs, sprint tracker, product docs, Platform & Service Registry | Lee (personal) | Unconfirmed | unconfirmed | no | app.notion.com | https://www.notion.so/a5ff3efa50c24545b07eb1a7c6763438 | workspace plan | n/a | Notion login | Active | not independently re-verified |
| Google Drive | Other | Product documents, shared assets, project working files. Accessed in Cowork via Google Drive MCP. | Lee (personal) | Free tier | $0 | no | supercreativepeople@gmail.com | drive.google.com | personal/workspace | n/a | Google Drive MCP (pre-authenticated in Cowork) | Active | 2026-08-09 |
| Fastmail | Other | Email for `lee@supercreativepeople.com`, `lee@frisson.digital`, and aliases. Partnership and vendor comms. Accessed in Cowork via Zapier MCP. | Lee (personal) | Unconfirmed | unconfirmed | no | supercreativepeople@gmail.com | app.fastmail.com | unconfirmed | n/a | Zapier MCP — call `inspect_zapier_actions` before any read/write | Active | 2026-08-09 |
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
| LiveKit Cloud | FY agent runtime | SuperCreativePeople | Remove SCP name. **$50/mo subscription, current, not arrears.** Partnership track pending. |
| Runway | Avatar rendering | SuperCreativePeople | Remove SCP name. **Credits exhausted.** |
| Fal.ai | Live video generation | SuperCreativePeople | Remove SCP name. Verify standing. |
| Reactor (world models) | Live world generation | SuperCreativePeople | Remove SCP name. 688,987 credits, alpha not blocked. |
| Deepgram | FY speech-to-text | SuperCreativePeople | Remove SCP name. Verify standing. |
| Cartesia | FY text-to-speech | SuperCreativePeople | Remove SCP name. Verify standing. |
| Supabase | Vault data + magic-link auth | SuperCreativePeople | Remove SCP name. |
| Netlify (team) | Hosts all 12 sites, both products | **Team is NAMED SuperCreativePeople** | Not a field edit. Slug is in every admin URL. Handle deliberately. |
| Resend | Magic-link sign-in email | SuperCreativePeople | Remove SCP name. |
| GCP / Cloud Run | Backend runtime | SuperCreativePeople | **DO NOT TOUCH** until Google for Startups responds. |
| Domain studioyou.app | Primary product domain | Porkbun, SCP as company | Remove SCP name. Renews 2027-03-27, auto-renew on. |
| Domain studioyou.studio | **Live sign-in path** | Porkbun, SCP as company | Remove SCP name. Renews 2027-03-27, auto-renew on. |
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
- [ ] **Decide whether to restore the Supabase project** (currently INACTIVE/paused, confirmed 2026-08-16) before the next live FY session — see dated section below.
- [ ] **Resolve the frontend-workflow discrepancy** — CLAUDE.md's Locked Decision says never commit frontend changes via git, but `studioyou-app`/`studioyou-site` are live git repos being committed to directly (confirmed 2026-08-16). Get Lee's call on which is actually current practice, then update CLAUDE.md to match reality.

Note (2026-08-07, still open): existing `CLAUDE.md` in this repo is long (~590 lines) and predates the protocol's "keep it under ~200 lines" guidance. Not restructured yet.

## Verified against live APIs, 2026-08-09

### LiveKit: corrected twice, now verified from the billing console

This row was first recorded as an alpha blocker, then as a $50 balance due. Both were wrong. Verified against the live LiveKit billing console 2026-08-09:

**It is a $50/month recurring subscription on the Ship plan.** Next billing cycle Sept 1, 2026. Nothing is overdue and nothing is suspended. **Runway is the sole hard blocker** on the live IDEATE retest.

Project `p_3abx9tkixic` (StudioYou-FutureYou-Avatar). Ship plan includes 5,000 agent session minutes, 150,000 WebRTC participant minutes, and 250GB downstream, with overage at $0.12/GB.

| Period | Agent session min | Participant min | Downstream | Total |
|---|---|---|---|---|
| July 2026 | 2,645 of 5,000 | 5,865 of 150,000 | 8 GB of 250 | $50.00 |
| August 2026 to date | — | — | **0 GB** | $50.00 |

**Idle spend flag.** August usage is zero. The product has not run this month, which tracks with no feature work since Session AF (2026-07-07) and Runway being out of credits. That is $50/month buying capacity nobody is using while alpha is stalled.

Do **not** downgrade before the partnership conversation. LiveKit is first on Lee's AIEWF follow-up list and a partnership track could change the economics entirely. But if that conversation does not land and alpha stays stalled, this is a live candidate for a lower tier.

**This is also the first hard monthly operating cost confirmed for StudioYou**, and the starting point for the run-cost number the incubator and fund conversations will need.

### Domain inventory: Porkbun, 11 domains, verified 2026-08-09

Pulled from the live Porkbun account. **All 11 have auto-renew ON, registrar lock ON, and WHOIS privacy ON.**

| Domain | Expires | Days out | Note |
|---|---|---|---|
| frisson.music | 2027-03-05 | 207 | defensive, unused |
| frisson.photography | 2027-03-05 | 207 | defensive, unused |
| frisson.technology | 2027-03-05 | 207 | defensive, unused |
| frisson.band | 2027-03-05 | 207 | defensive, unused |
| **frisson.digital** | 2027-03-05 | 207 | **LIVE** — program-application website |
| **screenbot.app** | 2027-03-25 | 228 | **LIVE** |
| **studioyou.app** | 2027-03-27 | 229 | **LIVE**, tagged StudioYou |
| **studioyou.studio** | 2027-03-27 | 229 | **LIVE**, sign-in path, tagged StudioYou |
| supercreativepeople.com | 2027-06-13 | 307 | live on Netlify |
| leebrownstein.com | 2027-06-20 | 314 | personal |
| leebrownstein.me | 2027-06-20 | 314 | personal |

**Expiry risk retracted.** Earlier entries in this file called the unknown domain renewal dates the single largest operational exposure on the company-dependent list, on the assumption a lapse could silently break sign-in. Every domain auto-renews, is locked, and is more than 200 days out. That is not a live risk and the flag was wrong.

**The real item is ownership, not expiry.** `screenbot.app`, `studioyou.app`, and `studioyou.studio` are Frisson product IP registered in Lee's personal name. The five `frisson.*` domains are literally named for the company and also sit personally. All belong on the asset schedule.

**One efficiency:** the SCP company name is set at the Porkbun *account* level, so removing it there covers all 11 domains in a single edit rather than eleven.

**Minor cost note:** four `frisson.*` registrations (music, photography, technology, band) are defensive and unused. Small recurring cost with no current purpose. Worth a keep-or-drop decision when the run-cost number gets built.

### Netlify: one team, twelve sites, and a bigger naming problem

Pulled live from the Netlify API rather than taken from docs. A single team hosts everything across both products.

**Team:** slug `supercreativepeople`, id `6961b4975f419aae0d9ba3dc`, Pro plan, 1 member, created 2026-01-10.

| Project | Primary URL | Plan |
|---|---|---|
| studioyou | https://studioyou.studio | dev |
| studioyou-app | https://studioyou.app | dev |
| frisson-digital | https://frisson.digital | pro |
| screenbot | https://screenbot.app | dev |
| screenbot-beta | screenbot-beta.netlify.app | pro |
| screenbot-assets | screenbot-assets.netlify.app | pro |
| supercreativepeople | https://supercreativepeople.com | dev (forms enabled) |
| ground-ai-blueprint | ground-ai-blueprint.netlify.app | pro |
| universal-briefing | universal-briefing.netlify.app | pro |
| seedance-briefing | seedance-briefing.netlify.app | pro |
| thriving-conkies-31dad5 | default netlify.app | dev |
| profound-gaufre-d7e81d | default netlify.app | dev |

Three findings:

1. **The Netlify team is itself named "SuperCreativePeople."** This is an account-level name, not a company-name field, and the slug is embedded in every project admin URL. It is the largest single SCP surface found so far and it is **not** part of the quick field-edit pass. Renaming a team slug can break links and integrations, so handle it deliberately and separately.
2. **`frisson.digital` is live and deploying independently, on a Pro plan.** That confirms the program-application website claim rather than taking it on trust.
3. **Two orphan projects** (`thriving-conkies-31dad5`, `profound-gaufre-d7e81d`) carry default Netlify names, are deployed and ready, and appear in no documentation. Purpose unknown. Add them to the load-bearing walkthrough. `ground-ai-blueprint`, `universal-briefing`, and `seedance-briefing` are also live and undocumented here.

Also missing until now: `studioyou-site`'s `SERVICES.md` had no hosting row at all, despite Netlify project `studioyou` being what actually serves `studioyou.studio`.

## Console verification round 2, 2026-08-09

### The alpha blocker has a price: about $20

**Runway Dev** (`dev.runwayml.com`, org `4b2afb94-a345-4b8a-a2cd-7376a2a4d2dc`) is at **0 credits**. Payment history: Jun 23 2026 $24.00 bought 3,000 credits, Jul 5 2026 $20.00 bought 2,000 credits. That is roughly **$0.0088 per credit**, so a **~$20 top-up restores ~2,000 credits** and the avatar renders again. Total spent to date: $44 for 5,000 credits, all consumed.

**Root cause of the silent failure:** autobilling is disabled and no card is saved. The balance reached zero with no warning and stays there. Enabling autobilling with a threshold prevents a repeat.

### Runway is two platforms, and only one of them matters here

| | Runway Dev | Runway Platform |
|---|---|---|
| URL | dev.runwayml.com | app.runwayml.com |
| What it is | The API | The creative application |
| Balance | **0 credits** | 684 credits |
| Used by | `studioyou-fy-agent` via `RUNWAYML_API_SECRET` | Lee, directly |
| Asset class | Company-dependent | Personal tooling |

The 684 credits on Platform **do not unblock the avatar.** Anyone reading "Runway has credits" and concluding the product works would be wrong. This is a clean instance of the asset-class split: Platform is Lee's creative workstation, Dev is the company's product runtime.

### Fal.ai is fine, but it is the hardest SCP removal on the list

**$19.99 available, current, ~$20/month, "no recent usage."** Video generation is not blocked. Zero recent usage is consistent with no product activity since Session AF.

The naming problem is worse here than anywhere else. SuperCreative People appears as **display name, full name, and username** (`supercreativepeople`), on a personal account under `supercreativepeople@gmail.com`. The account page states that changing full name or email requires contacting support, and the username may not be changeable at all. **This one cannot be handled in the quick field-edit pass.** It likely needs a support ticket, and worst case a fresh account under Frisson.

### Three routes to Seedance now

fal.ai is promoting "Seedance 2.5 in fal Agent," and Runway ships Seedance 2.5 natively. So the options are fal (current), Runway, or a direct ByteDance relationship. Worth weighing all three before opening a direct partner conversation, since two of them require no new commercial relationship at all.

### Updated cost picture

First hard numbers for StudioYou's monthly operating cost: LiveKit $50/month (Ship plan, currently zero usage), fal.ai ~$20/month, Runway Dev pay-as-you-go at roughly $20 per 2,000 credits. Plus the Porkbun portfolio annually. Still missing: GCP, Supabase, Netlify, Resend, Deepgram, Cartesia.

## Creative platform portfolio, verified 2026-08-09

Seven retail generative platforms Lee holds for research and partnership development. All `Personal tooling` under the asset-class split, all on `supercreativepeople@gmail.com`. **They matter to StudioYou architecture for a reason that isn't obvious from the billing:** almost all of them ship MCP connectors, and several sell exactly the capabilities StudioYou currently buys expensively elsewhere.

| Platform | Plan / cost | Balance | MCP | Renews |
|---|---|---|---|---|
| Adobe Creative Cloud Pro | $69.99/mo | n/a | no | 2026-09-02 |
| Adobe Firefly 7,000 Credits | $29.99/mo | 9,725 / 11,000 | no | 2026-08-23 |
| Luma Labs (Plus) | $30/mo | **0 / 10,000 used** | yes | 2026-09-04 |
| Midjourney (Basic) | $10/mo | 3h20m / 3h20m unused | no | 2026-09-01 |
| OpenArt (Pro) | price TBC | 24,000 credits | **yes** | TBC |
| ImagineArt | price TBC | 30,891 credits | **yes** | TBC |
| Runway Platform | Upgrade prompt shown | 684 credits | no | TBC |
| FilmPro.ai | partner credits | available | **no API at all** | n/a |

**Confirmed floor: ~$140/month** across Adobe, Luma, and Midjourney alone. OpenArt, ImagineArt, and Runway Platform prices are not yet captured, so the real number is higher.

### Corrections

**Adobe is two subscriptions, not one.** Firefly credits are a standalone $29.99/mo plan, separate from the $69.99 Creative Cloud Pro. Both on the same Visa. Adobe total is **$99.98/month**, not the ~$70 originally recalled.

**Firefly's unlimited-generations promo expires.** Qualifying credit plans get unlimited generations on select models for one year from plan start, then revert to consuming credits. Worth pinning the start date so the reversion isn't a surprise.

### Why this is an architecture asset, not just spend

StudioYou has two unresolved model-routing questions: replacing Reactor/Helios for world generation, and whether to go direct to Seedance rather than through fal.ai. This portfolio speaks to both.

- **Seedance is now available four ways.** fal.ai (current production path), Runway 2.5, ImagineArt, and a hypothetical direct ByteDance relationship. Three of the four require no new commercial agreement. That materially weakens the case for opening a direct partner negotiation as a first move.
- **OpenArt ships explicit World and Character generation modes.** That is the same capability StudioYou buys from Reactor at a per-call cost Lee has assessed as unsustainable. Worth evaluating as a Reactor replacement before starting a partner search.
- **ImagineArt ships "Imagine Computer"** (agents, automation, skills, connectors), which is architecturally adjacent to StudioYou. Useful prior art.
- **The MCP connectors are a free integration test bed.** Luma, OpenArt, and ImagineArt all push MCP. StudioYou's agent will eventually need to drive external generation tools, and this is already-paid-for surface to prototype that routing and control logic against, before committing to any one provider.

**FilmPro is the exception:** partner credits but no MCP and no API, so integration needs an intermediary like Twin. Lowest-priority target despite the free credits, given six MCP-native alternatives.

### Idle capacity

Luma is at 0 of 10,000 consumed, Firefly 9,725 of 11,000, Midjourney's fast hours entirely untouched, OpenArt 24,000, ImagineArt 30,891. Most of this portfolio is paid for and unused. That is either a cost-reduction candidate or an argument to actually run the routing experiments above, but it should be a deliberate choice rather than a default.

### One hygiene item worth copying

Luma has an **additional-spend cap enabled at $10**. Runway Dev, by contrast, had no card and no autobilling, which is how it hit zero silently. A spend cap on the platforms that allow one is the same control applied from the other direction.

## Reactor corrected, 2026-08-09 (verified from the dashboard)

Earlier sections of this file implied Reactor was a depleted, near-dead relationship. **The account holds 688,987 credits.** Development and testing are not blocked, and this is not an alpha blocker.

**The reseller read is confirmed by their own product surface.** The Reactor dashboard features three world models: **"Real-Time World Model by Alibaba"** (Happy Oyster), **LINGBOT WORLD 2** (Next-Gen World Generation), and **X2** (Streaming Video Editing). Reactor aggregates other companies' world models rather than building its own, exactly as Lee revised his read to say.

**This collapses one of the prospective-partner rows.** "Alibaba" was recorded as a partner account to open for world generation. That capability is **already reachable today**, through an account with 688,987 credits, requiring no new commercial relationship. The Alibaba-direct conversation and the Reactor relationship are the same capability reached two ways. Reconsider before pursuing Alibaba direct.

**The cold relationship is not a viability signal.** Reactor announced a $59M raise "to power the World Model era." They are scaling, not folding. Private beta, with an API, docs, and a sample app on GitHub.

**The real problem is narrower than recorded.** Per-call token burn makes live world generation uneconomic **at production scale**. Credits are ample for alpha. So this is a unit-economics question for launch, not a blocker for the retest. The pre-rendered-archetype option remains the likely production answer, but it does not need deciding before alpha.

Combined with the creative-platform findings above, world generation is now reachable at least three ways: Reactor (688,987 credits, Alibaba and LINGBOT models), OpenArt (24,000 credits, explicit World and Character modes), and pre-rendered video per archetype. None requires a new partner agreement.

## Supabase confirmed INACTIVE (paused), 2026-08-16 — new alpha blocker

This row previously read "unconfirmed project ref, unconfirmed standing" — genuinely unknown, not verified either way. Checked directly via Supabase MCP this session (`list_projects` and `get_project`, not a single ambiguous call):

- **Project ref:** `rubwhfjwqonqhfbkhren`, name "StudioYou", org `yepuslepymluiqycrkfd`, region us-east-2, Postgres 17.6.1.104.
- **Status: `INACTIVE`.** This is Supabase's paused-project state, not a transient/cached reading — both calls agree. A paused project does not serve queries; the `fy_vault_entries` table (creator answer capture) is unreachable from the live backend right now, exactly like the Runway/LiveKit pattern found earlier this month: a real blocker sitting silently behind a status word nobody had checked.
- **Not yet done:** restoring it. `restore_project` is available via the Supabase MCP tool, but restoring is a decision with real consequences (may affect billing tier, and a paused-then-restored project sometimes needs a moment to fully come back) — flagged to Lee rather than actioned unilaterally.
- **Open item:** confirm with Lee whether this pause was expected (e.g. free-tier auto-pause from inactivity — the project has had no traffic since alpha stalled on the Runway/LiveKit blockers, so auto-pause on a free/low tier is the likely mechanism) and get a decision on restoring before the next live FY session, since any conversation that tries to write to the vault will fail silently otherwise.

## Frontend repos are git-tracked and being committed to directly — contradicts a Locked Decision in CLAUDE.md, needs Lee's call

CLAUDE.md's Locked Decisions list "Frontend file workflow: Lee provides → Claude modifies → Claude presents. Never fetch from GitHub" as standing policy. Checked directly this session: both `studioyou-app` (`~/Downloads/studioyou-app`) and `studioyou-site` (`~/Downloads/studioyou-site`) are real git repos with GitHub remotes (`github.com/supercreativepeople/studioyou-app`, `github.com/supercreativepeople/studioyou-site`), both clean and in sync with `origin/main`. `studioyou-app`'s most recent commit (2026-08-15, same day as this repo's Tavus cleanup) is titled "Remove dead Tavus-era avatar states from FYAvatarSlot" — a real code change, committed directly to git, not the manual present-and-Lee-deploys flow the locked decision describes.

Not resolved here — this needs Lee to say which is actually current practice: has the frontend workflow moved to direct git commits (in which case the Locked Decision is stale and should be rewritten to match, and Desktop Commander becomes the tool for frontend work same as backend/agent), or should that Aug 15 commit not have happened that way. Either answer is fine, but CLAUDE.md should say what's actually true rather than a policy nobody's following.
