# Handoff — 2026-09-04 Session 3

## Session
Date: 2026-09-04
Repo: studioyou-backend
Commits this session: `ac24113`, `2a8ccde`
Backend HEAD at close: `2a8ccde`

---

## What Was Done

Two bugs fixed and deployed. Both auto-deployed via Cloud Build trigger on push to main.

### 1. formation_initialize() — commit ac24113

**Root cause:** `formation_initialize()` in `/api/formation/initialize` patches the `formations` table in Supabase but never included `creator_type` or `formation_data` in the patch payload. As a result, `build_fy_system_prompt(email, building_id, mode)` — which reads those columns to construct the FY system prompt server-side — was always getting empty values and falling back to the minimal generic prompt. Creator's briefing answers and type were never reaching FY.

**Fix:** Added `creator_type` and `formation_data` to the `sb_patch` dict in `formation_initialize()`. `formation_data` is stored as jsonb containing the full briefing/answers structure.

### 2. S2 Orchestrator — commit 2a8ccde (three bugs)

**Bug 1 (primary — steps never advance):** `FY_ORCHESTRATION_MODEL` Cloud Run env var is set to `claude-fable-5`. That is not a valid Anthropic API model name. Every call to `evaluate_success_state()` threw an API exception, was caught by the broad `except Exception`, and returned `{"satisfied": False, "reason": "eval error: ..."}`. Steps never advanced regardless of what the creator said.

**Fix:** `evaluate_success_state()` now tries `ORCHESTRATION_MODEL` first. If that throws any exception, it logs a warning and retries with `SURFACE_MODEL` (`claude-sonnet-4-6`). If the surface model also fails, returns `satisfied: False` with the error reason. This means S2 step advancement now works even with the misconfigured env var. The env var itself should be updated to a valid model ID when one is confirmed — see Pending section below.

**Bug 2 (seed condition):** The seed logic that sets `active_step_num = 1` for a building checked `b.get("state") == "active"`. But `EMPTY_BUILDINGS_STATE` initializes all buildings with `state = "untouched"`. A building that's been entered for the first time is `untouched`, not `active`, so the seed never fired cleanly. (The `or 1` fallback in `step_num = int(b.get("active_step_num") or 1)` partially masked this, but the state check was wrong.)

**Fix:** Seed condition now checks `b.get("state") in ("active", "untouched")`.

**Bug 3 (JSON parsing brittle):** `evaluate_success_state()` called `json.loads()` directly on the raw model response. If the model wrapped its JSON in markdown code fences or added prose, parsing failed silently.

**Fix:** New `_parse_raw()` helper — first tries direct `json.loads()`, then strips markdown code fence wrapper if present, then falls back to `re.search(r'\{[^{}]*"satisfied"[^{}]*\}', raw)` to extract an embedded JSON object. Raises `ValueError` only if none of those succeed.

---

## What Was Found

- `FY_ORCHESTRATION_MODEL` env var in Cloud Run is set to `claude-fable-5`. No such model exists in the Anthropic API as of 2026-09-04. This was silently breaking S2 entirely — every step eval returned false, no errors surfaced to the user.
- `build_fy_system_prompt()` architecture is correct and complete — it reads formations table, constructs a rich system prompt from creator_type/arsenal/roadblock/answers. It just never had data to work with because `formation_initialize()` wasn't writing it.
- STEP_MAP, `advance_building_step()`, the frontend `orchestrator` dict handling — all correct. The S2 orchestrator logic itself was sound; only the two data-pipeline bugs above were blocking it.

---

## Files Changed

- `main.py` — two commits:
  - `ac24113`: formation_initialize() adds creator_type + formation_data to Supabase patch
  - `2a8ccde`: evaluate_success_state() rewrite (model fallback + _parse_raw helper) + seed condition fix
- `CLAUDE.md` — updated Live State (Backend HEAD, Sprint, Pending bugs), Changelog entry, Locked Decisions (model fallback rule), Tech Stack note on FY_ORCHESTRATION_MODEL

---

## Git State at Close

```
Branch: main
HEAD: 2a8ccde — fix: S2 orchestrator — model fallback, robust JSON parse, seed untouched buildings
Working tree: clean
Cloud Build: auto-deployed on push
```

Both commits auto-deployed via Cloud Build trigger `studioyou-backend-main`. No manual deploy needed.

---

## Open Items and Carry-Forward

1. **FY_ORCHESTRATION_MODEL env var** — update to a valid Anthropic model ID. The intended architecture is a cheaper/faster model for step eval (haiku-class or fable-class). Confirm the correct model ID with Anthropic docs, then:
   ```
   gcloud run services update studioyou-api \
     --region us-east1 \
     --project neat-tangent-474222-m9 \
     --update-env-vars FY_ORCHESTRATION_MODEL=<valid-model-id>
   ```
   Use `--update-env-vars`, never `--set-env-vars`.

2. **S2 end-to-end test** — with model fallback in place, run a real building conversation and confirm step advancement fires. Check Cloud Run logs for `[evaluate_success_state]` warning lines to see if fallback is being used. If it is, that confirms the env var needs updating.

3. **DASHSCOPE_API_KEY** — pending Alibaba enterprise verification at `myaccount.console.alibabacloud.com`. Same `--update-env-vars` command when approved.

4. **GitHub MCP (PAT)** — Lee needs to generate PAT at `github.com/settings/tokens` (scopes: `repo`, `read:org`), then add config to `~/.claude/claude_desktop_config.json`. Never in chat.

---

## Next Session Opens With

Run an S2 end-to-end test: open a building in studio.html, complete a step's success condition in conversation, confirm the orchestrator dict in the response shows `step_advanced: true` and the step number increments. Check Cloud Run logs for `[evaluate_success_state]` entries. If fallback is firing on every call, fix the `FY_ORCHESTRATION_MODEL` env var as described above.
