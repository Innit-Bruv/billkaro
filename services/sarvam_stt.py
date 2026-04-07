"""Sarvam Saaras V3 Speech-to-Text service."""

import httpx
from config import get_settings


async def transcribe_audio(audio_data: bytes, filename: str = "audio.webm") -> str:
    """Send audio bytes to Sarvam Saaras V3 STT and return the transcript."""
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

    return result.get("transcript", "")
