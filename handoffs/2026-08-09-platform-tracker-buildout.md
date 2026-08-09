# Session: platform / partner / subscription tracker build-out — 2026-08-09

## What happened

Session opened as "continue the alpha build," and turned into the hygiene work instead once it became clear alpha is blocked on unpaid accounts rather than on code.

### Corporate structure corrected

`CLAUDE.md`'s business track documented a plan that did not happen: SCP Inc. as venture studio, StudioYou Inc. (Delaware C-corp) formed before the Anthology application. Per Lee:

- **Frisson Digital, Inc. was formed as a parent company owning both StudioYou and SCREENBot**, instead of per-product newcos. Rationale: a single parent aligns with incubator programs, Anthropic's programs, and fundraising/incubator fund opportunities.
- **StudioYou and SCREENBot each have executed IP assignment documentation to Frisson.** They are the two assigned products.
- **SCP Inc. owns nothing.** Real corporation, no IP ever assigned to it.
- **All of Lee's other products remain his personally**, unassigned.
- **StudioYou and SCREENBot are independent products** under a common parent. Corporate fact, not a shared-codebase fact.
- **Every paid resource is personally funded by Lee on personal cards.** Target state is every billing instance through Frisson.

The old plan is retained in `CLAUDE.md` marked SUPERSEDED rather than deleted, with a new open item: the IP-assignment step in the superseded plan no longer exists, so that question needs re-answering against the Frisson structure.

### Tracker schema extended

Added four columns to both `SERVICES.md` (all four repos) and the Notion Platform & Service Registry: `Billing Entity`, `Account Standing`, `Cost / Balance`, `Blocks Alpha`.

The format previously had nowhere to record that an account was unpaid, exhausted, or not yet activated. That is not a cosmetic gap: an unpaid LiveKit balance and exhausted Runway credits were both reading as plain "Active," which is why the tracker gave no warning that alpha was blocked.

### Live-stack audit found six untracked paid services

Audited every API key and external host the running code actually touches against what the tracker claimed. **Six paid or credentialed services were entirely absent**: Fal.ai, Reactor, Adobe Express, Adobe PDF Services, Frame.io, and both domains.

Root cause worth recording: the tracker was built by reading documentation, never by checking against the running system. Docs describing docs drift, and nothing cross-checked them.

Two further corrections found:

- **Seedance already ships**, resold through Fal.ai (`fal-ai/seedance-v1-lite` / `-pro`, plus Kling). `main.py` ~2224 has a commented-out stub for direct routing, "when enterprise terms apply." So the ByteDance conversation is a **margin decision on a live path**, not new capability.
- **Deepgram and Cartesia have their own API keys** in `studioyou-fy-agent/.env`, contradicting both that repo's `CLAUDE.md` and `SERVICES.md`, which claimed no separate keys were needed beyond LiveKit credentials. Two separately-billed accounts were invisible.
- **Tavus is not just stale env vars.** `main.py` ~1223-1460 still has live handlers posting to `tavusapi.com/v2/replicas` and `/v2/conversations`. Dead code in a running service pointed at a provider no longer in the stack.

### Alpha blockers identified

- **LiveKit: $50 balance due, unpaid.** Agent cannot hold a conversation room.
- **Runway: credits exhausted.** Avatar cannot render.

Both per Lee. The avatar feature itself is confirmed working; these are funding gaps, not technical failures. Together they mean the live IDEATE retest, which is the gate on alpha close, cannot be attempted. Recorded at the top of `CLAUDE.md` as item 0.

### Reactor / Helios: live world generation is an open architecture question

Context from Lee. Reactor is a worldbuilding model company; the dev relationship went cold, though they still supply dev credits. In-product, Helios powers live world generation from an archetype FutureYou selects during onboarding/briefing. Two problems: the token burn rate is **not practical to sustain as a live call**, and Lee's revised read is that Reactor is likely a **retail reseller** of other companies' models rather than the builder.

Two candidate paths, both Lee's: pre-render a video per archetype, or find a better world-model resource including direct relationships (NVIDIA, Alibaba, ByteDance). The second is the same negotiation as the Seedance-direct row, so one partner conversation could cover both video and world generation. This is an alpha scope decision, not just a tracker row.

### Anthropic credits verified and corrected

