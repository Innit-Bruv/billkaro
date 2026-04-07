"""Invoice flow state machine.

States: IDLE → EXTRACTING → AWAITING_FIELDS → CONFIRMING → GENERATING → DONE

The engine is adapter-agnostic: it takes an IncomingMessage and returns a BotResponse.
"""

import logging
from datetime import datetime

from models.invoice import (
    BotResponse,
    ExtractionResult,
    FlowState,
    IncomingMessage,
    Invoice,
    MessageType,
    Session,
)
from services.demo_safety_net import get_cached_extraction
from services.gstin_lookup import lookup_gstin
from services.pdf_generator import generate_invoice_number, generate_invoice_pdf
from services.sarvam_nlp import extract_invoice_fields
from services.sarvam_stt import transcribe_audio

logger = logging.getLogger(__name__)

# In-memory session store (replaced by DB in production)
_sessions: dict[str, Session] = {}


def get_session(session_id: str) -> Session:
    if session_id not in _sessions:
        _sessions[session_id] = Session(session_id=session_id)
    return _sessions[session_id]


def reset_session(session_id: str) -> Session:
    _sessions[session_id] = Session(session_id=session_id)
    return _sessions[session_id]


async def handle_message(msg: IncomingMessage) -> BotResponse:
    """Main entry point — route message through the state machine."""
    session = get_session(msg.session_id)
    session.touch()

    # Handle reset command
    if msg.type == MessageType.TEXT and msg.text.strip().lower() in ("reset", "start over", "new", "cancel"):
        reset_session(msg.session_id)
        return BotResponse(text="Session reset. Send me a voice note or text to create a new invoice.")

    # Handle button responses
    if msg.type == MessageType.BUTTON:
        return await _handle_button(session, msg)

    # Route based on state
    if session.state in (FlowState.IDLE, FlowState.DONE):
        return await _handle_new_input(session, msg)
    elif session.state == FlowState.AWAITING_FIELDS:
        return await _handle_missing_field_response(session, msg)
    elif session.state == FlowState.CONFIRMING:
        # User sent text instead of button — treat as edit
        return await _handle_edit_text(session, msg)
    else:
        return BotResponse(text="Processing your previous request. Please wait...")


async def _handle_new_input(session: Session, msg: IncomingMessage) -> BotResponse:
    """Handle new invoice input (voice or text) from IDLE state."""
    session.state = FlowState.EXTRACTING
    session.touch()

    # Step 1: Get text from input
    text = ""
    if msg.type == MessageType.VOICE and msg.audio_data:
        try:
            text = await transcribe_audio(msg.audio_data, msg.audio_filename)
        except Exception as e:
            logger.error("STT failed: %s", e)
            text = ""
    elif msg.type == MessageType.TEXT:
        text = msg.text

    if not text:
        session.state = FlowState.IDLE
        return BotResponse(text="I couldn't understand that. Please send a voice note or text with invoice details.")

    # Step 2: Extract fields (with demo safety net)
    is_forwarded = _looks_like_forwarded(text)
    extraction = get_cached_extraction(text)
    if extraction is None:
        try:
            extraction = await extract_invoice_fields(text, is_forwarded=is_forwarded)
        except Exception as e:
            logger.error("NLP extraction failed: %s", e)
            extraction = ExtractionResult()

    # Step 3: Build invoice from extraction
    session.invoice = _build_invoice(extraction)

    # Step 4: Auto-lookup GSTIN
    if session.invoice.buyer_name and not session.invoice.buyer_gstin:
        gstin_info = await lookup_gstin(session.invoice.buyer_name)
        if gstin_info:
            session.invoice.buyer_gstin = gstin_info["gstin"]

    # Step 5: Check for missing required fields
    missing = _check_missing_fields(session.invoice)
    if missing:
        session.state = FlowState.AWAITING_FIELDS
        session.missing_fields = missing
        field = missing[0]
        return BotResponse(text=f"Almost there! I need a few more details.\n\nPlease provide the **{field}**:")

    # All fields present — show draft
    session.state = FlowState.CONFIRMING
    return _build_draft_response(session.invoice)


def _build_invoice(extraction: ExtractionResult) -> Invoice:
    """Convert ExtractionResult to Invoice."""
    inv = Invoice(
        buyer_name=extraction.buyer_name,
        buyer_gstin=extraction.buyer_gstin,
        items=extraction.items,
        gst_rate=extraction.gst_rate or 0,
        notes=extraction.notes,
        date=datetime.now().strftime("%Y-%m-%d"),
    )
    # If amount given but no items, create a single line item
    if extraction.amount and not extraction.items:
        from models.invoice import LineItem
        inv.items = [LineItem(description="Goods/Services", quantity=1, unit="lot", rate=extraction.amount)]
    return inv


def _check_missing_fields(invoice: Invoice) -> list[str]:
    """Return list of missing required field names."""
    missing = []
    if not invoice.buyer_name:
        missing.append("buyer name")
    if not invoice.items:
        missing.append("item details (description, quantity, rate)")
    if not invoice.gst_rate:
        missing.append("GST rate (enter 5, 12, 18, or 28)")
    return missing


