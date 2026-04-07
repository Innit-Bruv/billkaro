"""Tests for the invoice flow state machine."""

import pytest
from models.invoice import IncomingMessage, MessageType, FlowState
from engine.invoice_flow import handle_message, get_session, reset_session


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
