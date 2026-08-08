# SERVICES.md - StudioYou Backend

Every external platform/service this project depends on. Update at session close whenever something changes. Credentials are NEVER stored here, pointer only. Mirrored into the cross-project Notion Platform & Service Registry (`https://app.notion.com/p/dd60c5c5ccda496eb10d58f8db0bc8b6`) at session close per the `dev-session-protocol` skill; that Notion database is the cross-project view, this file is the source of truth for this repo specifically.

Rows marked "(shared)" are used across the StudioYou family — see `studioyou-fy-agent`'s and `studioyou-app`'s own `SERVICES.md` for their repo-specific rows.

| Service | Category | Purpose | Account / Org ID | Console URL | Subscription / Tier | Renewal | Credential Location | Status | Last Verified |
|---|---|---|---|---|---|---|---|---|---|
| GitHub - studioyou-backend | Other | Source code, CLAUDE.md, handoffs/ | github.com/supercreativepeople | https://github.com/supercreativepeople/studioyou-backend | free | n/a | git credential helper (osxkeychain, remote URL de-tokenized 2026-08-07) | Active | 2026-08-07 |
| Cloud Run - studioyou-api | Hosting | Backend API (main.py) | neat-tangent-474222-m9, us-east1 | console.cloud.google.com/run | pay-as-you-go | n/a | Cloud Run env vars, set via GitHub Actions from GitHub Secrets | Active | not independently re-verified 2026-08-07 |
| GitHub Actions (shared) | CI/CD | Push to main → build Docker → push GCR → deploy Cloud Run | supercreativepeople/studioyou-backend | github.com/supercreativepeople/studioyou-backend/actions | free | n/a | GitHub Secrets | Active | not independently re-verified 2026-08-07 |
| Supabase (shared) | Storage/Database | `fy_vault_entries` table (creator answer capture) | unconfirmed project ref | app.supabase.com | unconfirmed | n/a | .env / Cloud Run env vars | Active | not independently re-verified 2026-08-07 |
| Netlify - studioyou.app | Distribution/Deploy | Frontend host (studioyou-app repo) | app.netlify.com | app.netlify.com | unconfirmed tier | n/a | Netlify login | Active | not independently re-verified 2026-08-07 |
| Anthropic API (shared) | AI/API | Claude (Fable 5) — session logic, chat | console.anthropic.com | console.anthropic.com | pay-as-you-go | n/a | ANTHROPIC_API_KEY in Cloud Run env | Active | not independently re-verified 2026-08-07 |
| Tavus | AI/API | Legacy avatar provider — env vars (TAVUS_*) still present but unused as of Session AA; superseded by Runway (see studioyou-fy-agent) | tavusapi.com | tavusapi.com | unconfirmed | n/a | .env (unused, not cleaned up) | Needs Verification | 2026-08-07 |
| Notion (shared) | Other | Session handoffs, sprint tracker, product docs | app.notion.com | https://www.notion.so/a5ff3efa50c24545b07eb1a7c6763438 (Sprint Tracker) | workspace plan | n/a | Notion login | Active | not independently re-verified 2026-08-07 |

Note (2026-08-07): existing `CLAUDE.md` in this repo is long (~580 lines) and predates this protocol's "keep it under ~200 lines, push detail to handoffs/references" guidance. Not restructured this session — flagged for a future session to split out.
