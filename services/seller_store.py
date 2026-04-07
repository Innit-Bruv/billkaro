"""Seller profile persistence — file-based store keyed by session_id / phone number."""

import json
import os
import pathlib
from typing import Optional

from models.invoice import SellerProfile

_PATH = pathlib.Path(os.environ.get("SELLER_PROFILES_PATH", "data/sellers.json"))


def load(session_id: str) -> Optional[SellerProfile]:
    """Return SellerProfile for session_id, or None if not found or file unreadable."""
    try:
        data = json.loads(_PATH.read_text())
        raw = data.get(session_id)
        return SellerProfile(**raw) if raw else None
    except Exception:
        return None  # missing or corrupt file → treat as no profile


def save(session_id: str, profile: SellerProfile) -> None:
    """Atomically merge profile into sellers.json."""
    try:
        data = json.loads(_PATH.read_text()) if _PATH.exists() else {}
    except Exception:
        data = {}
    data[session_id] = profile.model_dump()
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _PATH.with_suffix(".tmp")  # same filesystem as _PATH → os.replace() safe
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, _PATH)


def delete(session_id: str) -> None:
    """Remove a seller profile (called on 'reset' command)."""
    try:
        data = json.loads(_PATH.read_text()) if _PATH.exists() else {}
    except Exception:
        return
    data.pop(session_id, None)
    tmp = _PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, _PATH)
