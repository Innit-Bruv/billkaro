# TODOS

## /health endpoint
Add a simple health check endpoint to `main.py`.

**What:** `GET /health` returns `{"status": "ok", "sessions": N, "sarvam_configured": bool}`
**Why:** Enables UptimeRobot pinger to keep the Render instance warm; required by the test plan.
**Pros:** 3 lines of code, prevents cold start delays during demo.
**Cons:** None.
**Context:** The test plan (generated 2026-04-04) explicitly calls for this. Render free tier spins down after 15 min of inactivity — a pinger keeps it alive.
**Depends on:** Nothing.
