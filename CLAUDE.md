# FinanceAI — WhatsApp-Native GST Invoice Bot

## What this is
An interview demo project for a PM/strategy role at Sarvam AI. A WhatsApp bot (+ web chat demo) that lets MSME sellers generate GST-compliant invoices via voice note or text in under 60 seconds, powered by Sarvam's AI stack.

## Architecture
Dual Surface design: shared FastAPI backend with two thin message adapters (web chat + WhatsApp). Core engine is a conversation state machine (IDLE → EXTRACTING → AWAITING_FIELDS → CONFIRMING → GENERATING → DONE).

Key files:
- `engine/invoice_flow.py` — state machine, orchestrates services
- `adapters/web.py` and `adapters/whatsapp.py` — thin adapters
- `services/sarvam_stt.py` — Saaras V3 STT (REST)
- `services/sarvam_nlp.py` — Sarvam-30B extraction + Pydantic validation
- `services/pdf_generator.py` — reportlab/fpdf2 + mock IRN + QR
- `static/` — landing page + web chat UI (vanilla HTML/CSS/JS, dark mode WhatsApp theme)

## Tech stack
- Python 3.11+ / FastAPI
- Sarvam AI: Saaras V3 (STT), Sarvam-30B (NLP extraction)
- PostgreSQL via Supabase
- WhatsApp Cloud API v21.0 (via BSP sandbox)
- Render hosting + Dockerfile with ffmpeg

## Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Run tests with real Sarvam API (slow)
pytest tests/ -v -m slow
```

## Key design decisions
- **Adapter pattern**: single InvoiceFlow engine, two adapters (web + WhatsApp). Adding a new surface = new adapter only.
- **LLM output validation**: json.loads → Pydantic → retry with stricter prompt → manual fallback. Never trust LLM JSON output blindly.
- **Demo safety net**: pre-seeded audio samples have cached responses. If Sarvam API fails during demo, fallback is transparent.
- **Audio format**: browser sends whatever MediaRecorder supports (WebM/Opus on Chrome, MP4/AAC on Safari). Backend has ffmpeg for transcoding if needed.
- **Sessions**: client-side UUID in localStorage. No auth needed for demo.
- **Two extraction prompts**: single-message prompt for voice/text, dedicated conversation prompt for forwarded messages.

## Environment variables
See `.env.example` for the full list. Required: `SARVAM_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`.
