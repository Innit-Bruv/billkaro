"""GSTIN lookup — demo fallback with hardcoded entries."""

DEMO_GSTIN_DB: dict[str, dict] = {
    "ramesh traders": {
        "gstin": "27AABCU9603R1ZM",
        "legal_name": "Ramesh Traders Pvt Ltd",
        "state": "Maharashtra",
    },
    "kumar enterprises": {
        "gstin": "29AAGCK5148R1ZX",
        "legal_name": "Kumar Enterprises",
        "state": "Karnataka",
    },
    "patel distributors": {
        "gstin": "24AAACH7409R1ZW",
        "legal_name": "Patel Distributors LLP",
        "state": "Gujarat",
    },
}


async def lookup_gstin(buyer_name: str) -> dict | None:
    """Look up by buyer name. Returns dict with gstin, legal_name, state or None."""
    key = buyer_name.strip().lower()
    for name, info in DEMO_GSTIN_DB.items():
        if name in key or key in name:
            return info
    return None


async def lookup_by_gstin(gstin: str) -> dict | None:
    """Reverse lookup by GSTIN value. Returns dict with gstin, legal_name, state or None."""
    g = gstin.strip().upper()
    for info in DEMO_GSTIN_DB.values():
        if info["gstin"] == g:
            return info
    return None
