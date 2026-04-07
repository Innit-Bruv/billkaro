"""WhatsApp Cloud API adapter — webhook + Graph API v21.0."""

import logging

import httpx
from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse

from config import get_settings
from engine.invoice_flow import handle_message
from models.invoice import IncomingMessage, MessageType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["whatsapp"])

GRAPH_API = "https://graph.facebook.com/v21.0"


@router.get("")
async def verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """WhatsApp webhook verification (GET)."""
    settings = get_settings()
    if hub_mode == "subscribe" and hub_token == settings.whatsapp_verify_token:
        return PlainTextResponse(hub_challenge)
    return PlainTextResponse("Forbidden", status_code=403)


@router.post("")
async def receive(request: Request):
    """Handle incoming WhatsApp messages."""
    body = await request.json()

    # Extract message from webhook payload
    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        message = value["messages"][0]
        sender = message["from"]
    except (KeyError, IndexError):
        return {"status": "no message"}

    msg_type = message.get("type", "")

    if msg_type == "text":
        incoming = IncomingMessage(
            session_id=sender,
            type=MessageType.TEXT,
            text=message["text"]["body"],
        )
    elif msg_type == "audio":
        audio_data = await _download_media(message["audio"]["id"])
        incoming = IncomingMessage(
            session_id=sender,
            type=MessageType.VOICE,
            audio_data=audio_data,
        )
    elif msg_type == "interactive":
        button_reply = message.get("interactive", {}).get("button_reply", {})
        incoming = IncomingMessage(
            session_id=sender,
            type=MessageType.BUTTON,
            button_payload=button_reply.get("id", ""),
        )
    else:
        incoming = IncomingMessage(
            session_id=sender,
            type=MessageType.TEXT,
            text=f"[Unsupported message type: {msg_type}]",
        )

    response = await handle_message(incoming)
    await _send_whatsapp_message(sender, response)

    return {"status": "ok"}


async def _download_media(media_id: str) -> bytes:
    """Download media from WhatsApp Cloud API."""
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.whatsapp_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        # Step 1: Get media URL
        resp = await client.get(f"{GRAPH_API}/{media_id}", headers=headers)
        resp.raise_for_status()
        media_url = resp.json()["url"]

        # Step 2: Download the media
        resp = await client.get(media_url, headers=headers)
        resp.raise_for_status()
        return resp.content


async def _send_whatsapp_message(to: str, response) -> None:
    """Send a response back via WhatsApp Cloud API."""
    settings = get_settings()
    if not settings.whatsapp_token:
        logger.warning("WhatsApp token not configured, skipping send")
        return

    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    url = f"{GRAPH_API}/{settings.whatsapp_phone_number_id}/messages"

    async with httpx.AsyncClient(timeout=30) as client:
        # Send text message
        if response.buttons:
            # Interactive buttons message
            buttons = [
                {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                for b in response.buttons[:3]  # WhatsApp max 3 buttons
            ]
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": response.text[:1024]},
                    "action": {"buttons": buttons},
                },
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": response.text},
            }

        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.error("WhatsApp send failed: %s", resp.text)

        # Send PDF if present
        if response.pdf_bytes:
            await _send_pdf(client, url, headers, to, response.pdf_bytes)


async def _send_pdf(client, url, headers, to, pdf_bytes):
    """Upload and send PDF document via WhatsApp."""
    settings = get_settings()
    upload_url = f"{GRAPH_API}/{settings.whatsapp_phone_number_id}/media"

    # Upload media
    resp = await client.post(
        upload_url,
        headers={"Authorization": headers["Authorization"]},
        files={"file": ("invoice.pdf", pdf_bytes, "application/pdf")},
        data={"messaging_product": "whatsapp"},
    )
    if resp.status_code != 200:
        logger.error("PDF upload failed: %s", resp.text)
        return

    media_id = resp.json().get("id")
    if not media_id:
        return

    # Send document message
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": "invoice.pdf",
            "caption": "Your GST invoice",
        },
    }
    await client.post(url, headers=headers, json=payload)