async def _handle_missing_field_response(session: Session, msg: IncomingMessage) -> BotResponse:
    """Handle user's response to a missing field prompt."""
    if not session.missing_fields:
        session.state = FlowState.CONFIRMING
        return _build_draft_response(session.invoice)

    field = session.missing_fields[0]
    text = msg.text.strip()

    if "buyer" in field.lower() or "name" in field.lower():
        session.invoice.buyer_name = text
        # Try GSTIN lookup
        gstin_info = await lookup_gstin(text)
        if gstin_info:
            session.invoice.buyer_gstin = gstin_info["gstin"]
    elif "gst" in field.lower():
        # Parse GST rate from plain number or "12%" etc.
        import re
        match = re.search(r"\d+", text)
        if match:
            session.invoice.gst_rate = float(match.group())
    elif "item" in field.lower():
        # Try to extract items from the response
        try:
            extraction = await extract_invoice_fields(text)
            if extraction.items:
                session.invoice.items = extraction.items
                if extraction.gst_rate:
                    session.invoice.gst_rate = extraction.gst_rate
        except Exception:
            from models.invoice import LineItem
            session.invoice.items = [LineItem(description=text, quantity=1, unit="lot", rate=0)]

    session.missing_fields.pop(0)

    # Check if more fields are missing
    remaining = _check_missing_fields(session.invoice)
    if remaining:
        session.missing_fields = remaining
        field = remaining[0]
        return BotResponse(text=f"Got it. Now please provide the **{field}**:")

    session.state = FlowState.CONFIRMING
    return _build_draft_response(session.invoice)


async def _handle_button(session: Session, msg: IncomingMessage) -> BotResponse:
    """Handle button press (Confirm / Edit)."""
    payload = msg.button_payload.lower()

    if payload == "confirm" and session.state == FlowState.CONFIRMING:
        return await _generate_invoice(session)
    elif payload == "edit":
        session.state = FlowState.IDLE
        return BotResponse(text="No problem. Send me the updated details and I'll create a new draft.")
    elif payload == "new":
        reset_session(msg.session_id)
        return BotResponse(text="Ready for a new invoice. Send me details via voice or text.")
    else:
        return BotResponse(text="Please confirm or edit the current draft.")


async def _handle_edit_text(session: Session, msg: IncomingMessage) -> BotResponse:
    """User sent text while in CONFIRMING state — re-extract and show new draft."""
    session.state = FlowState.IDLE
    return await _handle_new_input(session, msg)


async def _generate_invoice(session: Session) -> BotResponse:
    """Generate the final PDF."""
    from config import get_settings
    session.state = FlowState.GENERATING
    session.touch()

    invoice = session.invoice
    invoice.invoice_number = generate_invoice_number()

    settings = get_settings()
    if not invoice.seller_name:
        invoice.seller_name = settings.seller_name
    if not invoice.seller_gstin:
        invoice.seller_gstin = settings.seller_gstin

    try:
        pdf_bytes = generate_invoice_pdf(invoice)
    except Exception as e:
        logger.error("PDF generation failed: %s", e)
        session.state = FlowState.CONFIRMING
        return BotResponse(text="Failed to generate PDF. Please try confirming again.")

    session.state = FlowState.DONE
    session.touch()

    return BotResponse(
        text=f"Invoice **{invoice.invoice_number}** generated for **{invoice.buyer_name}**.\nTotal: Rs. {invoice.total:,.2f} (incl. {invoice.gst_rate}% GST)",
        pdf_bytes=pdf_bytes,
        buttons=[{"id": "new", "title": "New Invoice"}],
    )


def _looks_like_forwarded(text: str) -> bool:
    """Detect if text looks like forwarded WhatsApp messages (multiple speakers)."""
    import re
    lines = text.strip().split("\n")
    if len(lines) < 3:
        return False
    # Look for patterns like "Name:" or "[Name]" at line starts
    speaker_pattern = re.compile(r"^[\[\s]*\w[\w\s]{0,20}[\]:]")
    matches = sum(1 for line in lines if speaker_pattern.match(line.strip()))
    return matches >= 2


def _build_draft_response(invoice: Invoice) -> BotResponse:
    """Build the draft confirmation message."""
    items_text = ""
    for item in invoice.items:
        items_text += f"  - {item.description} | {item.quantity:g} {item.unit} x Rs. {item.rate:,.0f} = Rs. {item.amount:,.2f}\n"

    draft = f"""**Invoice Draft**

**Buyer:** {invoice.buyer_name}
**GSTIN:** {invoice.buyer_gstin or 'Not provided'}

**Items:**
{items_text}
**Subtotal:** Rs. {invoice.subtotal:,.2f}
**GST ({invoice.gst_rate}%):** Rs. {invoice.gst_amount:,.2f}
**Total:** Rs. {invoice.total:,.2f}"""

    return BotResponse(
        text=draft,
        buttons=[
            {"id": "confirm", "title": "Confirm"},
            {"id": "edit", "title": "Edit"},
        ],
    )
