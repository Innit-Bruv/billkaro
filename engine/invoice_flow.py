"""Invoice flow state machine.

States:
  Setup:   SETUP_GSTIN → SETUP_CONFIRM → IDLE
                       → SETUP_NAME    → IDLE
  Invoice: IDLE → EXTRACTING → AWAITING_FIELDS → CONFIRMING → GENERATING → DONE

The engine is adapter-agnostic: it takes an IncomingMessage and returns a BotResponse.
"""

import logging
import re
from datetime import datetime

from models.invoice import (
    BotResponse,
    ExtractionResult,
    FlowState,
    IncomingMessage,
    Invoice,
    MessageType,
    SellerProfile,
    Session,
)
from i18n.strings import LANG_NAMES, STRINGS, detect_script_language, t
from services.demo_safety_net import get_cached_extraction
from services.gstin_lookup import lookup_by_gstin, lookup_gstin
from services.pdf_generator import generate_invoice_number, generate_invoice_pdf
from services.sarvam_nlp import extract_invoice_fields
from services.sarvam_stt import transcribe_audio
import services.seller_store as seller_store


def _seller_lang(session: Session) -> str:
    """Active language code for bot responses. Defaults to English."""
    if session.seller_profile and session.seller_profile.preferred_language:
        return session.seller_profile.preferred_language
    return "en"

_GSTIN_RE = re.compile(r'^([0-2][0-9]|3[0-8])[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$')


def _is_valid_gstin(s: str) -> bool:
    return bool(_GSTIN_RE.match(s))

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

    # Load seller profile from disk if not yet in memory
    if session.seller_profile is None:
        loaded = seller_store.load(msg.session_id)
        if loaded:
            session.seller_profile = loaded

    # Handle reset command — clears both session and seller profile
    if msg.type == MessageType.TEXT and msg.text.strip().lower() in ("reset", "start over", "new", "cancel"):
        lang = _seller_lang(session)
        seller_store.delete(msg.session_id)
        reset_session(msg.session_id)
        return BotResponse(text=t("reset_ack", lang))

    # Handle "change language" command anytime after setup
    if (
        msg.type == MessageType.TEXT
        and session.seller_profile is not None
        and msg.text.strip().lower() in ("change language", "language", "भाषा", "மொழி", "ഭാഷ", "ভাষা")
    ):
        session.seller_profile.preferred_language = None
        seller_store.save(msg.session_id, session.seller_profile)
        return BotResponse(
            text="Which language would you like me to reply in?",
            buttons=[{"id": f"lang_set_{code}", "title": name} for code, name in LANG_NAMES.items()],
        )

    # First-time user: no seller profile → run setup flow
    if session.seller_profile is None:
        return await _handle_setup(session, msg)

    # Handle button responses (setup + language-confirm buttons route here too)
    if msg.type == MessageType.BUTTON:
        if msg.button_payload.startswith("setup_"):
            return await _handle_setup(session, msg)
        if msg.button_payload.startswith("lang_"):
            return await _handle_language_button(session, msg)
        return await _handle_button(session, msg)

    # Route based on invoice flow state
    if session.state == FlowState.AWAITING_LANGUAGE_CONFIRM:
        # Text sent instead of button — treat as implicit "keep detected lang"
        return await _confirm_pending_language(session, msg, accept=True)
    if session.state in (FlowState.IDLE, FlowState.DONE):
        return await _handle_new_input(session, msg)
    elif session.state == FlowState.AWAITING_FIELDS:
        return await _handle_missing_field_response(session, msg)
    elif session.state == FlowState.CONFIRMING:
        # User sent text instead of button — treat as edit
        return await _handle_edit_text(session, msg)
    else:
        return BotResponse(text=t("busy", _seller_lang(session)))


