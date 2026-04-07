"""Supabase/PostgreSQL database layer.

For the demo, sessions are in-memory (see engine/invoice_flow.py).
This module provides invoice persistence for history/audit.
"""

import logging
from typing import Optional

from config import get_settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        settings = get_settings()
        if settings.supabase_url and settings.supabase_key:
            try:
                from supabase import create_client
                _client = create_client(settings.supabase_url, settings.supabase_key)
            except Exception as e:
                logger.warning("Supabase unavailable, using in-memory fallback: %s", e)
    return _client


# In-memory fallback for when Supabase isn't configured
_invoice_store: list[dict] = []


async def save_invoice(invoice_data: dict) -> dict:
    """Save an invoice record. Returns the saved record."""
    client = _get_client()
    if client:
        try:
            result = client.table("invoices").insert(invoice_data).execute()
            return result.data[0] if result.data else invoice_data
        except Exception as e:
            logger.error("DB save failed: %s", e)

    # Fallback: in-memory
    _invoice_store.append(invoice_data)
    return invoice_data


async def get_invoices(session_id: str, limit: int = 5) -> list[dict]:
    """Get recent invoices for a session."""
    client = _get_client()
    if client:
        try:
            result = (
                client.table("invoices")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("DB query failed: %s", e)

    # Fallback
    return [inv for inv in _invoice_store if inv.get("session_id") == session_id][-limit:]
