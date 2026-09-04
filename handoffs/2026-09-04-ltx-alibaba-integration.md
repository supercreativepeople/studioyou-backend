# Handoff — 2026-09-04 — LTX + Alibaba Tool Wiring

## Session
Date: 2026-09-04
Repos touched: studioyou-backend
Commits: c8cc2d1 (main.py — 7 new tool endpoints), CLAUDE.md update (this session)

---

## What Was Done

### 1. formation_briefing bug — CLOSED (stale handoff)
Prior handoff said `client.messages.create` bug was "pre-existing, still not fixed." Code audit 2026-09-04 found all 8 call sites in `main.py` already use `anthropic_client.messages.create`. Bug was fixed in a prior session. Handoff was stale. No action needed.

### 2. LTX Studio integration — DEPLOYED, pending key activation
7 new endpoints added to `main.py` and deployed to Cloud Run at commit `c8cc2d1`:

- `POST /api/tools/ltx/text-to-video` — ltx-2-5-pro, prompt + dims + num_frames + seed
- `POST /api/tools/ltx/image-to-video` — ltx-2-5-pro, image_url (required public URL) + prompt
- `GET /api/tools/ltx/job-status?job_id=xxx` — poll for completion
- `POST /api/tools/qwen/chat` — Qwen LLM via OpenAI-compat endpoint (qwen-max default)
- `POST /api/tools/wan/text-to-video` — WAN 3.0 async, returns task_id
- `GET /api/tools/wan/task-status?task_id=xxx` — status: PENDING | RUNNING | SUCCEEDED | FAILED

All endpoints: session-gated via `validate_session()`, return 503 with human-readable message when key env var is empty. Activate by adding keys to Cloud Run — no redeploy needed.

### 3. Env vars added to main.py
```python
LTX_API_KEY        = os.environ.get("LTX_API_KEY", "")
DASHSCOPE_API_KEY  = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
```

### 4. CLAUDE.md updated
- Backend HEAD updated to c8cc2d1
- LTX Studio + Alibaba DashScope added to Services table
- formation_briefing bug closed
- New locked decision for 503 pattern on absent keys

---

## What's Blocked / Pending

| Item | Status | Next action |
|---|---|---|
| LTX activation | Key in hand (Lee has it) | `gcloud run services update studioyou-api --region us-east1 --project neat-tangent-474222-m9 --update-env-vars LTX_API_KEY=<value>` via Desktop Commander. Use `--update-env-vars` only. |
| Alibaba DashScope activation | Enterprise identity verification submitted, not yet confirmed | When Alibaba confirms: generate key at modelstudio.console.alibabacloud.com/ap-southeast-1, add as `DASHSCOPE_API_KEY` to Cloud Run same way |
| Alibaba free trial access | Unknown — depends on whether verification must complete first | Check modelstudio.console.alibabacloud.com/ap-southeast-1 after verification confirms |
| S2 orchestrator | Not started | Top build priority after tool wiring sprint. Requires sprint architecture session. |
| build_fy_system_prompt() completeness | arsenal/roadblock/creator_type not reliably in top-level Supabase columns | FY prompt falls back to minimal — needs dedicated fix session |
| Supabase RLS permissive policies | Waiting for JWT/direct Supabase client path | Blocked on implementation decision |

---

## Files Changed
- `main.py` — 431 insertions (7 new endpoints + 3 env vars + 2 helpers)
- `CLAUDE.md` — updated changelog, live state, services, locked decisions
- `SESSION_LOG.md` — checkpoint entries

---

## Git State at Close
- studioyou-backend: clean, HEAD `c8cc2d1` (CLAUDE.md commit follows this handoff)
- studioyou-fy-agent: untouched this session
- studioyou-app: untouched this session

---

## Open Items / Carry-Forward
1. Add LTX_API_KEY to Cloud Run — Lee has the key
2. Alibaba enterprise verification — await confirmation, then generate key
3. S2 orchestrator build — next major sprint
4. WAN 3.0 note: uses different async base URL pattern (`/api/v1/services/aigc/video-generation/video-synthesis`) vs. Qwen OpenAI-compat — documented in code

---

## Next Session Opens With
"StudioYou alpha — LTX key is in Cloud Run. Check LTX activation by hitting `/api/tools/ltx/text-to-video` with a test prompt. If Alibaba verification confirmed, add DASHSCOPE_API_KEY same way. Then: S2 orchestrator architecture."
