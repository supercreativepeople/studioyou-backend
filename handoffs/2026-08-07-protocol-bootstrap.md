# Session: dev-session-protocol bootstrap — 2026-08-07

## What happened

StudioYou brought onto the same `dev-session-protocol` skill SCREENBot uses, at Lee's request. This session covered all four StudioYou repos (studioyou-backend, studioyou-fy-agent, studioyou-app, studioyou-site).

For this repo (studioyou-backend) specifically:

- Renamed `claude.md` → `CLAUDE.md` (case only, git history preserved via git mv).
- Added a protocol-update banner at the top of `CLAUDE.md` flagging that the git copy (not a chat upload) is now the source of truth — the file's existing "never read the project copy, it's stale" instruction predates this and is now superseded.
- Added `handoffs/` (this file is the first entry), `SERVICES.md`, and `tools/check_repo_status.sh`.
- Fixed a security issue: the GitHub remote URL had a login token embedded directly in it instead of using the Mac's keychain. Switched to the clean `https://github.com/supercreativepeople/studioyou-backend.git` URL relying on the existing `osxkeychain` credential helper; confirmed working with a live `git fetch`.
- Working tree had a few stray untracked files (`.DS_Store`, `main.py.good`, `main.py.new`, `main.py.tavus`) — left untouched, not committed, flagged below as an open item since they look like experiment variants that need a human decision, not a blind commit.

## Open items for next session

- [ ] Decide what to do with `main.py.good` / `main.py.new` / `main.py.tavus` — commit, delete, or gitignore.
- [ ] This repo's `CLAUDE.md` is ~580 lines, above the protocol's ~200-line guidance — worth splitting older history into `handoffs/` entries over time.
- [ ] Confirm Supabase project ref and Netlify site/tier for `SERVICES.md` (currently unverified).
