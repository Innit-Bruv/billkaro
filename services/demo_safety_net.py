"""Demo safety net — cached responses for pre-seeded flows.

If Sarvam API fails during a live demo, these fallbacks kick in transparently.
"""

from models.invoice import ExtractionResult, LineItem

# Pre-seeded demo extractions keyed by partial text match
DEMO_EXTRACTIONS: dict[str, ExtractionResult] = {
    "ramesh traders": ExtractionResult(
        buyer_name="Ramesh Traders",
        amount=45000,
        items=[LineItem(description="Cotton", quantity=150, unit="kg", rate=300)],
        gst_rate=12,
        notes="Demo order — cotton supply",
    ),
    "kumar enterprises": ExtractionResult(
        buyer_name="Kumar Enterprises",
        amount=72000,
        items=[LineItem(description="Steel Rods", quantity=200, unit="kg", rate=360)],
        gst_rate=18,
        notes="Steel supply order",
    ),
    # Forwarded messages demo — triggers on "150kg cotton" + "300/kg" in conversation
    "300/kg": ExtractionResult(
        buyer_name="Ramesh Traders",
        amount=45000,
        items=[LineItem(description="Cotton", quantity=150, unit="kg", rate=300)],
        gst_rate=12,
        notes="Extracted from forwarded negotiation",
    ),
}


def get_cached_extraction(text: str) -> ExtractionResult | None:
    """Return a cached extraction if the text matches a demo scenario."""
    lower = text.lower()
    for trigger, result in DEMO_EXTRACTIONS.items():
        if trigger in lower:
            return result
    return None
