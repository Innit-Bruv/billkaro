# TODOS

---

## P1 — Send Invoice to Buyer via WhatsApp
**What:** After confirming an invoice, bot asks "Want to send this to Ramesh directly?" — seller taps Yes and BillKaro WhatsApps the PDF to the buyer's number.
**Why:** Closes the entire loop inside WhatsApp. Right now seller has to manually download and forward. This is the feature that makes the narrative complete: negotiate → invoice → deliver, never leave WhatsApp.
**Pros:** The "wow" moment for the demo. Makes BillKaro a delivery tool, not just a generation tool.
**Cons:** Requires seller to know buyer's WhatsApp number. Need to store buyer phone numbers in buyer profiles.
**Context:** Buyer must be a registered WhatsApp user. WhatsApp Cloud API supports sending documents to any number. Buyer profiles (when built) should include phone number field.
**Effort:** M (human: ~3 days / CC: ~30 min)
**Priority:** P1 — build before buyer profiles
**Depends on:** Buyer profiles (for storing buyer phone numbers)

---

## P1 — Buyer Profiles / Address Book
**What:** Bot remembers buyer details (name, GSTIN, phone number) across invoices. Second invoice for "Ramesh Traders" auto-fills his GSTIN without asking.
**Why:** MSME sellers invoice the same 5-10 buyers repeatedly. Asking for GSTIN every time breaks the 60-second promise.
**Pros:** Zero friction — profiles built automatically as invoices are confirmed. Existing `lookup_gstin()` pattern already in place.
**Cons:** Need fuzzy name matching ("Ramesh" should match "Ramesh Traders Pvt Ltd").
**Context:** Save on invoice confirmation. Supabase `buyer_profiles(seller_id, name, gstin, phone, created_at)`. Load when buyer name mentioned in new invoice.
**Effort:** M (human: ~2 days / CC: ~20 min)
**Priority:** P1
**Depends on:** Supabase (already set up)

---

## P1 — Invoice History
**What:** Seller can say "show my invoices" or "last invoice for Ramesh" → bot lists recent invoices with amounts and dates.
**Why:** Once a PDF is generated it's gone. No way to retrieve, resend, or track. Makes BillKaro feel like a one-shot tool instead of a business tool.
**Pros:** Massive for usability. Enables resend, dispute resolution, month-end reconciliation.
**Cons:** Requires storing invoices in Supabase (currently in-memory only).
**Context:** Store invoice metadata (number, buyer, amount, date, PDF URL) on confirmation. Expose via "show invoices", "last 5 invoices", "invoices for [buyer name]" commands.
**Effort:** M (human: ~2 days / CC: ~20 min)
**Priority:** P1
**Depends on:** Supabase (already set up)

---

## P2 — HSN Code Auto-Suggest
**What:** When seller mentions "cotton" or "steel rods", bot suggests the correct HSN code for GST compliance.
**Why:** GST law requires HSN codes on invoices. Currently blank/optional. A real MSME seller will notice and won't trust the invoice for actual filing.
**Pros:** Makes invoices actually compliant. Sarvam-30B can be prompted to suggest HSN codes from item descriptions.
**Cons:** HSN database has thousands of codes — accuracy matters. Wrong HSN = tax compliance issue.
**Context:** Could be a Sarvam-30B prompt addition: include HSN suggestion in the extraction prompt. Show suggested HSN in draft for seller to confirm.
**Effort:** M (human: ~1 week / CC: ~30 min)
**Priority:** P2
**Depends on:** Nothing

---

## P2 — CRM / ERP Sync (Zoho, Tally stub)
**What:** After invoice is confirmed, push data to seller's CRM or accounting system (Zoho Books, Tally, etc.) via webhook or API.
**Why:** Turns BillKaro from a standalone tool into middleware — it sits between WhatsApp (where deals happen) and the backend system (where accounting lives). This is the platform play.
**Pros:** Huge for adoption — seller doesn't have to double-enter data. Makes BillKaro sticky.
**Cons:** Each integration is its own project. Zoho Books API is well-documented; Tally requires a local plugin.
**Context:** Start with Zoho Books (most common among Indian SMEs, REST API available). Offer as an optional webhook URL — seller configures it in setup. BillKaro POSTs invoice JSON after confirmation.
**Effort:** L per integration (human: ~1-2 weeks each / CC: ~1 hour each)
**Priority:** P2 — design the webhook interface now, implement integrations later
**Depends on:** Invoice history (need to store invoice data first)

---

## P3 — Payment Link After Invoice
**What:** After PDF is generated, bot sends a Razorpay/UPI payment link. Buyer can pay directly from the WhatsApp conversation.
**Why:** Closes the money loop. Invoice → payment in one thread. This is where BillKaro becomes a fintech product.
**Pros:** Massive value-add. Sellers get paid faster. BillKaro can take a transaction cut.
**Cons:** Requires Razorpay integration and KYC. Regulatory complexity for payment processing.
**Context:** Razorpay Payment Links API is straightforward. UPI deep links are even simpler for India. Could start with a static UPI ID configured during seller setup.
**Effort:** L (human: ~2 weeks / CC: ~1 hour)
**Priority:** P3 — startup territory, not demo territory
**Depends on:** Seller profile (need seller UPI/bank details)

---

## P3 — /health endpoint
Add a simple health check endpoint to `main.py`.

**What:** `GET /health` returns `{"status": "ok", "sessions": N, "sarvam_configured": bool}`
**Why:** Enables UptimeRobot pinger to keep the Render instance warm; required by the test plan.
**Pros:** 3 lines of code, prevents cold start delays during demo.
**Cons:** None.
**Context:** The test plan (generated 2026-04-04) explicitly calls for this. Render free tier spins down after 15 min of inactivity — a pinger keeps it alive.
**Depends on:** Nothing.