async def _handle_setup(session: Session, msg: IncomingMessage) -> BotResponse:
    """Drive the first-time seller onboarding flow."""

    # First message → begin setup
    if session.state == FlowState.IDLE:
        session.state = FlowState.SETUP_GSTIN
        return BotResponse(
            text="Welcome to BillKaro! 🎉 I'll help you create GST invoices in 60 seconds.\n\nFirst, what's your GSTIN?"
        )

    if session.state == FlowState.SETUP_GSTIN:
        gstin = msg.text.strip().upper()
        if not _is_valid_gstin(gstin):
            session.gstin_attempts += 1
            if session.gstin_attempts >= 3:
                session.state = FlowState.SETUP_NAME
                return BotResponse(text="No worries — let's skip the GSTIN for now. What's your business name?")
            return BotResponse(
                text="That doesn't look like a valid GSTIN (15 characters, e.g. 27AABCS1234R1ZV). Try again?"
            )

        session.pending_gstin = gstin
        gstin_info = await lookup_by_gstin(gstin)
        if gstin_info:
            session.pending_seller_name = gstin_info["legal_name"]
            session.state = FlowState.SETUP_CONFIRM
            return BotResponse(
                text=f"Found it! Is this you?\n🏢 {gstin_info['legal_name']}\n📍 {gstin_info['state']}",
                buttons=[
                    {"id": "setup_yes", "title": "Yes, that's me"},
                    {"id": "setup_no", "title": "No, enter manually"},
                ],
            )
        else:
            session.state = FlowState.SETUP_NAME
            return BotResponse(text="I couldn't find that GSTIN in my records. What's your business name?")

    if session.state == FlowState.SETUP_CONFIRM:
        if msg.type == MessageType.BUTTON and msg.button_payload == "setup_yes":
            return await _complete_setup(session, msg.session_id,
                                         session.pending_seller_name, session.pending_gstin)
        else:  # "setup_no" or any text
            session.state = FlowState.SETUP_NAME
            return BotResponse(text="No problem. What's your business name?")

    if session.state == FlowState.SETUP_NAME:
        name = msg.text.strip()
        if not name:
            return BotResponse(text="Please enter your business name:")
        return await _complete_setup(session, msg.session_id, name, session.pending_gstin)

    # Fallback (shouldn't reach here)
    session.state = FlowState.SETUP_GSTIN
    return BotResponse(text="Let's get you set up. What's your GSTIN?")


async def _complete_setup(session: Session, session_id: str, name: str, gstin: str) -> BotResponse:
    """Finalise setup, persist profile, transition to IDLE."""
    session.seller_profile = SellerProfile(name=name, gstin=gstin)
    session.state = FlowState.IDLE
    session.gstin_attempts = 0
    session.pending_gstin = ""
    session.pending_seller_name = ""
    seller_store.save(session_id, session.seller_profile)
    return BotResponse(
        text=(
            f"You're set up, {name}! 🎉\n\n"
            "Create a GST invoice in 60 seconds — 3 ways:\n\n"
            "🎙 *Voice* — say it in Hindi, English or Hinglish\n"
            "⌨️ *Text* — type the deal details\n"
            "↪ *Forward* — paste a negotiation chat, I'll extract the invoice\n\n"
            "How do you want to try?"
        ),
        buttons=[
            {"id": "mode_voice",   "title": "🎙 Try Voice"},
            {"id": "mode_text",    "title": "⌨️ Type It"},
            {"id": "mode_forward", "title": "↪ Forward Chat"},
        ],
    )


async def _handle_new_input(session: Session, msg: IncomingMessage) -> BotResponse:
    """Handle new invoice input (voice or text) from IDLE state."""
    session.state = FlowState.EXTRACTING
    session.touch()

    # Step 1: Get text from input (+ detected language from STT if voice)
    text = ""
    detected_lang: str | None = None
    if msg.type == MessageType.VOICE and msg.audio_data:
        try:
            text, detected_lang = await transcribe_audio(msg.audio_data, msg.audio_filename)
        except Exception as e:
            logger.error("STT failed: %s", e)
            text = ""
    elif msg.type == MessageType.TEXT:
        text = msg.text
        detected_lang = detect_script_language(text)

    if not text:
        session.state = FlowState.IDLE
        return BotResponse(text=t("input_unclear", _seller_lang(session)))

    # Step 2: If seller hasn't confirmed a language yet, run the detect-confirm
    # flow. Buffer the message so we can resume extraction after confirmation.
    if (
        session.seller_profile is not None
        and session.seller_profile.preferred_language is None
        and detected_lang is not None
        and detected_lang != "en"
    ):
        return _ask_language_confirm(session, text, detected_lang)

    is_forwarded = _looks_like_forwarded(text)
    return await _extract_and_draft(session, text, is_forwarded)


async def _extract_and_draft(session: Session, text: str, is_forwarded: bool) -> BotResponse:
    """Run extraction on ``text`` and build a draft response or prompt for fields."""
    # Step 2: Extract fields (with demo safety net)
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

    lang = _seller_lang(session)

    # Step 5: Check for missing required fields
    missing = _check_missing_fields(session.invoice, lang)
    if missing:
        session.state = FlowState.AWAITING_FIELDS
        session.missing_fields = missing
        return BotResponse(text=t("missing_prompt", lang, field=_field_label(missing[0], lang)))

    # All fields present — show draft
    session.state = FlowState.CONFIRMING
    return _build_draft_response(session.invoice, lang)


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


