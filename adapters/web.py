"""Web chat adapter — JSON in/out for the browser-based demo UI."""

import base64
import logging

from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse

from engine.invoice_flow import handle_message
from models.invoice import IncomingMessage, MessageType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["web"])


@router.post("/chat")
async def chat(session_id: str = Form(...), text: str = Form(""), button: str = Form("")):
    """Handle text or button input from web chat."""
    if button:
        msg = IncomingMessage(
            session_id=session_id,
            type=MessageType.BUTTON,
            button_payload=button,
        )
    else:
        msg = IncomingMessage(
            session_id=session_id,
            type=MessageType.TEXT,
            text=text,
        )

    response = await handle_message(msg)

    return JSONResponse({
        "text": response.text,
        "pdf": base64.b64encode(response.pdf_bytes).decode() if response.pdf_bytes else None,
        "buttons": response.buttons,
    })


@router.post("/voice")
async def voice(session_id: str = Form(...), audio: UploadFile = File(...)):
    """Handle voice input from web chat (MediaRecorder blob)."""
    audio_data = await audio.read()
    filename = audio.filename or "audio.webm"

    msg = IncomingMessage(
        session_id=session_id,
        type=MessageType.VOICE,
        audio_data=audio_data,
        audio_filename=filename,
    )

    response = await handle_message(msg)

    return JSONResponse({
        "text": response.text,
        "pdf": base64.b64encode(response.pdf_bytes).decode() if response.pdf_bytes else None,
        "buttons": response.buttons,
    })
