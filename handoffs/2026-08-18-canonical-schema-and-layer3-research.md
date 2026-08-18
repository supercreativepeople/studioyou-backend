# Handoff — 2026-08-18 — Canonical Schema Build + Layer 3 Research/Authoring Pass (IDEATE, DEVELOP)

## Session

Opened on the sprint architecture discussion deferred from the 2026-08-17 handoff. Landed a locked three-tier SUCCESS STATE framework (step/session/goal) for S2, then Lee enabled Auto Mode and the session shifted into real build work: a canonical per-building JSON schema for all 12 buildings, a full authoring-reference doc set delivered to Lee for his own batch-authoring pass, and — after Lee's own StudioBinder-inspired epiphany mid-session — a new research-driven Layer 3 authoring philosophy that got applied end-to-end to IDEATE and partially to DEVELOP. Four separate architecture decisions got locked into `FY_LAYER2_SCHEMA.md` this session. This was a long session (picked up from one prior compaction) — closing here deliberately rather than letting it run into a second.

## What Was Done

1. **Three-tier SUCCESS STATE framework locked for S2** (step/session/goal) — step tier already existed (Section 6.1), session tier (open/close catch-up) and goal tier (standing objective record, can halt on insufficient input) newly scoped. Documented in a new Claude Project doc, `StudioYou_FY_DecisionTiers_Positioning_2026-08-17.md`.
2. **Corrected framing from Lee, mid-session:** Runway/LiveKit is FY-avatar infrastructure (a standing CODB, tracked via `check_service_balances.md`), not part of the per-building goal-check gate — propagated the fix everywhere it had been written wrong.
3. **Canonical building schema built.** `tools/build_schema.py` (v2, handles both IDEATE's flat-section style and DEVELOP's 5-archetype-track style) generates `knowledge/schemas/<building_id>.json` for all 12 buildings from the existing `.md` specs + frontend `BUILDING_TASKS`, plus `_drift_report.json` surfacing content-parity gaps (biggest: DEVELOP's 13-step frontend placeholder has zero title overlap with its real 31-step, 5-track spec). Commit `5e4b9b0`.
4. **Skeleton-building authoring rule locked** into `FY_LAYER2_SCHEMA.md` — any building whose `spec_level` is `stub`, or where drift surfaces unauthored real content, gets raised to Lee rather than authored solo. Commit `bf4d325`. Model-feedback addendum (canvas-card actions as a future second input to Section 7, alongside Lee's manual field testing) also added. Commit `9590a0c`.
5. **Authoring-reference doc set built and delivered.** `tools/build_all_building_references.py` generates one markdown reference per building (`knowledge/schemas/authoring_reference/*.md`) — IDEATE/DEVELOP render their full real spec for revision, the other 10 render a blank blueprint template (FY_LAYER2_SCHEMA Sections 1-10) pre-seeded from current frontend titles. All 12 delivered to Lee via SendUserFile for his own batch-authoring pass. Commit `41b5d63`.
6. **Philosophy shift, Lee-originated.** After reviewing StudioBinder's marketing (named-practitioner technique breakdowns, not personal-anecdote content), Lee concluded Layer 3 shouldn't be limited to his own catalog — it should draw on verified, sourced, real-practitioner research, with his own material staying wherever it's genuinely load-bearing. Agreed process: research pass first (with binding sourcing/verification discipline), then author steps together from what the research turns up, building by building, starting at IDEATE (the natural entry point).
7. **Two more architecture decisions, both Lee-originated, both locked into `FY_LAYER2_SCHEMA.md`:**
   - A two-tier Layer 3 retrieval design — a pre-vetted corpus (fast path) plus a creator-triggered live lookup ("do you have a favorite X that inspires you?") that gets hedged and promoted into the corpus once verified (slow path). Also functions as an input to FY's persistent per-creator model over time, not just a stuck-point tool.
   - A generic sixth "Other" track for any archetype-branched building (DEVELOP today), using the same 3-question skeleton IDEATE's Step 8 OTHER branch already uses — never a dead end for a creator whose project doesn't fit the named tracks.
   - A data-driven v1 scope ceiling + post-launch update program — bounded track/injection-corpus depth at ship, next-tier coverage prioritized from usage signals already planned elsewhere in the schema (canvas-card actions, Other-track usage, Section 11 generation logging), not from guessing. Commit `03f7659`.
8. **IDEATE Layer 3 research pass, fully integrated.** Verified, sourced injections added to Steps 1 (Kusama), 2 (Miyazaki), 4 (Blakely), 7 (McCartney), 8 (Catmull's "ugly baby") — Step 3 got a short FY-approach nuance (Catmull's elevator-test tension) instead of a forced story block. Steps 5/6 untouched (Lee's own material). Commit `ec344da`.
9. **DEVELOP Layer 3 research pass, batch 1 integrated.** Verified injections added to N-5 (Stephen King), M-1 (Paul Epworth on Adele's "21"), V-1 (Georgia O'Keeffe). P-1 and B-1 researched but didn't clear the sourcing bar this round — left open, not forced.
10. **The Lock Calculus (Lee Brownstein method)** — a five-factor weighing framework (time, money, patience, window of opportunity, revisability) replacing "chasing certainty" at any lock/ship decision — written once as a new FY Universal Behavioral Rule, referenced (not duplicated) from all five DEVELOP lock steps (N-7, M-6, V-6, P-6, B-6). Commit `b0cea60`.

## What Was Found

- DEVELOP's frontend placeholder (13 generic steps) has zero title overlap with its real spec (31 steps across 5 archetype tracks) — the drift report makes this concrete for the first time rather than it being a vague known gap.
- Verification discipline caught two real misattribution/weak-fit risks before they went in: "art is never finished, only abandoned" is commonly misattributed to da Vinci (it's Paul Valéry, about poems) — not used; several researched leads (MrBeast, Ira Glass, Frida Kahlo, Conan O'Brien, Wendy's Twitter voice) had real, findable material that didn't actually clear the two-source/primary-source bar for the specific step they were being considered for — banked as open rather than forced in.
- The "how do we handle a use-case with no archetype data" question Lee raised turned out to have two different answers at two different layers: content-lookup (solved by the two-tier retrieval design) and structural (DEVELOP genuinely has no track for a creator whose project isn't Narrative/Music/Visual/Podcast/Brand — the Other-track gap is real today, not hypothetical).

## Files Changed

All in `studioyou-backend`:
- `tools/build_schema.py` (new)
- `knowledge/schemas/<building_id>.json` × 12 (new) + `knowledge/schemas/_drift_report.json` (new)
- `knowledge/FY_LAYER2_SCHEMA.md` (edited 4×: model-feedback addendum, skeleton-authoring rule, Layer 3 sourcing model + v1 ceiling, Lock Calculus)
- `tools/build_develop_reference.py` (new), `knowledge/DEVELOP_REFERENCE_FOR_AUTHORING_2026-08-17.md` (new)
- `tools/build_all_building_references.py` (new), `knowledge/schemas/authoring_reference/<building_id>.md` × 12 (new)
- `knowledge/schemas/ideate.json` (edited — 5 injections + 1 nuance)
- `knowledge/schemas/develop.json` (edited — 3 injections + 5 lock-step references)
- This handoff doc; `CLAUDE.md` rebuilt (see below)

`studioyou-fy-agent`, `studioyou-app`, `studioyou-site` — untouched this session; confirm still clean/in-sync at next open, don't assume.

## Git State at Close

`studioyou-backend`: 8 commits this session (`5e4b9b0`, `9590a0c`, `bf4d325`, `94fa66b`, `41b5d63`, `03f7659`, `ec344da`, `b0cea60`), all pushed to `origin/main`, working tree clean as of close. Other three repos not touched — re-verify at next open.

## Open Items & Carry-Forward

- **IDEATE Step 8** — `creator_prompt`/`fy_rationale` still unauthored (voice copy, not a research gap). Small, but real.
- **DEVELOP** — P-1 (podcast, Format Design) and B-1 (Brand voice/tone) still need a verified injection; remaining un-reviewed steps (most of N-2/3/4, M-2–5, V-2–5, P-2–5, B-2–5) haven't had a systematic pass yet to confirm which do/don't need one.
- **DEVELOP's sixth "Other" track** — structural build (Purpose/Success/Failure/FY approach/steps from scratch), explicitly a "build with Lee" session per the standing skeleton-authoring rule, not a research task. Not started.
- **Two-tier Layer 3 retrieval system (fast corpus / slow-path live lookup)** — architecture locked, no infrastructure built yet. Deliberately deferred — it's Tier 2 orchestrator scaffolding, and the orchestrator itself (Sprint S2) is still unbuilt. Extra verified research from this session not yet in any schema (Miyazaki as an IDEATE Step 1 alt, two Emma Chamberlain angles, Karen Kilgariff/My Favorite Murder) is sitting in conversation only — will need to seed the corpus once that system exists.
- **Remaining 10 buildings** (FUND, CAST, PLAN, PRODUCE, POST, LICENSING, DISTRIBUTE, BRAND, MARKET, MONETIZE) — authoring-reference blueprints delivered to Lee; session is waiting on his batch-authoring pass before any further building-specific work.
- **Original schema-refactor task list items #3–7** (Supabase migration for `fy_session_snapshots`/`fy_goal_records`, backend endpoint serving the canonical schema, studio.html track-aware wiring, agent/prompts.py wiring, end-to-end test) — paused this whole session for the authoring-reference/research side-thread. Still pending.
- **FY model-selection learning loop** (canvas-card action logging → Section 7 second input) — tracked in Notion Sprint Tracker (`3bfb9630-47e5-8118-a8a3-f27385ef760e`), not started.
- Notion Sprint Tracker rows from this session's earlier half (schema refactor, Tier 2 orchestrator spec, orchestrator implementation, DEVELOP creator-facing copy) have notes appended but status fields not re-confirmed against actual current state — worth a pass next session.

## Next Session Opens With

Lee's call on where to pick up — three real options, not a default: (1) continue the DEVELOP research pass (P-1, B-1, remaining steps), (2) build DEVELOP's sixth Other track together, or (3) shift to the paused orchestrator/backend-wiring tasks (#3–7 above) now that IDEATE has a full round of real content behind it. Whichever Lee picks, open by re-confirming git status on all four repos per protocol before assuming this handoff's state still holds.
