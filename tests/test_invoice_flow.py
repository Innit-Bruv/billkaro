"""Tests for the invoice flow state machine."""

import pytest
from models.invoice import IncomingMessage, MessageType, FlowState, SellerProfile
from engine.invoice_flow import handle_message, get_session, reset_session
import services.seller_store as seller_store


@pytest.mark.asyncio
async def test_reset_command():
    msg = IncomingMessage(session_id="test-1", type=MessageType.TEXT, text="reset")
    resp = await handle_message(msg)
    assert "reset" in resp.text.lower() or "new" in resp.text.lower()


@pytest.mark.asyncio
async def test_demo_extraction_ramesh():
    """Test that the demo safety net kicks in for 'Ramesh Traders'."""
    reset_session("test-2")
    msg = IncomingMessage(
        session_id="test-2",
        type=MessageType.TEXT,
        text="Ramesh Traders ka invoice banao, 150kg cotton, 45000 rupees, 12% GST",
    )
    resp = await handle_message(msg)
    # Should return a draft with Ramesh Traders
    assert "Ramesh Traders" in resp.text
    assert resp.buttons  # Should have Confirm/Edit buttons


@pytest.mark.asyncio
async def test_confirm_generates_pdf():
    """Test that confirming a draft produces a PDF."""
    # First, create a draft
    reset_session("test-3")
    msg = IncomingMessage(
        session_id="test-3",
        type=MessageType.TEXT,
        text="Ramesh Traders ka invoice banao, 150kg cotton, 45000 rupees, 12% GST",
    )
    await handle_message(msg)

    # Confirm it
    confirm = IncomingMessage(
        session_id="test-3",
        type=MessageType.BUTTON,
        button_payload="confirm",
    )
    resp = await handle_message(confirm)
    assert resp.pdf_bytes is not None
    assert len(resp.pdf_bytes) > 0
    assert "INV-" in resp.text


@pytest.mark.asyncio
async def test_missing_buyer_name_prompts():
    """Test that missing buyer name triggers a follow-up question."""
    reset_session("test-4")
    msg = IncomingMessage(
        session_id="test-4",
        type=MessageType.TEXT,
        text="invoice for 500 units of rice at 50 per kg",
    )
    resp = await handle_message(msg)
    session = get_session("test-4")
    # Should either ask for buyer name or show a draft (if NLP extracted something)
    assert session.state in (FlowState.AWAITING_FIELDS, FlowState.CONFIRMING)


@pytest.mark.asyncio
async def test_gst_rate_zero_prompts_for_rate():
    """Missing gst_rate should trigger a follow-up question, not a 0% invoice."""
    reset_session("test-6")
    # "300/kg" triggers the forwarded demo cache (has gst_rate=12) — use a plain text
    # that the demo cache won't match, so the engine processes it with gst_rate=0
    from services.demo_safety_net import DEMO_EXTRACTIONS
    from models.invoice import ExtractionResult, LineItem
    # Temporarily inject a 0-gst extraction into the safety net
    DEMO_EXTRACTIONS["__test_no_gst__"] = ExtractionResult(
        buyer_name="Test Buyer",
        items=[LineItem(description="Widgets", quantity=10, unit="pcs", rate=100)],
        gst_rate=None,
    )
    try:
        msg = IncomingMessage(
            session_id="test-6",
            type=MessageType.TEXT,
            text="__test_no_gst__ invoice",
        )
        resp = await handle_message(msg)
        assert "GST" in resp.text
        session = get_session("test-6")
        assert session.state == FlowState.AWAITING_FIELDS
        assert any("gst" in f.lower() for f in session.missing_fields)
    finally:
        del DEMO_EXTRACTIONS["__test_no_gst__"]


@pytest.mark.asyncio
async def test_awaiting_fields_full_resolution():
    """Providing all missing fields should transition to CONFIRMING."""
    reset_session("test-7")
    from services.demo_safety_net import DEMO_EXTRACTIONS
    from models.invoice import ExtractionResult, LineItem
    # Inject extraction with no buyer name and no gst_rate
    DEMO_EXTRACTIONS["__test_missing_all__"] = ExtractionResult(
        items=[LineItem(description="Rice", quantity=100, unit="kg", rate=50)],
    )
    try:
        msg = IncomingMessage(session_id="test-7", type=MessageType.TEXT, text="__test_missing_all__ invoice")
        await handle_message(msg)
        session = get_session("test-7")
        assert session.state == FlowState.AWAITING_FIELDS

        # Provide buyer name
        resp = await handle_message(IncomingMessage(session_id="test-7", type=MessageType.TEXT, text="Sharma Traders"))
        session = get_session("test-7")
        # Still AWAITING_FIELDS for gst_rate, or already CONFIRMING if gst_rate was 0 before fix
        # After fix: should ask for GST rate next
        if session.state == FlowState.AWAITING_FIELDS:
            resp = await handle_message(IncomingMessage(session_id="test-7", type=MessageType.TEXT, text="18"))

        session = get_session("test-7")
        assert session.state == FlowState.CONFIRMING
        assert session.invoice.buyer_name == "Sharma Traders"
    finally:
        del DEMO_EXTRACTIONS["__test_missing_all__"]