Verified against the event's own published information: the $200 is the **Claude Impact Lab hackathon perk** (Los Angeles, 2026-08-08, $200 API credits per attendee). Balance is $212.62.

Two corrections to how these were being planned around:

1. **They are API credits.** They cannot pay for Claude Code / Cowork build sessions, which run on the Max subscription. Only the product itself calling Claude draws them down.
2. **The Aug 15 expiry is unverified.** Event materials state no expiration; the console credits page was unreachable this session (Chrome extension not connected). Also unconfirmed: whether the `ANTHROPIC_API_KEY` in Cloud Run belongs to the same org holding the credits. If not, alpha testing spends real money and the $200 sits unused.

Spend this month is $1.73, so urgency is low regardless.

### Other confirmations from Lee

- `studioyou.studio` is **live**, part of the livelink user sign-in engine. Not a leftover. Registrar and renewal date unknown, which is an exposure since a lapse breaks login.

## Notion

Registry schema extended with the same four columns. StudioYou rows went from 11 to 25. LiveKit and Runway updated with their real standing and flagged alpha-blocking. All StudioYou rows set to `Lee (personal)` billing.

## Open items for next session

- [ ] **Settle LiveKit ($50) and top up Runway.** Blocks the live IDEATE retest, which blocks alpha.
- [ ] **Load-bearing walkthrough with Lee**, service by service. Adobe Express, Adobe PDF Services, and Frame.io are the least clear from code alone. Lee asked to do this as a guided pass rather than answer cold.
- [ ] **Rebuild the sprint schedule.** Per Lee, billing constraints and a focus shift to SCREENBot set the proposed dev schedule back. He wants it rebuilt once hygiene is correct, not before. The existing S1-S6 plan in `CLAUDE.md` targets alpha close the week of 2026-08-10 and is no longer real.
- [ ] **Decide the world-generation path**: pre-rendered archetype videos vs. a new model partner.
- [ ] **Move billing to Frisson Digital, Inc.** Counsel and accountant question, not a dev task.
- [ ] Confirm registrar and renewal for both domains.
- [ ] Strip dead Tavus code from `main.py`; fix the stale "Tavus Phoenix is aging your photo" string at `studioyou-app/dashboard.html:2234`.
- [ ] Verify Fal.ai, Deepgram, and Cartesia standing. Any could be a further hidden blocker.
- [ ] Carried from 2026-08-08: live IDEATE retest; `studioyou-app` checkpoint commit `54c6458` still unreviewed; canvas whiteboard rework; generated-asset persistence; Docker sandbox exploration.

## Proposed structural work (discussed, not yet started)

1. **Make the audit mechanical.** Extend `tools/check_repo_status.sh`, or add `tools/audit_services.sh`, to extract every env var the code reads and every external host it calls, diff against `SERVICES.md`, and fail on anything present in code but missing from the tracker. This is the automated version of the grep that found six missing services today. Highest-leverage change available.
2. **A Frisson-level ops repo.** Nothing today owns cross-product concerns, which is why the corporate structure was stranded in a stale section of one product's `CLAUDE.md` and why `check_repo_status.sh` is copy-pasted per repo. Would hold the cross-product registry, shared tooling in one copy, the corporate record, and the session protocol. Must respect that StudioYou and SCREENBot are independent products.
3. **Move `studioyou-app` and `studioyou-site` out of `~/Downloads` into `~/Projects`.** The protocol classifies Downloads as an untrusted staging tier; two of four repos living there is how the 92-file uncommitted checkpoint went unnoticed.
4. **Split `CLAUDE.md`.** 594 lines, carrying sprint system, funding pipeline, and entity structure, none of it backend-specific. That is exactly why the entity info went stale where nobody would look.
5. **Build a monthly run-cost number.** Nothing anywhere answers what StudioYou costs to operate. Needed for incubator and fund conversations, and now buildable for the first time since the full service list exists.

---

# Session close addendum, 2026-08-09

The session continued well past the original tracker build-out into a full live-systems verification pass. Everything below was verified against running code, live APIs, or billing consoles, not documentation.

## Headline: alpha is blocked on roughly $20

