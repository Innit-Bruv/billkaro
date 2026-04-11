"""Seller profile persistence — Supabase-backed, falls back to local JSON if not configured."""

import json
import logging
import os
import pathlib
from typing import Optional

from models.invoice import SellerProfile

logger = logging.getLogger(__name__)

# --- Supabase client (lazy-initialised) ---

_supabase = None


def _get_client():
    global _supabase
    if _supabase is not None:
        return _supabase
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if url and key:
        try:
            from supabase import create_client
            _supabase = create_client(url, key)
            return _supabase
        except Exception as e:
            logger.warning("Supabase init failed, falling back to file store: %s", e)
    return None


# --- File-based fallback ---

_PATH = pathlib.Path(os.environ.get("SELLER_PROFILES_PATH", "data/sellers.json"))


def _file_load(session_id: str) -> Optional[SellerProfile]:
    try:
        data = json.loads(_PATH.read_text())
        raw = data.get(session_id)
        return SellerProfile(**raw) if raw else None
    except Exception:
        return None


def _file_save(session_id: str, profile: SellerProfile) -> None:
    try:
        data = json.loads(_PATH.read_text()) if _PATH.exists() else {}
    except Exception:
        data = {}
    data[session_id] = profile.model_dump()
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, _PATH)


def _file_delete(session_id: str) -> None:
    try:
        data = json.loads(_PATH.read_text()) if _PATH.exists() else {}
    except Exception:
        return
    data.pop(session_id, None)
    tmp = _PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, _PATH)


# --- Public API ---

def load(session_id: str) -> Optional[SellerProfile]:
    """Return SellerProfile for session_id, or None if not found."""
    client = _get_client()
    if client:
        try:
            result = (
                client.table("seller_profiles")
                .select("name,gstin,preferred_language")
                .eq("session_id", session_id)
                .execute()
            )
            if result.data:
                return SellerProfile(**result.data[0])
        except Exception as e:
            logger.warning("Supabase load failed, trying file fallback: %s", e)
    return _file_load(session_id)


def save(session_id: str, profile: SellerProfile) -> None:
    """Upsert seller profile."""
    client = _get_client()
    if client:
        try:
            client.table("seller_profiles").upsert({
                "session_id": session_id,
                "name": profile.name,
                "gstin": profile.gstin,
                "preferred_language": profile.preferred_language,
            }).execute()
            return
        except Exception as e:
            logger.warning("Supabase save failed, falling back to file: %s", e)
    _file_save(session_id, profile)


def delete(session_id: str) -> None:
    """Delete seller profile."""
    client = _get_client()
    if client:
        try:
            client.table("seller_profiles").delete().eq("session_id", session_id).execute()
            return
        except Exception as e:
            logger.warning("Supabase delete failed, falling back to file: %s", e)
    _file_delete(session_id)
