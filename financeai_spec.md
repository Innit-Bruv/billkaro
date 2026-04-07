# FinanceAI — WhatsApp-Native GST Invoice Bot
## Product Spec v0.1 (MVP / Interview Demo Build)

---

## 1. One-Line Description

A WhatsApp bot that lets an MSME seller generate a GST-compliant e-invoice in under 60 seconds — via voice note or text — without leaving WhatsApp.

---

## 2. Problem Statement

MSME sellers in India negotiate deals on WhatsApp daily. After the deal is agreed, they must:
- Switch to a separate app (Tally, Vyapar, Zoho, or call their CA)
- Manually enter all invoice fields
- Generate and download a PDF
- Come back to WhatsApp and send it

This is slow, friction-heavy, and often gets delayed — which delays payment and GST filing.

**The insight:** The deal happens on WhatsApp. The invoice should too.

---

## 3. Target User

**Primary:** Small MSME seller/supplier in India
- Turnover ₹50L–₹5Cr range (GST-registered, e-invoicing mandatory or imminent)
- Conducts B2B trade negotiations on WhatsApp
- Uses basic bookkeeping software or relies on a CA
- Comfortable with voice notes in Hinglish/regional language

**Not targeting (for MVP):** The buyer. Buyer just receives a PDF. No onboarding required from them.

---

## 4. Core User Flow (MVP)

```
[1] DEAL AGREED on WhatsApp (between seller and buyer, normal chat)

[2] Seller opens their FinanceAI WhatsApp contact
    → Forwards 5–10 key messages from the negotiation
    OR
    → Sends a voice note: "Ramesh Traders ka invoice banao, 150kg cotton, 
       45000 rupees, 12% GST"
    OR
    → Types: "Invoice Ramesh Traders 45000 150kg cotton 12% GST"

[3] FinanceAI parses input using Sarvam AI (STT + NLP)
    → Extracts: buyer name, amount, line items, GST rate, quantity

[4] Bot replies with a structured draft:
    ---
    📋 Invoice Draft
    Buyer: Ramesh Traders (GSTIN: auto-fetched or prompted)
    Item: Cotton — 150kg
    Rate: ₹300/kg | Amount: ₹45,000
    GST (12%): ₹5,400
    Total: ₹50,400
    ---
    [✅ Confirm] [✏️ Edit]

[5] Seller taps Confirm

[6] System:
    → Generates GST-compliant invoice PDF
    → Submits to IRP via GSP API → gets IRN + QR code
    → Updates seller's connected accounting software (Zoho Books / stub for demo)
    → Sends PDF to buyer via WhatsApp + email

[7] Seller gets confirmation:
    "✅ Invoice #INV-2025-041 sent to Ramesh Traders. IRN generated."
```

---

## 5. Tech Stack

### 5a. Core AI — Sarvam AI
- **Speech-to-Text (STT):** Sarvam's **Saaras V3** model — supports all 22 scheduled Indian languages + English, auto-detects language, handles code-mixed audio (Hinglish). Available via REST (files <30s), Batch (up to 1hr with diarization), and **Streaming WebSocket** (real-time transcription).
- **NLP / Intent Parsing:** **Sarvam-30B** (chat completions API) to extract structured invoice fields from messy voice/text input. Cost-efficient and more than capable for structured extraction. Sarvam-105B (flagship MoE model) available as fallback for ambiguous/complex inputs.
- **Text-to-Speech (optional):** Sarvam's **Bulbul V3** for voice confirmations — 35+ voices across 11 Indian languages (expanding to 22), pace and temperature control, 8kHz–48kHz output.
- **Document Vision (stretch):** **Sarvam Vision** — vision-language model for OCR and document understanding in Indian scripts. Enables image-based invoice extraction (e.g., seller photographs a handwritten order/challan).

**Why Sarvam:** Built for Indian languages, handles the Hinglish/regional language problem that generic Whisper/GPT-4 struggles with at scale. Sarvam-30B and 105B were open-sourced in Feb 2026, demonstrating strong commitment to the Indian AI ecosystem. Also a strong talking point for placement interviews given their IIT Bombay/India AI Mission positioning.

### 5b. WhatsApp Interface
- **WhatsApp Business Cloud API (Meta)** — official, fully supported (Graph API **v21.0**). On-premises API was deprecated Oct 2025; Cloud API is now the only supported architecture.
- Use a BSP (Business Solution Provider) like **Interakt** or **WATI** for easier onboarding during demo phase
- Message types used: Text messages, Button messages (Confirm/Edit), Document messages (PDF delivery)
- Webhooks for incoming message handling
- **Pricing note:** Since July 2025, Meta charges per delivered template message (no more flat 24-hour conversation fees). Factor this into cost projections.

