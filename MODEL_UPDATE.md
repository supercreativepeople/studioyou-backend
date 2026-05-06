# UPDATED main.py — Model Change Only

**Change Made**: Line 694
- FROM: `model="claude-sonnet-4-20250514"`
- TO: `model="claude-opus-4-1"`

**Reason**: Your new API key doesn't support claude-sonnet-4-20250514. Using claude-opus-4-1 which is available on all Anthropic API tiers.

**File Size**: 31KB, 729 lines (same as before, only model string changed)

**Instructions**:
1. Download **main.py** from outputs
2. Replace `/Users/supercreativepeople/Projects/studioyou-backend/main.py`
3. Commit: `git add main.py && git commit -m "Phase 10.12: Change model to claude-opus-4-1"`
4. Push: `git push origin main`
5. Deploy to Cloud Run
6. Test https://studioyou.app

**Verification** (after download):
- Line 696 should read: `model="claude-opus-4-1",`
- That's the only change from previous version