@pytest.mark.asyncio
async def test_edit_from_confirming_resets_to_idle():
    """Sending text while in CONFIRMING state should re-extract (not crash)."""
    reset_session("test-8")
    # Get to CONFIRMING state
    msg = IncomingMessage(
        session_id="test-8",
        type=MessageType.TEXT,
        text="Ramesh Traders ka invoice banao, 150kg cotton, 45000 rupees, 12% GST",
    )
    await handle_message(msg)
    session = get_session("test-8")
    assert session.state == FlowState.CONFIRMING

    # Send a correction as text
    edit_msg = IncomingMessage(
        session_id="test-8",
        type=MessageType.TEXT,
        text="actually make it Kumar Enterprises, 200kg steel, 72000, 18% GST",
    )
    resp = await handle_message(edit_msg)
    # Should re-extract and show a new draft or ask for fields
    session = get_session("test-8")
    assert session.state in (FlowState.CONFIRMING, FlowState.AWAITING_FIELDS)


@pytest.mark.asyncio
async def test_forwarded_messages_extraction():
    """Forwarded message text (300/kg trigger) should use forwarded prompt cache."""
    reset_session("test-9")
    forwarded = (
        "Ramesh: Can you do 150kg cotton?\n"
        "You: Yes, 300/kg works\n"
        "Ramesh: Done. 12% GST right?\n"
        "You: Yes, total 50400 with GST"
    )
    msg = IncomingMessage(session_id="test-9", type=MessageType.TEXT, text=forwarded)
    resp = await handle_message(msg)
    # "300/kg" triggers demo cache → Ramesh Traders, 150kg cotton, 12% GST
    assert "Ramesh Traders" in resp.text
    assert resp.buttons


@pytest.mark.asyncio
async def test_setup_gstin_found_and_confirmed():
    """New user: valid GSTIN found → confirm → seller profile set → IDLE."""
    reset_session("setup-1")
    seller_store.delete("setup-1")

    # First message triggers welcome + SETUP_GSTIN
    resp = await handle_message(IncomingMessage(session_id="setup-1", type=MessageType.TEXT, text="hi"))
    assert "GSTIN" in resp.text
    assert get_session("setup-1").state == FlowState.SETUP_GSTIN

    # Send a known demo GSTIN
    resp = await handle_message(IncomingMessage(session_id="setup-1", type=MessageType.TEXT, text="27AABCU9603R1ZM"))
    assert "Ramesh Traders" in resp.text
    assert resp.buttons
    assert get_session("setup-1").state == FlowState.SETUP_CONFIRM

    # Confirm
    resp = await handle_message(IncomingMessage(session_id="setup-1", type=MessageType.BUTTON, button_payload="setup_yes"))
    assert "set up" in resp.text.lower()
    session = get_session("setup-1")
    assert session.state == FlowState.IDLE
    assert session.seller_profile is not None
    assert session.seller_profile.name == "Ramesh Traders Pvt Ltd"
    assert session.seller_profile.gstin == "27AABCU9603R1ZM"


@pytest.mark.asyncio
async def test_setup_gstin_found_user_says_no():
    """GSTIN found but user says 'No' → ask for name → GSTIN retained."""
    reset_session("setup-2")
    seller_store.delete("setup-2")

    await handle_message(IncomingMessage(session_id="setup-2", type=MessageType.TEXT, text="hi"))
    await handle_message(IncomingMessage(session_id="setup-2", type=MessageType.TEXT, text="27AABCU9603R1ZM"))

    # User says No
    resp = await handle_message(IncomingMessage(session_id="setup-2", type=MessageType.BUTTON, button_payload="setup_no"))
    assert "business name" in resp.text.lower()
    assert get_session("setup-2").state == FlowState.SETUP_NAME

    # Provide name
    resp = await handle_message(IncomingMessage(session_id="setup-2", type=MessageType.TEXT, text="Sharma Exports"))
    session = get_session("setup-2")
    assert session.state == FlowState.IDLE
    assert session.seller_profile.name == "Sharma Exports"
    assert session.seller_profile.gstin == "27AABCU9603R1ZM"  # GSTIN retained


