"""GST-compliant invoice PDF generator with mock IRN and QR code.

Labels are bilingual when the seller has a non-English preferred language:
English on top (required for GST filing compatibility) + regional script
below. Font files are bundled under ``assets/fonts/`` and loaded lazily on
first use.
"""

import hashlib
import io
import logging
import os
import uuid
from datetime import datetime

import qrcode
from fpdf import FPDF
from i18n.strings import t
from models.invoice import Invoice

logger = logging.getLogger(__name__)

# --- Font registration ----------------------------------------------------

_FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")

# Which bundled font to use for each supported language.
_LANG_FONT = {
    "hi": ("NotoDev", "NotoSansDevanagari-VF.ttf"),
    "mr": ("NotoDev", "NotoSansDevanagari-VF.ttf"),
    "ta": ("NotoTam", "NotoSansTamil-VF.ttf"),
    "ml": ("NotoMal", "NotoSansMalayalam-VF.ttf"),
    "bn": ("NotoBen", "NotoSansBengali-VF.ttf"),
}


def _register_font(pdf: FPDF, lang: str) -> str | None:
    """Register the Noto font for ``lang`` with ``pdf``. Returns the font
    alias to use, or ``None`` if the language doesn't need a custom font or
    the font file is missing."""
    entry = _LANG_FONT.get(lang)
    if not entry:
        return None
    alias, filename = entry
    path = os.path.join(_FONTS_DIR, filename)
    if not os.path.exists(path):
        logger.warning("Noto font missing: %s — falling back to Helvetica", path)
        return None
    try:
        pdf.add_font(alias, "", path)
        return alias
    except Exception as e:
        logger.warning("Font registration failed for %s: %s", lang, e)
        return None


def generate_invoice_number() -> str:
    """Generate a sequential-looking invoice number."""
    now = datetime.now()
    seq = uuid.uuid4().hex[:4].upper()
    return f"INV-{now.year}-{now.month:02d}{seq}"


def generate_mock_irn(invoice: Invoice) -> str:
    """Generate a mock 64-char IRN hash (simulating GSP/IRP response)."""
    seed = f"{invoice.seller_gstin}{invoice.invoice_number}{invoice.date}"
    return hashlib.sha256(seed.encode()).hexdigest()


def generate_qr_bytes(irn: str) -> bytes:
    """Generate QR code PNG bytes for the IRN."""
    qr = qrcode.make(irn)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()


def generate_invoice_pdf(invoice: Invoice, lang: str = "en") -> bytes:
    """Generate a GST-compliant invoice PDF and return bytes.

    ``lang`` controls the regional-script label layer. English labels are
    always present (required for GST compliance); regional labels appear
    alongside when ``lang`` is non-English and the font is available.
    """
    if not invoice.invoice_number:
        invoice.invoice_number = generate_invoice_number()

    irn = generate_mock_irn(invoice)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    regional_font = _register_font(pdf, lang) if lang and lang != "en" else None

    def _regional(key: str) -> str | None:
        """Return the regional label for ``key`` if we have a font for it."""
        if not regional_font:
            return None
        return t(key, lang)

    # --- Header ---
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "TAX INVOICE", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # --- Invoice meta ---
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"Invoice #: {invoice.invoice_number}")
    pdf.cell(95, 6, f"Date: {invoice.date}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # --- Seller / Buyer block ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 6, "Seller", new_x="END")
    pdf.cell(95, 6, "Buyer", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(95, 5, invoice.seller_name or "Demo Seller", new_x="END")
    pdf.cell(95, 5, invoice.buyer_name or "-", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(95, 5, f"GSTIN: {invoice.seller_gstin or 'N/A'}", new_x="END")
    pdf.cell(95, 5, f"GSTIN: {invoice.buyer_gstin or 'N/A'}", new_x="LMARGIN", new_y="NEXT")

    # Regional "Buyer" header (if font available) — small, gray, below the English line
    reg_buyer = _regional("draft_buyer")
    if reg_buyer:
        pdf.set_font(regional_font, "", 8)
        pdf.set_text_color(110, 110, 110)
        pdf.cell(95, 5, "", new_x="END")
        pdf.cell(95, 5, reg_buyer, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    pdf.ln(6)

    # --- Line items table ---
    pdf.set_font("Helvetica", "B", 9)
    col_w = [10, 70, 25, 20, 25, 40]
    headers = ["#", "Description", "Qty", "Unit", "Rate", "Amount"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for idx, item in enumerate(invoice.items, 1):
        pdf.cell(col_w[0], 7, str(idx), border=1, align="C")
        pdf.cell(col_w[1], 7, item.description[:35], border=1)
        pdf.cell(col_w[2], 7, f"{item.quantity:g}", border=1, align="R")
        pdf.cell(col_w[3], 7, item.unit, border=1, align="C")
        pdf.cell(col_w[4], 7, f"{item.rate:,.0f}", border=1, align="R")
        pdf.cell(col_w[5], 7, f"{item.amount:,.2f}", border=1, align="R")
        pdf.ln()

    pdf.ln(4)

    # --- Totals ---
    x_label = 130
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(x_label)
    pdf.cell(30, 6, "Subtotal:", align="R")
    pdf.cell(30, 6, f"Rs. {invoice.subtotal:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    half_rate = invoice.gst_rate / 2
    if invoice.is_interstate:
        pdf.set_x(x_label)
        pdf.cell(30, 6, f"IGST ({invoice.gst_rate}%):", align="R")
        pdf.cell(30, 6, f"Rs. {invoice.igst:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_x(x_label)
        pdf.cell(30, 6, f"CGST ({half_rate}%):", align="R")
        pdf.cell(30, 6, f"Rs. {invoice.cgst:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(x_label)
        pdf.cell(30, 6, f"SGST ({half_rate}%):", align="R")
        pdf.cell(30, 6, f"Rs. {invoice.sgst:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(x_label)
    pdf.cell(30, 8, "Total:", align="R")
    pdf.cell(30, 8, f"Rs. {invoice.total:,.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    # Regional "Total" label below, right-aligned under the amount
    reg_total = _regional("draft_total")
    if reg_total:
        pdf.set_font(regional_font, "", 8)
        pdf.set_text_color(110, 110, 110)
        pdf.set_x(x_label)
        pdf.cell(60, 5, reg_total, align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    pdf.ln(6)

    # --- IRN ---
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(0, 4, f"IRN: {irn}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # --- QR Code ---
    qr_bytes = generate_qr_bytes(irn)
    qr_stream = io.BytesIO(qr_bytes)
    pdf.image(qr_stream, x=10, w=30)

    # --- Footer ---
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(0, 4, "Generated by BillKaro | Powered by Sarvam", align="C")

    return bytes(pdf.output())
