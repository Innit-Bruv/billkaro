# BillKaro — Cost Analysis

## Sarvam AI — What's Free

| Item | Details |
|---|---|
| **Signup credits** | **₹1,000 free** on signup. Works across all APIs. Never expires. |
| **Sarvam-M (24B) chat** | Free unlimited access (legacy model, but could work for extraction) |
| **OCR** | Free |

## Estimated Cost for This Demo Project

### Speech-to-Text (Saaras V3)
- Development: ~100 test calls x 15s avg = 1,500 seconds of audio
- Demo day: ~10-20 calls = ~300 seconds
- Total: ~1,800 seconds

### Chat Completions (Sarvam-30B)
- Development: ~200 extraction calls x ~200 tokens each = ~40K tokens
- Demo day: ~10-20 calls = ~4K tokens
- Total: ~44K tokens

### TTS (Bulbul V3) — stretch goal only
- ₹30 per 10K characters. Minimal if used at all.

With ₹1,000 free credits, all development and demo usage should be covered comfortably. The exact per-second/per-token rates aren't publicly listed, but ₹1,000 should cover hundreds of STT calls and thousands of NLP extraction calls based on comparable Indian AI platform pricing.

## Other Project Costs

| Service | Cost |
|---|---|
| **Render hosting** | Free tier (with UptimeRobot pinger) |
| **Supabase** | Free tier (500MB DB, 50K rows) |
| **UptimeRobot** | Free (50 monitors) |
| **WATI/Interakt** (WhatsApp BSP) | Free sandbox/trial for development |
| **Resend** (email) | Free tier (100 emails/day) |
| **Domain** (optional) | ~₹500-800/year for a `.in` domain |

## Total Expected Cost: ₹0 — ₹800

The entire project can likely be built within the ₹1,000 free Sarvam credits + free tiers of all other services. The only optional cost is a custom domain for the resume link (Render gives you a free `*.onrender.com` URL).

## Pro Tip: Apply for the Startup Program

Sarvam launched a Startup Program in March 2026 — 6-12 months of API credits + priority engineering support. Since you're building a product that showcases their stack, you're exactly the kind of builder they want. Even if you're applying for a job there, the "Powered by Sarvam" badge on your demo would be a nice touch. Apply on Day 1.

- Program: https://www.sarvam.ai/startup-program
- Includes: 6-12 months of credits, priority engineering support, co-branded launch amplification
- Requirement: Display "Powered by Sarvam" in product

## References

- Sarvam AI Pricing: https://www.sarvam.ai/api-pricing
- Sarvam AI Credits & Rate Limits: https://docs.sarvam.ai/api-reference-docs/getting-started/pricing
- Sarvam Startup Program: https://www.sarvam.ai/startup-program