### 5c. Backend
- **Language:** Python (FastAPI)
- **Hosting:** Railway / Render (fast to deploy, free tier available for demo)
- **Core services:**
  - Message router (classifies incoming as voice note / text / forwarded messages)
  - Sarvam Saaras V3 STT handler (REST + streaming WebSocket)
  - Invoice field extractor (Sarvam-30B chat completions)
  - Invoice PDF generator (use `reportlab` or `fpdf2`)
  - GST API handler (mock for MVP, real GSP integration as stretch goal)
  - Notification dispatcher (WhatsApp outbound + email via Resend/SendGrid)

### 5d. GST Integration
- **MVP/Demo:** Mock IRN generation — simulate the GSP response with a fake IRN and QR code. Functionally identical UX, no regulatory approval needed for demo.
- **Real integration (post-MVP):** Partner with a licensed GSP — ClearTax, Masters India, or IRIS Business. Use their sandbox APIs first.
- Fields required for a valid e-invoice: Seller GSTIN, Buyer GSTIN, Invoice number, Date, Line items (HSN code, quantity, rate, taxable value), GST rate + amount, Total

### 5e. Accounting Software Sync
- **MVP:** Zoho Books API (clean REST API, free sandbox, good docs)
- Stretch: Tally connector via TallyPrime REST API
- On invoice confirmation → POST to Zoho Books `/invoices` endpoint

### 5f. Data Storage
- **PostgreSQL** (via Supabase free tier)
- Tables: `sellers` (GSTIN, WhatsApp number, Zoho credentials), `invoices` (all invoice data, status, IRN), `messages` (raw incoming for audit trail)

---

## 6. MVP Scope (What to Actually Build)

### In Scope ✅
- WhatsApp bot onboarding flow (seller registers GSTIN + Zoho connection)
- Voice note → STT via Sarvam Saaras V3 → invoice field extraction via Sarvam-30B
- Text input → invoice field extraction
- Forwarded messages → invoice field extraction (parse as concatenated text)
- Invoice draft shown to seller with Confirm/Edit buttons
- GST-compliant invoice PDF generation (with mock IRN for demo)
- PDF delivery to seller on WhatsApp
- Buyer notification via WhatsApp (PDF + payment due message)
- Basic invoice log/history ("show my last 5 invoices")

### Out of Scope for MVP ❌
- Real GSP/IRP submission (use mock)
- Buyer onboarding or acceptance flow
- Real Zoho Books sync (show as stub / mock API call)
- Payment collection
- Multi-user / team accounts
- Invoice editing flow (just re-prompt for now)
- Analytics dashboard
- Image-based invoice extraction via Sarvam Vision (stretch goal for post-MVP)

---

## 7. Demo Flow for Interview

**Setup before interview:**
- Live WhatsApp number running the bot
- Pre-onboarded seller account with dummy GSTIN
- Sarvam Saaras V3 STT working for at least Hinglish voice input
- Mock IRN generation returning a real-looking IRN format (`<Year><GSTIN Hash><InvoiceHash>`)

**Demo script:**
1. Show the problem — "This is how MSMEs currently invoice" (show Tally UI, count the steps)
2. "Here's what I built" — send a voice note to the bot live
3. Bot replies with structured draft in ~5 seconds
4. Tap Confirm — PDF generated and sent
5. Show the PDF — GST-compliant format with IRN and QR code
6. "This is what gets sent to the buyer"

**Talking points for PM interview:**
- Why WhatsApp: where the deal happens, zero new app to download, 500M+ users in India
- Why voice: MSME owners in Tier 2/3 prefer voice notes, removes typing friction
- Why Sarvam: Indian language-first, handles Hinglish, aligns with India AI Mission. Saaras V3 beats Gemini and GPT-4o on Indian speech benchmarks.
- Market timing: e-invoicing threshold dropped to ₹2Cr, forcing more MSMEs into compliance
- What's next: invoice financing on top of the data asset (the real business). Sarvam Vision for image-based invoice extraction from handwritten orders.

---

## 8. Project Structure

```
financeai/
├── main.py                      # FastAPI app, CORS, route registration
├── adapters/
│   ├── base.py                  # MessageAdapter abstract class (parse_incoming, send_response)
│   ├── web.py                   # WebAdapter — JSON in/out for web chat UI
│   └── whatsapp.py              # WhatsAppAdapter — webhook + Graph API v21.0
├── engine/
│   └── invoice_flow.py          # InvoiceFlow state machine (IDLE→EXTRACTING→CONFIRMING→DONE)
├── services/
│   ├── sarvam_stt.py            # Saaras V3 STT (REST API)
│   ├── sarvam_nlp.py            # Sarvam-30B extraction + Pydantic validation + retry logic
│   ├── gstin_lookup.py          # GSTIN auto-lookup (API or hardcoded demo fallback)
│   ├── pdf_generator.py         # reportlab/fpdf2 + mock IRN + QR code
│   └── demo_safety_net.py       # Cached responses for pre-seeded demo flows
├── models/
│   └── invoice.py               # Pydantic models (Invoice, Session, Message, ExtractionResult)
├── db/
│   └── database.py              # Supabase/Postgres connection + queries
├── static/
│   ├── index.html               # Landing page (hero, before/after, pipeline diagram, CTA)
│   ├── chat.html                # Web chat UI (dark mode WhatsApp theme)
│   ├── style.css                # Dark mode WhatsApp color palette
│   └── app.js                   # MediaRecorder (dynamic format), chat logic, API calls
├── templates/
│   └── invoice_template.html    # Invoice PDF template
├── Dockerfile                   # Python + ffmpeg for audio transcoding
├── .env.example                 # Template for env vars (never commit .env)
├── requirements.txt
├── tests/
│   ├── test_invoice_flow.py     # State machine unit tests
│   ├── test_sarvam_stt.py       # STT service tests (mocked API)
│   ├── test_sarvam_nlp.py       # NLP extraction tests (mocked API)
│   ├── test_pdf_generator.py    # PDF generation tests
│   └── test_e2e.py              # End-to-end voice→PDF flow test
└── README.md
```