# Map internal field keys → translation key for their display label.
_FIELD_LABEL_KEYS = {
    "buyer": "field_buyer",
    "items": "field_items",
    "gst": "field_gst",
}


def _check_missing_fields(invoice: Invoice, lang: str = "en") -> list[str]:
    """Return list of missing required field **keys** (not display labels).

    Keys are stable identifiers (buyer/items/gst) — the display label is
    rendered via ``t()`` at the time the prompt is shown. Back-compat: the
    returned strings still contain substrings like "buyer"/"gst"/"item"
    that legacy callers may match against.
    """
    missing: list[str] = []
    if not invoice.buyer_name:
        missing.append("buyer")
    if not invoice.items:
        missing.append("items")
    if not invoice.gst_rate:
        missing.append("gst")
    return missing


def _field_label(key: str, lang: str) -> str:
    """Render the human-readable label for a missing-field key."""
    return t(_FIELD_LABEL_KEYS.get(key, key), lang)


async def _handle_missing_field_response(session: Session, msg: IncomingMessage) -> BotResponse:
    """Handle user's response to a missing field prompt."""
    lang = _seller_lang(session)
    if not session.missing_fields:
        session.state = FlowState.CONFIRMING
        return _build_draft_response(session.invoice, lang)

    field_key = session.missing_fields[0]
    text = msg.text.strip()

    if field_key == "buyer":
        session.invoice.buyer_name = text
        gstin_info = await lookup_gstin(text)
        if gstin_info:
            session.invoice.buyer_gstin = gstin_info["gstin"]
    elif field_key == "gst":
        import re
        match = re.search(r"\d+", text)
        if match:
            session.invoice.gst_rate = float(match.group())
    elif field_key == "items":
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

    remaining = _check_missing_fields(session.invoice, lang)
    if remaining:
        session.missing_fields = remaining
        return BotResponse(text=t("missing_next", lang, field=_field_label(remaining[0], lang)))

    session.state = FlowState.CONFIRMING
    return _build_draft_response(session.invoice, lang)


