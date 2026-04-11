"""Sarvam Saaras V3 Speech-to-Text service."""

import httpx
from config import get_settings


# Saaras returns codes like "hi-IN", "ta-IN" — map to our 2-char internal codes.
_SARVAM_LANG_MAP = {
    "hi": "hi",
    "en": "en",
    "ta": "ta",
    "ml": "ml",
    "bn": "bn",
    "mr": "mr",
}


def _normalise_lang(code: str) -> str | None:
    """Convert Sarvam's ``hi-IN`` style code to our internal 2-char code."""
    if not code:
        return None
    prefix = code.split("-", 1)[0].lower()
    return _SARVAM_LANG_MAP.get(prefix)


async def transcribe_audio(
    audio_data: bytes, filename: str = "audio.webm"
) -> tuple[str, str | None]:
    """Send audio to Sarvam Saaras V3 STT.

    Returns ``(transcript, detected_language_code)`` where the language code
    is one of ``en/hi/ta/ml/bn/mr`` or ``None`` if unsupported/undetected.
    """
    settings = get_settings()

    # Determine MIME type from filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webm"
    mime_map = {
        "webm": "audio/webm",
        "ogg": "audio/ogg",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "mp4": "audio/mp4",
        "aac": "audio/aac",
        "flac": "audio/flac",
    }
    mime = mime_map.get(ext, "audio/webm")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            settings.sarvam_stt_url,
            headers={"api-subscription-key": settings.sarvam_api_key},
            files={"file": (filename, audio_data, mime)},
            data={
                "model": settings.sarvam_stt_model,
                "language_code": "unknown",
                "with_timestamps": "false",
            },
        )
        resp.raise_for_status()
        result = resp.json()

    transcript = result.get("transcript", "")
    detected = _normalise_lang(result.get("language_code") or "")
    return transcript, detected