---

## 9. Environment Variables Needed

```
# WhatsApp
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=

# Sarvam AI
SARVAM_API_KEY=

# Database
SUPABASE_URL=
SUPABASE_KEY=

# Zoho (optional for MVP)
ZOHO_CLIENT_ID=
ZOHO_CLIENT_SECRET=
ZOHO_REFRESH_TOKEN=

# Email (optional)
RESEND_API_KEY=
```

---

## 10. Key API References

- Sarvam Saaras V3 STT (REST): `https://api.sarvam.ai/speech-to-text` — POST with audio file, returns transcript
- Sarvam Saaras V3 STT (Streaming): WebSocket endpoint for real-time transcription
- Sarvam Chat Completions: `https://api.sarvam.ai/chat/completions` — OpenAI-compatible, use `model="sarvam-30b"`
- Sarvam Translate (if needed): `https://api.sarvam.ai/translate`
- Sarvam Bulbul V3 TTS: `https://api.sarvam.ai/text-to-speech`
- WhatsApp Cloud API: `https://graph.facebook.com/v21.0/{phone-number-id}/messages`
- WhatsApp Webhook: Verify token + handle incoming `messages` events
- Zoho Books: `https://www.zohoapis.in/books/v3/invoices?organization_id={id}`
- IRN Format (mock): 64-char alphanumeric hash

---

## 11. Build Order (Suggested Sequence)

1. **WhatsApp webhook** — receive and log incoming messages (text + voice)
2. **Sarvam Saaras V3 STT** — transcribe voice notes to text (REST for short clips, streaming WebSocket for real-time)
3. **Invoice parser** — extract fields from raw text (Sarvam-30B chat completions with structured extraction prompt)
4. **Draft reply** — send structured draft back with Confirm button
5. **PDF generator** — produce GST-format invoice PDF on confirm
6. **Mock IRN** — simulate GSP response
7. **Outbound delivery** — send PDF to seller + buyer on WhatsApp
8. **Onboarding flow** — GSTIN registration, buyer address book
9. **Invoice history** — "show last 5 invoices" command
10. **Polish for demo** — error handling, edge cases, demo script

---

## 12. Sarvam-Specific Notes

### STT — Saaras V3
- Supports all 22 scheduled Indian languages + English
- Auto-detects spoken language, handles code-mixed (Hinglish) audio natively
- Audio formats: MP3, WAV, AAC, OGG, Opus, FLAC, M4A, AMR, WMA, WebM
- Modes: `transcribe`, `translate`, `verbatim`, `translit`, `codemix`
- For WhatsApp voice notes (typically OGG/Opus), use REST API for clips <30s or streaming WebSocket for real-time

### TTS — Bulbul V3
- 35+ voices, 11 languages (expanding to 22)
- Up to 2,500 chars per request, pace/temperature control
- Sample rates: 8kHz (telephony) to 48kHz (full band)

### Chat Completions — Sarvam-30B / 105B
- **Sarvam-30B** (`model="sarvam-30b"`) — recommended for invoice field extraction (cost-efficient)
- **Sarvam-105B** (`model="sarvam-105b"`) — flagship MoE model, use for complex/ambiguous inputs
- **Sarvam-M** (`model="sarvam-m"`) — legacy, do not use for new development
- Endpoint: `/chat/completions` (OpenAI-compatible format)
- Supports 10 Indic languages + English

### Invoice Parsing via Chat Completions

- Send the raw transcript to Sarvam-30B `/chat/completions` endpoint with a structured extraction prompt
- Prompt example:
```
Extract invoice details from this message and return JSON only:
"{transcript}"

Return format:
{
  "buyer_name": "",
  "amount": 0,
  "items": [{"description": "", "quantity": 0, "unit": "", "rate": 0}],
  "gst_rate": 0,
  "notes": ""
}
```
- Handle missing fields gracefully — bot should ask follow-up questions for any missing required field (GSTIN is the most commonly missing one)

---

*Spec version: 0.2 | Updated: April 2026 | Built for: PM/Generalist interview demo | Stack: Python + FastAPI + Sarvam AI (Saaras V3 + Sarvam-30B + Bulbul V3) + WhatsApp Cloud API v21.0*