async def _handle_button(session: Session, msg: IncomingMessage) -> BotResponse:
    """Handle button press (Confirm / Edit / mode guides)."""
    payload = msg.button_payload.lower()

    # Input mode guide buttons — teach the feature, leave state as IDLE
    if payload == "mode_voice":
        return BotResponse(text=(
            "Hold the 🎤 mic button in WhatsApp and record your details.\n"
            "Speak naturally — for example:\n\n"
            "_'Ramesh Traders ka invoice banao, 150kg cotton, 45000 rupees, 12% GST'_\n\n"
            "Works in Hindi, English, or Hinglish 🇮🇳"
        ))
    if payload == "mode_text":
        return BotResponse(text=(
            "Just type your deal details. For example:\n\n"
            "_Invoice Kumar Enterprises 200kg steel rods 72000 18% GST_\n\n"
            "I'll figure out buyer name, items, and GST — type it naturally."
        ))
    if payload == "mode_forward":
        return BotResponse(text=(
            "Forward me the WhatsApp conversation where you negotiated the deal.\n\n"
            "I'll read through it, find the final agreed price, and create the "
            "invoice automatically — ignoring earlier offers.\n\n"
            "Just paste the messages below 👇"
        ))

    lang = _seller_lang(session)
    if payload == "confirm" and session.state == FlowState.CONFIRMING:
        return await _generate_invoice(session)
    elif payload == "edit":
        session.state = FlowState.IDLE
        return BotResponse(text=t("edit_ack", lang))
    elif payload == "new":
        # Preserve the seller profile (including language) across "new invoice".
        preserved = session.seller_profile
        new_session = reset_session(msg.session_id)
        new_session.seller_profile = preserved
        return BotResponse(text=t("new_ack", lang))
    else:
        return BotResponse(text=t("btn_fallback", lang))


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
        invoice.seller_name = (
            session.seller_profile.name if session.seller_profile and session.seller_profile.name
            else settings.seller_name
        )
    if not invoice.seller_gstin:
        invoice.seller_gstin = (
            session.seller_profile.gstin if session.seller_profile and session.seller_profile.gstin
            else settings.seller_gstin
        )

    lang = _seller_lang(session)
    try:
        pdf_bytes = generate_invoice_pdf(invoice, lang=lang)
    except Exception as e:
        logger.error("PDF generation failed: %s", e)
        session.state = FlowState.CONFIRMING
        return BotResponse(text=t("pdf_fail", lang))

    session.state = FlowState.DONE
    session.touch()

    return BotResponse(
        text=t(
            "invoice_done",
            lang,
            number=invoice.invoice_number,
            buyer=invoice.buyer_name,
            total=f"{invoice.total:,.2f}",
            rate=invoice.gst_rate,
        ),
        pdf_bytes=pdf_bytes,
        buttons=[{"id": "new", "title": t("btn_new", lang)}],
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


def _build_draft_response(invoice: Invoice, lang: str = "en") -> BotResponse:
    """Build the draft confirmation message in the seller's preferred language."""
    items_text = ""
    for item in invoice.items:
        items_text += f"  - {item.description} | {item.quantity:g} {item.unit} x Rs. {item.rate:,.0f} = Rs. {item.amount:,.2f}\n"

    gstin_display = invoice.buyer_gstin or t("draft_gstin_none", lang)
    draft = f"""**{t('draft_header', lang)}**

**{t('draft_buyer', lang)}:** {invoice.buyer_name}
**{t('draft_gstin', lang)}:** {gstin_display}

**{t('draft_items', lang)}:**
{items_text}
**{t('draft_subtotal', lang)}:** Rs. {invoice.subtotal:,.2f}
**{t('draft_gst', lang)} ({invoice.gst_rate}%):** Rs. {invoice.gst_amount:,.2f}
**{t('draft_total', lang)}:** Rs. {invoice.total:,.2f}"""

    return BotResponse(
        text=draft,
        buttons=[
            {"id": "confirm", "title": t("btn_confirm", lang)},
            {"id": "edit", "title": t("btn_edit", lang)},
        ],
    )


# ---------------------------------------------------------------------------
# Language detection + confirmation flow
# ---------------------------------------------------------------------------

def _ask_language_confirm(session: Session, text: str, detected: str) -> BotResponse:
    """Pause the current invoice input and ask the seller to confirm language."""
    session.state = FlowState.AWAITING_LANGUAGE_CONFIRM
    session.pending_language = detected
    session.pending_message_text = text
    session.pending_message_is_forwarded = _looks_like_forwarded(text)

    # Bilingual prompt: native script line + English fallback for readability.
    prompt = f"{t('lang_confirm', detected)}\n\n({t('lang_confirm', 'en')} — tap 'Keep English' to stay in English.)"
    return BotResponse(
        text=prompt,
        buttons=[
            {"id": f"lang_set_{detected}", "title": t("btn_lang_keep", detected)},
            {"id": "lang_set_en", "title": "Keep English"},
            {"id": "lang_set_other", "title": t("btn_lang_switch", detected)},
        ],
    )


async def _handle_language_button(session: Session, msg: IncomingMessage) -> BotResponse:
    """Handle a ``lang_set_*`` button press."""
    payload = msg.button_payload

    if payload == "lang_set_other":
        # Show the full picker.
        return BotResponse(
            text="Pick a language:",
            buttons=[
                {"id": f"lang_set_{code}", "title": name}
                for code, name in LANG_NAMES.items()
            ],
        )

    if not payload.startswith("lang_set_"):
        return BotResponse(text=t("btn_fallback", _seller_lang(session)))

    code = payload.removeprefix("lang_set_")
    if code not in STRINGS:
        return BotResponse(text=t("btn_fallback", _seller_lang(session)))

    return await _confirm_pending_language(session, msg, accept=True, override_lang=code)


async def _confirm_pending_language(
    session: Session,
    msg: IncomingMessage,
    accept: bool,
    override_lang: str | None = None,
) -> BotResponse:
    """Persist the language choice and resume the buffered invoice input."""
    chosen = override_lang or (session.pending_language if accept else "en") or "en"

    if session.seller_profile is None:
        return BotResponse(text=t("input_unclear", "en"))

    session.seller_profile.preferred_language = chosen
    seller_store.save(msg.session_id, session.seller_profile)

    pending_text = session.pending_message_text
    pending_forwarded = session.pending_message_is_forwarded
    session.pending_language = None
    session.pending_message_text = ""
    session.pending_message_is_forwarded = False

    if not pending_text:
        # Language was set via "change language" command — no buffered message.
        session.state = FlowState.IDLE
        return BotResponse(text=t("lang_set", chosen))

    # Resume extraction on the buffered message in the chosen language.
    session.state = FlowState.EXTRACTING
    return await _extract_and_draft(session, pending_text, pending_forwarded)
