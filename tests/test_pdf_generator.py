"""Tests for PDF generation."""

from models.invoice import Invoice, LineItem
from services.pdf_generator import generate_invoice_pdf, generate_invoice_number, generate_mock_irn


def test_generate_invoice_number():
    num = generate_invoice_number()
    assert num.startswith("INV-")
    assert len(num) > 8


def test_generate_mock_irn():
    inv = Invoice(seller_gstin="27AABCU9603R1ZM", invoice_number="INV-2025-01AB", date="2025-04-01")
    irn = generate_mock_irn(inv)
    assert len(irn) == 64  # SHA-256 hex digest


def test_generate_pdf_returns_bytes():
    inv = Invoice(
        invoice_number="INV-TEST-001",
        seller_name="Test Seller",
        seller_gstin="27AABCU9603R1ZM",
        buyer_name="Test Buyer",
        buyer_gstin="29AAGCK5148R1ZX",
        items=[LineItem(description="Cotton", quantity=100, unit="kg", rate=300)],
        gst_rate=12,
    )
    pdf_bytes = generate_invoice_pdf(inv)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes[:5] == b"%PDF-"


def test_pdf_with_multiple_items():
    inv = Invoice(
        invoice_number="INV-TEST-002",
        buyer_name="Multi Item Buyer",
        items=[
            LineItem(description="Cotton", quantity=100, unit="kg", rate=300),
            LineItem(description="Silk", quantity=50, unit="m", rate=1200),
        ],
        gst_rate=18,
    )
    pdf_bytes = generate_invoice_pdf(inv)
    assert pdf_bytes[:5] == b"%PDF-"
