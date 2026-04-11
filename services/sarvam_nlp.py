"""Sarvam-30B invoice field extraction via chat completions."""

import json
import logging

import httpx
from config import get_settings
from models.invoice import ExtractionResult, LineItem

logger = logging.getLogger(__name__)

_MULTILINGUAL_NOTE = """
Input may be in Hindi, English, Tamil, Malayalam, Bengali, Marathi, or a mix (e.g. Hinglish).
ALL JSON values MUST be returned in English / Latin script — this data is used to generate a
legal GST invoice that must be machine-readable by Indian tax authorities. Transliterate any
non-Latin buyer names to Latin script (e.g. रमेश ट्रेडर्स → "Ramesh Traders"). Translate item
descriptions to English (e.g. கપாસ → "Cotton", चावल → "Rice").
"""

EXTRACTION_PROMPT = f"""You are an invoice data extractor for Indian MSMEs. Extract invoice details from the user's message and return ONLY valid JSON — no markdown, no explanation.

Return format:
{{
  "buyer_name": "",
  "amount": 0,
  "items": [{{"description": "", "quantity": 0, "unit": "", "rate": 0}}],
  "gst_rate": 0,
  "buyer_gstin": "",
  "notes": ""
}}

Rules:
- If quantity and rate are given, compute amount = quantity * rate
- If only total amount is given and one item, set rate = amount / quantity
- gst_rate should be a number like 5, 12, 18, 28 (not a decimal)
- If a field is not mentioned, use empty string or 0
- buyer_gstin should be a 15-character alphanumeric string if mentioned, otherwise ""
- For unit, use common abbreviations: kg, pcs, ltr, m, box, etc.
{_MULTILINGUAL_NOTE}"""

FORWARDED_MSG_PROMPT = f"""You are an invoice data extractor. The user has forwarded several WhatsApp messages from a business negotiation. Extract the final agreed-upon invoice details from this conversation and return ONLY valid JSON.

Return format:
{{
  "buyer_name": "",
  "amount": 0,
  "items": [{{"description": "", "quantity": 0, "unit": "", "rate": 0}}],
  "gst_rate": 0,
  "buyer_gstin": "",
  "notes": ""
}}

Focus on the final agreed price/quantity, not earlier negotiation offers. If fields are unclear, use empty string or 0.
{_MULTILINGUAL_NOTE}"""


async def extract_invoice_fields(
    text: str, is_forwarded: bool = False
) -> ExtractionResult:
    """Use Sarvam-30B to extract structured invoice fields from text."""
    settings = get_settings()
    system_prompt = FORWARDED_MSG_PROMPT if is_forwarded else EXTRACTION_PROMPT

    payload = {
        "model": settings.sarvam_chat_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            settings.sarvam_chat_url,
            headers={
                "api-subscription-key": settings.sarvam_api_key,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        result = resp.json()

    message = result["choices"][0]["message"]
    raw = message.get("content") or ""

    # Sarvam-30b is a reasoning model — if content is empty, try reasoning_content
    if not raw.strip():
        reasoning = message.get("reasoning_content", "")
        # Try to find JSON in the reasoning output
        raw = _extract_json_from_reasoning(reasoning)

    if not raw.strip():
        logger.warning("Sarvam returned empty content and no parseable JSON in reasoning")
        return ExtractionResult()

    return _parse_extraction(raw)


def _extract_json_from_reasoning(reasoning: str) -> str:
    """Try to extract a JSON block from reasoning_content (fallback for reasoning models)."""
    import re
    # Look for JSON code blocks
    match = re.search(r"```json?\s*\n(\{.*?\})\s*\n```", reasoning, re.DOTALL)
    if match:
        return match.group(1)
    # Look for any JSON object with buyer_name key
    match = re.search(r"\{[^{}]*\"buyer_name\"[^{}]*\}", reasoning, re.DOTALL)
    if match:
        return match.group(0)
    return ""


def _parse_extraction(raw: str) -> ExtractionResult:
    """Parse LLM output into ExtractionResult with fallback handling."""
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON output: %s", raw[:200])
        return ExtractionResult()

    # Build items list
    items = []
    for item_data in data.get("items", []):
        try:
            items.append(LineItem(
                description=str(item_data.get("description", "")),
                quantity=float(item_data.get("quantity", 0)),
                unit=str(item_data.get("unit", "pcs")),
                rate=float(item_data.get("rate", 0)),
            ))
        except (ValueError, TypeError):
            continue

    return ExtractionResult(
        buyer_name=str(data.get("buyer_name", "")),
        amount=data.get("amount"),
        items=items,
        gst_rate=data.get("gst_rate"),
        buyer_gstin=str(data.get("buyer_gstin", "")),
        notes=str(data.get("notes", "")),
    )