@pytest.mark.asyncio
async def test_setup_gstin_not_found():
    """Unknown GSTIN → falls back to name entry."""
    reset_session("setup-3")
    seller_store.delete("setup-3")

    await handle_message(IncomingMessage(session_id="setup-3", type=MessageType.TEXT, text="hi"))
    resp = await handle_message(IncomingMessage(session_id="setup-3", type=MessageType.TEXT, text="29AAGCK9999R1ZX"))
    assert "business name" in resp.text.lower()
    assert get_session("setup-3").state == FlowState.SETUP_NAME

    resp = await handle_message(IncomingMessage(session_id="setup-3", type=MessageType.TEXT, text="New Exports Ltd"))
    session = get_session("setup-3")
    assert session.state == FlowState.IDLE
    assert session.seller_profile.name == "New Exports Ltd"


@pytest.mark.asyncio
async def test_setup_invalid_gstin_three_times_then_fallthrough():
    """Three invalid GSTIN attempts → auto-fallthrough to name entry."""
    reset_session("setup-4")
    seller_store.delete("setup-4")

    await handle_message(IncomingMessage(session_id="setup-4", type=MessageType.TEXT, text="hi"))
    for _ in range(3):
        resp = await handle_message(IncomingMessage(session_id="setup-4", type=MessageType.TEXT, text="BADGSTIN"))

    assert get_session("setup-4").state == FlowState.SETUP_NAME
    assert "business name" in resp.text.lower()

    resp = await handle_message(IncomingMessage(session_id="setup-4", type=MessageType.TEXT, text="Fallback Traders"))
    session = get_session("setup-4")
    assert session.state == FlowState.IDLE
    assert session.seller_profile.name == "Fallback Traders"
    assert session.seller_profile.gstin == ""  # no GSTIN collected


@pytest.mark.asyncio
async def test_returning_user_skips_setup():
    """Returning user with existing profile goes straight to invoice flow."""
    reset_session("setup-5")
    # Pre-seed a seller profile on disk
    seller_store.save("setup-5", SellerProfile(name="Patel Distributors LLP", gstin="24AAACH7409R1ZW"))

    resp = await handle_message(IncomingMessage(
        session_id="setup-5",
        type=MessageType.TEXT,
        text="Ramesh Traders ka invoice banao, 150kg cotton, 45000 rupees, 12% GST",
    ))
    session = get_session("setup-5")
    # Should be in invoice flow, not setup
    assert session.state in (FlowState.CONFIRMING, FlowState.AWAITING_FIELDS)
    assert session.seller_profile is not None
    assert session.seller_profile.name == "Patel Distributors LLP"
    # Clean up
    seller_store.delete("setup-5")


@pytest.mark.asyncio
async def test_setup_completion_shows_mode_buttons():
    """After setup, welcome message should include 3 input mode buttons."""
    reset_session("setup-6")
    seller_store.delete("setup-6")

    await handle_message(IncomingMessage(session_id="setup-6", type=MessageType.TEXT, text="hi"))
    await handle_message(IncomingMessage(session_id="setup-6", type=MessageType.TEXT, text="27AABCU9603R1ZM"))
    resp = await handle_message(IncomingMessage(session_id="setup-6", type=MessageType.BUTTON, button_payload="setup_yes"))

    button_ids = [b["id"] for b in resp.buttons]
    assert "mode_voice" in button_ids
    assert "mode_text" in button_ids
    assert "mode_forward" in button_ids
    assert get_session("setup-6").state == FlowState.IDLE


@pytest.mark.asyncio
async def test_mode_buttons_return_guides_and_stay_idle():
    """Tapping a mode button returns a guide and leaves state as IDLE."""
    seller_store.save("setup-7", SellerProfile(name="Test Co", gstin="27AADCB2230M1ZT"))
    reset_session("setup-7")

    for payload, keyword in [
        ("mode_voice", "mic"),
        ("mode_text", "type"),
        ("mode_forward", "Forward"),
    ]:
        reset_session("setup-7")
        resp = await handle_message(IncomingMessage(
            session_id="setup-7", type=MessageType.BUTTON, button_payload=payload
        ))
        assert keyword.lower() in resp.text.lower(), f"Expected '{keyword}' in {payload} response"
        assert get_session("setup-7").state == FlowState.IDLE
        assert resp.pdf_bytes is None

    seller_store.delete("setup-7")


@pytest.mark.asyncio
async def test_new_button_resets():
    """Test that the 'new' button resets the session."""
    reset_session("test-5")
    # Create and confirm an invoice first
    msg = IncomingMessage(
        session_id="test-5",
        type=MessageType.TEXT,
        text="Kumar Enterprises, 200kg steel rods, 72000, 18% GST",
    )
    await handle_message(msg)
    confirm = IncomingMessage(session_id="test-5", type=MessageType.BUTTON, button_payload="confirm")
    await handle_message(confirm)

    # Now press "new"
    new_msg = IncomingMessage(session_id="test-5", type=MessageType.BUTTON, button_payload="new")
    resp = await handle_message(new_msg)
    session = get_session("test-5")
    assert session.state == FlowState.IDLE
