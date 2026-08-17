# StudioYou — Live-Test Service Balance Check

Runbook for verifying the four services a live FY avatar test actually calls, before any code work resumes and before any live test. Built 2026-08-17 after Runway's balance sat wrong in two records for six days.

**Why this exists:** `SERVICES.md` and the Notion registry are records of the last time someone checked. They are not the check itself. This file is the check. Run it, don't read the docs and assume they're still true.

**API-based automation was evaluated and ruled out for now.** Deepgram's `/v1/projects/{id}/balances` endpoint returned `403 Forbidden` with the key currently in `studioyou-fy-agent/.env` — that key is scoped for STT calls, not project/billing reads. Cartesia's credit-usage endpoint requires a separate admin key (`sk_car_admin_...`, generated at `play.cartesia.ai/keys/admin`) that doesn't exist yet. Runway and LiveKit expose no balance API at all — LiveKit's Analytics API is Scale-plan-only (we're on Ship) and only returns historical session data, not remaining quota, even on that tier. So this runbook is a browser check, not a script, until/unless Lee generates the missing admin-scoped keys.

## How to run this

Sign in via Google SSO as `supercreativepeople@gmail.com` (all four services return this account first in the account picker — no password entry needed). Use Claude in Chrome, not a headless request.

| # | Service | URL | Where to look | Read this number |
|---|---|---|---|---|
| 1 | Deepgram | https://console.deepgram.com/ → Dashboard | "Credit" card | Dollar balance remaining |
| 2 | Runway Dev | https://dev.runwayml.com/settings/billing | "Current credits" | Credit balance |
| 3 | Cartesia | https://play.cartesia.ai/subscription | "Model Credits Remaining" and "Voice Agent Dollars Remaining" | Both numbers — the Voice Agent Dollars figure is the tight one |
| 4 | LiveKit Cloud | https://cloud.livekit.io/projects/p_3abx9tkixic/settings/billing | "Current plan" and this month's usage table | Confirm plan is still Ship ($50/mo) and check agent-session minutes used against the 5,000/mo included in the plan |

## Warning thresholds — notify, don't auto-act

No autobilling is configured anywhere in this stack, by Lee's explicit decision (2026-08-17). Nothing here should ever add a card or trigger a charge. The only action on a threshold breach is a notification, so Lee can manually top up or make a subscription call before the balance actually hits zero mid-test.

| Service | Warn below | Why this number |
|---|---|---|
| Runway Dev credits | 500 credits | Historical burn per test room ran 13–98 credits (CODB log, Session AG/AF). 500 leaves roughly 5–10 more test rooms of runway before a hard stop. |
| Deepgram balance | $20.00 | Conservative floor given near-zero spend to date ($0.03 total as of 2026-08-09) — this threshold exists for when live testing resumes and usage actually starts drawing it down. |
| Cartesia Voice Agent Dollars | $3.00 | At $0.06/min agent calling, $3 is roughly 50 minutes of remaining runway — enough warning to top up before a session gets cut off mid-test. |
| Cartesia Model Credits | 20,000 credits | Text-to-speech is priced 1 credit/character; 170K+ on hand as of 2026-08-17, this floor is a distant early-warning, not a near-term risk. |
| LiveKit agent-session minutes | 4,000 of 5,000 used this billing cycle | Warns before overage billing kicks in ($0.12/GB and per-minute overage beyond the Ship plan's included quota). |
| LiveKit — plan check | Any value other than "Ship" | Confirms the $50/mo subscription itself is still active and hasn't silently lapsed or changed. |

## What to do when a threshold is crossed

State the finding plainly (service, current balance, threshold crossed) and stop there. Do not add a card, do not enable autobilling, do not purchase credits — those are Lee's calls every time, per the no-autobilling decision. Update `SERVICES.md` (both `studioyou-backend` and `studioyou-fy-agent`) and the Notion Software Stack Service Registry with the live-checked number and today's date in Last Verified, regardless of whether a threshold was crossed — a clean check is itself worth recording so the next person (or the next scheduled run) knows this isn't stale.

## When this runs

1. **Scheduled**, every 3 days, via the "StudioYou — Service Balance Check" scheduled task. Silent if everything's above threshold; pushes a notification to Lee if anything isn't.
2. **Before any live FY test session** (IDEATE retest, avatar demo, anything that opens a LiveKit room) — this is now a required step in `dev-session-protocol`'s pre-live-test checklist, not optional.
3. **At session open**, if the session's scope touches `studioyou-fy-agent` or a live-test task — same protocol reference.
