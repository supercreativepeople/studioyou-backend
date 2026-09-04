# Handoff: studioyou-backend

Date: 2026-09-04 (session 4)
Session: Runway credit-drain fix (test_mode), Cartesia voice drift resolution, and custom FutureYou avatar architecture plus groundwork.

## What Was Done

**Runway credit drain fixed.** Lee had been manually disabling the avatar during testing to avoid burning credits. Root cause was eager avatar start: the agent called `start_avatar()` on every job before any user interaction, so every test session, page reload, and error recovery spent credits immediately. Runway bills 2 credits up front plus 2 per 6 seconds of active session time, so the charge lands whether or not anyone speaks.

Lazy start was evaluated and rejected. `RoomOutputOptions(audio_enabled=False)` has to be set at `session.start()` and cannot be changed after init, so whether the avatar will be used must be known before the session starts.

The shipped fix is a `test_mode` flag carried in `formation_context`. When true, the agent skips `start_avatar()` entirely and falls through to Cartesia audio only. Full conversation still works with zero Runway spend. Implemented across all three repos with dual-layer activation: the backend auto-detects `nyclaabq@gmail.com` via a `TEST_EMAILS` set (so no frontend change is strictly required), and the frontend also sends `test_mode` explicitly so intent is visible in the payload. Manual avatar disabling is no longer needed.

`nyclaabq@gmail.com` is now the confirmed E2E test account.

**Cartesia voice drift resolved.** The `agent.py` Session AD docstring claimed a switch to sonic-3.5 and the Jameson voice that was never actually made in code. CLAUDE.md Live State was correct throughout (Corey on sonic-3); the docstring was the only wrong artifact. Lee elected to keep Corey on sonic-3. The false claim was removed and the active voice recorded inline.

**Custom FutureYou avatar: architecture settled and groundwork shipped.** Runway's own documentation contradicts itself on whether avatars can be created programmatically, so the question was settled by probing the live dev API directly. Findings are in the next section. Groundwork shipped: the Supabase table, per-creator avatar resolution in the agent, backend injection, and the brief generation module.

A full architecture document was written to the Claude Project at `claude/FutureYou_CustomAvatar_Architecture.md`.

## What Was Found

**Runway API, verified live rather than from docs:**

Avatar creation is fully programmatic. `POST /v1/avatars` requires `name`, `referenceImage`, `personality`, and `voice` (an object discriminated on `type`).

There is no training step. Avatars return `status: READY` immediately. This removes the async training job, status polling, and the "preparing your FutureYou" wait state from all earlier plans.

`referenceImage` is fetched server side from a URL, so a publicly readable Supabase Storage URL is sufficient. No multipart upload is needed.

Runway does native voice cloning: `POST /v1/voices` with `{name, from: {type: "audio", ...}}`. The `audio` discriminator is confirmed valid.

The account holds exactly one avatar, "The DUDE" (`d44bf1d0-c297-4e26-839a-93099a485ca5`), matching `RUNWAY_AVATAR_ID` in the agent `.env`. Its voice is `{type: "runway-live-preset", presetId: "zach"}`.

**Voice cannot consolidate onto Runway.** Per LiveKit's Runway integration docs: "LiveKit TTS settings will supersede selected voices and personalities configured for the Runway character." Cartesia generates the speech and Runway only renders video lip synced to it, so a Runway cloned voice would be silently ignored on this path.

A consequence worth knowing: The DUDE's `personality` and `startScript`, configured in the Runway dashboard, are inert. Claude's system prompt is the actual brain and Runway never sees those fields. That is dead config.

**Two CLAUDE.md errors found and corrected this close:**

1. Section 3 stated "Database: Supabase. RLS disabled." That directly contradicts section 7 Locked Decisions ("Security fix 6: RLS ENABLED + FORCED") and the live state confirmed at session open (RLS on all 9 public tables). Section 3 was stale and wrong.

2. Locked Decisions claimed `lk agent update` does not rebuild and that only `delete && create` produces a fresh image with a new agent ID. This was verified false. `lk agent deploy` rebuilt and shipped twice this session (16:36Z and 17:43:21Z) while preserving agent ID `CA_Mnhkjj3mUr7T`, producing a new version string each time. The delete and recreate dance is no longer necessary.

## Files Changed

| File | Change | Commit |
|---|---|---|
| `main.py` | `test_mode` support: `TEST_EMAILS` auto-detect plus POST body flag | `70cb447`, `566b422` |
| `main.py` | Custom avatar injection: looks up active `ready` `creator_avatars` row, injects `runway_avatar_id` / `runway_voice_id`, skipped under test_mode, non-fatal on failure | `97224bd` |
| `future_you_brief.py` | New. Brief generation: static cacheable system prompt plus creator data in user turn, returns `{brief, image_prompt}` | `c96422f` |
| `SESSION_LOG.md` | Post-compaction entries appended | this close |
| `CLAUDE.md` | Rebuilt: RLS correction, agent deploy correction, avatar architecture, new Live State | this close |

