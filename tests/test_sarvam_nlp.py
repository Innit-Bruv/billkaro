"""Tests for NLP extraction (mocked API)."""

from services.sarvam_nlp import _parse_extraction


def test_parse_valid_json():
    raw = '{"buyer_name": "Ramesh Traders", "amount": 45000, "items": [{"description": "Cotton", "quantity": 150, "unit": "kg", "rate": 300}], "gst_rate": 12, "buyer_gstin": "", "notes": ""}'
    result = _parse_extraction(raw)
    assert result.buyer_name == "Ramesh Traders"
    assert len(result.items) == 1
    assert result.items[0].description == "Cotton"
    assert result.gst_rate == 12


def test_parse_json_with_markdown_fences():
    raw = '```json\n{"buyer_name": "Test", "amount": 1000, "items": [], "gst_rate": 18, "buyer_gstin": "", "notes": ""}\n```'
    result = _parse_extraction(raw)
    assert result.buyer_name == "Test"
    assert result.gst_rate == 18


def test_parse_invalid_json_returns_empty():
    raw = "Sorry, I can't parse that input."
    result = _parse_extraction(raw)
    assert result.buyer_name == ""
    assert result.items == []


def test_parse_partial_items():
    raw = '{"buyer_name": "Patel", "items": [{"description": "Rice", "quantity": 500, "unit": "kg", "rate": 50}, {"description": "invalid"}], "gst_rate": 5}'
    result = _parse_extraction(raw)
    assert result.buyer_name == "Patel"
    # First item valid, second should still parse (with 0 defaults)
    assert len(result.items) >= 1
    assert result.items[0].description == "Rice"
