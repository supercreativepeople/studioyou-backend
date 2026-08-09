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
