"""End-to-end tests for the multilingual detect → confirm → resume flow."""

import pytest

import services.seller_store as seller_store
from engine.invoice_flow import get_session, handle_message, reset_session
from i18n.strings import STRINGS
from models.invoice import (
    FlowState,
    IncomingMessage,
    MessageType,
    SellerProfile,
)


def _seed(session_id: str, lang: str | None = None) -> None:
    """Pre-seed a seller profile so we bypass setup, then reset the session."""
    seller_store.save(
        session_id,
        SellerProfile(name="Test Seller", gstin="27AADCB2230M1ZT", preferred_language=lang),
    )
    reset_session(session_id)


@pytest.mark.asyncio
async def test_hindi_input_triggers_language_confirm():
    _seed("mlang-1", lang=None)
    try:
        msg = IncomingMessage(
            session_id="mlang-1",
            type=MessageType.TEXT,
            text="रमेश ट्रेडर्स को 150 किलो कपास, 45000 रुपये, 12% GST",
        )
        resp = await handle_message(msg)
        session = get_session("mlang-1")
        assert session.state == FlowState.AWAITING_LANGUAGE_CONFIRM
        assert session.pending_language == "hi"
        assert session.pending_message_text  # buffered
        # Button ids should include Hindi keep + English keep + switch
        ids = [b["id"] for b in resp.buttons]
        assert "lang_set_hi" in ids
        assert "lang_set_en" in ids
        assert "lang_set_other" in ids
    finally:
        seller_store.delete("mlang-1")


@pytest.mark.asyncio
async def test_english_input_skips_language_confirm():
    """Latin-script input should go straight to extraction, no prompt."""
    _seed("mlang-2", lang=None)
    try:
        msg = IncomingMessage(
            session_id="mlang-2",
            type=MessageType.TEXT,
            text="Ramesh Traders ka invoice banao, 150kg cotton, 45000 rupees, 12% GST",
        )
        await handle_message(msg)
        session = get_session("mlang-2")
        assert session.state != FlowState.AWAITING_LANGUAGE_CONFIRM
        # Should have gone through extraction → CONFIRMING
        assert session.state in (FlowState.CONFIRMING, FlowState.AWAITING_FIELDS)
    finally:
        seller_store.delete("mlang-2")


@pytest.mark.asyncio
async def test_confirm_hindi_language_resumes_extraction():
    _seed("mlang-3", lang=None)
    try:
        await handle_message(IncomingMessage(
            session_id="mlang-3",
            type=MessageType.TEXT,
            text="रमेश ट्रेडर्स को 150 किलो कपास, 45000 रुपये, 12% GST",
        ))
        # Press "Keep Hindi" button
        resp = await handle_message(IncomingMessage(
            session_id="mlang-3",
            type=MessageType.BUTTON,
            button_payload="lang_set_hi",
        ))
        session = get_session("mlang-3")
        assert session.seller_profile.preferred_language == "hi"
        # Buffered message should be cleared
        assert session.pending_message_text == ""
        # Should have resumed extraction → draft shown in Hindi
        assert session.state in (FlowState.CONFIRMING, FlowState.AWAITING_FIELDS)
        if session.state == FlowState.CONFIRMING:
            # Draft header should be in Hindi
            assert STRINGS["hi"]["draft_header"] in resp.text
    finally:
        seller_store.delete("mlang-3")


@pytest.mark.asyncio
async def test_keep_english_still_resumes_extraction():
    _seed("mlang-4", lang=None)
    try:
        await handle_message(IncomingMessage(
            session_id="mlang-4",
            type=MessageType.TEXT,
            text="रमेश ट्रेडर्स को 150 किलो कपास, 45000 रुपये, 12% GST",
        ))
        resp = await handle_message(IncomingMessage(
            session_id="mlang-4",
            type=MessageType.BUTTON,
            button_payload="lang_set_en",
        ))
        session = get_session("mlang-4")
        assert session.seller_profile.preferred_language == "en"
        assert session.state in (FlowState.CONFIRMING, FlowState.AWAITING_FIELDS)
    finally:
        seller_store.delete("mlang-4")


@pytest.mark.asyncio
async def test_lang_set_other_shows_full_picker():
    _seed("mlang-5", lang=None)
    try:
        await handle_message(IncomingMessage(
            session_id="mlang-5",
            type=MessageType.TEXT,
            text="রমেশ ট্রেডার্সের জন্য 150 কেজি তুলা, 45000 টাকা, 12% GST",
        ))
        resp = await handle_message(IncomingMessage(
            session_id="mlang-5",
            type=MessageType.BUTTON,
            button_payload="lang_set_other",
        ))
        ids = [b["id"] for b in resp.buttons]
        # Full picker shows all 6
        assert "lang_set_en" in ids
        assert "lang_set_hi" in ids
        assert "lang_set_ta" in ids
        assert "lang_set_ml" in ids
        assert "lang_set_bn" in ids
        assert "lang_set_mr" in ids
    finally:
        seller_store.delete("mlang-5")


@pytest.mark.asyncio
async def test_seller_with_preferred_language_skips_confirm():
    """If the seller already has a preferred language, no prompt should fire."""
    _seed("mlang-6", lang="hi")
    try:
        msg = IncomingMessage(
            session_id="mlang-6",
            type=MessageType.TEXT,
            text="रमेश ट्रेडर्स को 150 किलो कपास, 45000 रुपये, 12% GST",
        )
        await handle_message(msg)
        session = get_session("mlang-6")
        assert session.state != FlowState.AWAITING_LANGUAGE_CONFIRM
        assert session.state in (FlowState.CONFIRMING, FlowState.AWAITING_FIELDS)
    finally:
        seller_store.delete("mlang-6")


@pytest.mark.asyncio
async def test_change_language_command_reopens_picker():
    _seed("mlang-7", lang="hi")
    try:
        resp = await handle_message(IncomingMessage(
            session_id="mlang-7",
            type=MessageType.TEXT,
            text="change language",
        ))
        ids = [b["id"] for b in resp.buttons]
        assert "lang_set_en" in ids
        assert "lang_set_ta" in ids
        session = get_session("mlang-7")
        assert session.seller_profile.preferred_language is None
    finally:
        seller_store.delete("mlang-7")


@pytest.mark.asyncio
async def test_tamil_input_triggers_tamil_confirm():
    _seed("mlang-8", lang=None)
    try:
        resp = await handle_message(IncomingMessage(
            session_id="mlang-8",
            type=MessageType.TEXT,
            text="ரமேஷ் ட்ரேடர்ஸுக்கு 150 கிலோ பருத்தி, 45000 ரூபாய், 12% GST",
        ))
        session = get_session("mlang-8")
        assert session.state == FlowState.AWAITING_LANGUAGE_CONFIRM
        assert session.pending_language == "ta"
        ids = [b["id"] for b in resp.buttons]
        assert "lang_set_ta" in ids
    finally:
        seller_store.delete("mlang-8")


@pytest.mark.asyncio
async def test_reset_ack_localized_after_language_set():
    """After the seller chooses Hindi, reset should reply in Hindi."""
    _seed("mlang-9", lang="hi")
    try:
        resp = await handle_message(IncomingMessage(
            session_id="mlang-9",
            type=MessageType.TEXT,
            text="reset",
        ))
        assert STRINGS["hi"]["reset_ack"] in resp.text
    finally:
        seller_store.delete("mlang-9")