Supabase migration `create_creator_avatars` applied to project `rubwhfjwqonqhfbkhren`: email keyed, status lifecycle (`draft` through `ready`), history retained so a FutureYou can be regenerated as formation data evolves, partial unique index enforcing one active avatar per creator, RLS enabled.

Related commits in sibling repos: `studioyou-fy-agent` `c998625`, `ee22229`, `a0c9ccf`. `studioyou-app` `8e7b755`.

## Git State at Close

`studioyou-backend` HEAD `c96422f` before this close's documentation commit. Clean and in sync with `origin/main` other than the documentation written during close. `__pycache__/` remains untracked and was deliberately excluded from all commits.

## Open Items and Carry-Forward

**Custom avatar pipeline, not yet built:**

1. Supabase Storage bucket for source uploads. Must be publicly readable because Runway fetches `referenceImage` server side.
2. Pipeline endpoints: upload, generate brief, generate portrait, creator approval, provision Runway avatar and voice, mark `ready` and set `is_active`.
3. Open integration detail: how the reference image is passed or tagged into a Gen-4 References call. Settle this against the live API by probing, not by reading docs. The docs already contradicted themselves once today.
4. Frontend UX. Lives in its own building on the lot. Progressive: photo unlocks it, voice deepens it, formation data makes it uniquely theirs.
5. Product decision still open: whether avatar creation is gated on formation completion (better data to write the brief from, fits the gamification model) or offered early as an acquisition hook. This shapes the UX and is a product call, not a technical one.

**Carried from prior sessions:**

- `DASHSCOPE_API_KEY` still pending Alibaba enterprise verification. Endpoints return 503 until the key is present. Deploy command when ready: `gcloud run services update studioyou-api --region us-east1 --project neat-tangent-474222-m9 --update-env-vars DASHSCOPE_API_KEY=<key>`
- S2 orchestrator end to end test. Unblocked as of session 3 but requires a live session to exercise.
- `supercreativepeople@gmail.com` still has no `formations` record in Supabase. Needs a formation run in studio.html at some point.
- TAVUS_* entries remain in the `studioyou-fy-agent` `.env`. Backend code paths were stripped in `5172736`; the agent `.env` cleanup is the remaining half.

## Next Session Opens With

Test the `test_mode` path end to end. Sign in as `nyclaabq@gmail.com` in studio.html and confirm a full FY conversation runs with zero Runway spend and no manual avatar disabling. All three repos are deployed for this: agent version `Fqxg6JLvSBb8`, backend through Cloud Build, frontend through Netlify.

Once that passes, the S2 orchestrator end to end test is the next blocker to clear, since it also needs a live session and can be run in the same sitting.

If avatar pipeline work is preferred instead, start at open item 3 above: probe the Gen-4 References API for the reference image tagging syntax, because every other piece of the creation flow is already specified.

---

## RESOLVED same session: Runway credits were 0, topped to 3,000

**Resolution (2026-09-04, live-verified via `GET /v1/organization`): balance is 3,000.**
Lee topped up Runway Dev ($30.00, 09/04/2026 11:25 AM, 3,000 credits) and **enabled
autobilling**, set to auto-recharge whenever credits fall below 500, with a Visa card
saved to the project. The silent-zero failure mode described below is now CLOSED for
the first time since it was first flagged in July. Live avatar rendering and custom
avatar provisioning are unblocked.

Lifetime spend on Runway Dev is now $99.00 for 10,500 credits, roughly $0.0094 per credit.

One correction this resolution surfaced: a Runway **Platform** balance of 684 credits
was briefly read as evidence that credits were fine. It is not. Dev and Platform are
separate accounts with separate wallets. Always verify Dev via the API, never by
reading the Platform UI. See Locked Decisions.

The original finding is preserved below for the record.

---

### Original finding: Runway credit balance is 0

Live-verified via `GET https://api.dev.runwayml.com/v1/organization`: `creditBalance: 0`.

SERVICES.md recorded 2,500 credits as of 2026-08-17 with zero usage since. Those
credits are now gone. This is the exact silent-zero failure mode SERVICES.md already
flagged as still live (autobilling off, no card saved), and it is almost certainly the
eager-avatar-start drain fixed in this session having consumed the balance: the agent
started a billed Runway session on every job, before any user interaction, and Runway
bills 2 credits up front plus 2 per 6 seconds of active session.

Impact:

- Any work requiring live avatar rendering is BLOCKED until Lee tops up.
- E2E testing is NOT blocked. The `test_mode` path shipped this session skips the
  Runway avatar entirely and runs on Cartesia audio, so `nyclaabq@gmail.com` can
  exercise a full FY conversation at zero credit cost. The fix shipped today is
  precisely what makes testing possible despite the zero balance.
- Custom avatar provisioning (`POST /v1/avatars`) will also need credits, so the
  avatar pipeline build can proceed but cannot be live-tested until top-up.

Recommendation carried forward from SERVICES.md and now urgent: enable autobilling
with a threshold, or set a spend cap, before the next top-up. This is the second time
the balance has reached zero silently.

Account context verified same call: tier `maxMonthlyCreditSpend` 50000, and
`gen4_image_turbo` is present in the account's available models, confirming the
Gen-4 image path chosen for FutureYou portrait generation is actually available here.