**Runway Dev is the only hard blocker.** Zero credits, no card saved, autobilling disabled. Payment history prices the fix: $24 bought 3,000 credits, $20 bought 2,000, so ~$0.0088/credit. **A ~$20 top-up restores the avatar.**

Everything else in the stack is current.

## Corrections made to my own earlier findings

Recorded plainly, because several were wrong and the pattern matters:

1. **LiveKit, corrected three times.** First recorded as an alpha blocker, then as $50 arrears. Neither was right. It is a **$50/month Ship-plan subscription**, current, next cycle Sept 1. August usage is **0 GB** — the plan includes 5,000 agent minutes going entirely unused. July ran 2,645 agent minutes and 5,865 participant minutes, all inside limits.
2. **Domain expiry risk, retracted.** Flagged as the largest operational exposure on the assumption renewals were unknown and possibly imminent. All 11 Porkbun domains auto-renew, are locked, and are 200+ days out. Not a risk.
3. **Reactor, corrected.** Implied depleted and near-dead. It holds **688,987 credits**. Not an alpha blocker.
4. **Anthropic Startup Program framing.** My web-search-derived take was worse than the research already in Lee's July records. Program membership is open regardless of VC backing; institutional funding gates only the higher credit tiers. And the application was already submitted 2026-08-05 under a dedicated Frisson Console org.
5. **Adobe cost.** Not one ~$70 subscription. Two: Creative Cloud Pro $69.99 and a standalone Firefly 7,000 Credits plan $29.99. **$99.98/month.**

What held up without exception: findings derived from grepping the actual code and querying actual APIs.

## Verified inventory

**Registry grew from 8 tracked services to 33.** Thirteen were invisible while actively costing money.

- **Porkbun:** 11 domains, all auto-renew/locked/private. `studioyou.app` and `studioyou.studio` renew 2027-03-27. SCP company name is set at **account level**, so one edit clears all 11. Four `frisson.*` registrations are defensive and unused.
- **Netlify:** one team hosting 12 sites across both products. **The team itself is named SuperCreativePeople**, slug embedded in every admin URL — not a quick field edit. `frisson.digital` confirmed live on Pro. Two orphan projects (`thriving-conkies-31dad5`, `profound-gaufre-d7e81d`) plus `ground-ai-blueprint`, `universal-briefing`, `seedance-briefing` are live and undocumented.
- **Creative portfolio:** 7 platforms, ~$140/month confirmed floor, mostly idle capacity.

## Strategic consequences

**The direct-partner case weakened substantially.** Seedance is reachable four ways (fal.ai in production, Runway 2.5, ImagineArt, direct). World generation is reachable three ways (Reactor with 688,987 credits including Alibaba's model, OpenArt's World/Character modes with 24,000 credits, pre-rendered archetypes). **The Alibaba prospective-partner row collapses into Reactor** — same capability, already accessible, no new agreement.

**Corporate structure recorded.** Frisson Digital, Inc. owns StudioYou and SCREENBot via executed IP assignment. SCP Inc. owns nothing. All infrastructure runs on Lee's personal cards. The finding is **asset control, not commingling**: the assignment moved the products but not the accounts they run on.

**The SCP naming problem, scoped.** Every vendor account carries "SuperCreativePeople" as company name. Decision: strip now, do not replace with Frisson until Frisson has a payment instrument. Three exceptions: GCP billing account `019309-BEB782-398472` is ringfenced while the Google for Startups application is under review; the Netlify team slug needs deliberate handling; and **fal.ai has SCP embedded in display name, full name, and username**, requiring a support ticket rather than a field edit.

## Next session opens with

1. **Top up Runway Dev (~$20).** Unblocks the live IDEATE retest, which gates alpha.
2. **Alibaba CoCreate finalists notified on or around 2026-08-10.** If selected, live LA pitch Sept 9-10 — the avatar needs to work by then.
3. **Google for Startups response due** (submitted 08-05, 3-5 business day window).
4. **Load-bearing walkthrough**, now including the 5 undocumented Netlify sites.
5. **Rebuild the sprint schedule.** Per Lee, billing constraints and the SCREENBot focus shift set it back; rebuild once hygiene lands.
6. **Strip the SCP name** from vendor accounts, minus the three exceptions.
7. Test OpenArt World/Character modes as a Reactor production alternative — zero marginal cost, 24,000 credits already paid for.
