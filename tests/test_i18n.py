"""Tests for the i18n string table and script detection."""

import pytest

from i18n.strings import LANG_NAMES, STRINGS, detect_script_language, t


SUPPORTED = ("en", "hi", "ta", "ml", "bn", "mr")


def test_all_languages_present():
    for code in SUPPORTED:
        assert code in STRINGS, f"missing language: {code}"
        assert code in LANG_NAMES, f"missing display name: {code}"


def test_string_table_parity():
    """Every language must provide every key present in English."""
    english_keys = set(STRINGS["en"].keys())
    for code in SUPPORTED:
        keys = set(STRINGS[code].keys())
        missing = english_keys - keys
        assert not missing, f"{code} missing keys: {sorted(missing)}"
        extra = keys - english_keys
        assert not extra, f"{code} has unknown keys: {sorted(extra)}"


def test_no_empty_strings():
    for code in SUPPORTED:
        for key, value in STRINGS[code].items():
            assert value, f"{code}.{key} is empty"


def test_format_placeholders_preserved():
    """Keys that format placeholders in English must preserve them in every language."""
    import re
    placeholder_re = re.compile(r"\{(\w+)\}")
    for key, english in STRINGS["en"].items():
        english_slots = set(placeholder_re.findall(english))
        if not english_slots:
            continue
        for code in SUPPORTED:
            translated = STRINGS[code][key]
            their_slots = set(placeholder_re.findall(translated))
            assert their_slots == english_slots, (
                f"{code}.{key} placeholder mismatch: {their_slots} vs {english_slots}"
            )


def test_t_fallback_to_english_for_unknown_lang():
    assert t("btn_confirm", "xx") == STRINGS["en"]["btn_confirm"]


def test_t_fallback_to_english_for_none():
    assert t("btn_confirm", None) == STRINGS["en"]["btn_confirm"]


def test_t_fallback_to_english_for_missing_key():
    # "bogus_key" is not in any table → returns the key itself
    assert t("bogus_key", "hi") == "bogus_key"


def test_t_format_substitution():
    out = t("invoice_done", "en", number="INV-1", buyer="Ramesh", total="100.00", rate=12)
    assert "INV-1" in out
    assert "Ramesh" in out
    assert "100.00" in out


def test_t_format_missing_arg_returns_unformatted():
    # Missing format args shouldn't raise — should return the raw template
    out = t("invoice_done", "en")
    assert out  # graceful fallback, not an exception


@pytest.mark.parametrize("text,expected", [
    ("रमेश ट्रेडर्स को 150 किलो कपास का इनवॉइस बनाओ", "hi"),
    ("ரமேஷ் ட்ரேடர்ஸுக்கு 150 கிலோ பருத்தி", "ta"),
    ("രമേഷ് ട്രേഡേഴ്സിന് 150 കിലോ പഞ്ഞി", "ml"),
    ("রমেশ ট্রেডার্সের জন্য 150 কেজি তুলা", "bn"),
    ("Ramesh Traders ka invoice banao 150kg cotton", None),  # Latin dominant
    ("", None),
    ("12345 !!!", None),
])
def test_detect_script_language(text, expected):
    assert detect_script_language(text) == expected


def test_detect_script_mixed_hindi_english():
    """Hinglish with Devanagari should still detect as hi."""
    assert detect_script_language("Ramesh को 150 किलो चाहिए") == "hi"


def test_lang_names_in_native_script():
    """Each LANG_NAME should be in its own script (sanity check)."""
    assert LANG_NAMES["hi"] == "हिंदी"
    assert LANG_NAMES["ta"] == "தமிழ்"
    assert LANG_NAMES["ml"] == "മലയാളം"
    assert LANG_NAMES["bn"] == "বাংলা"
    assert LANG_NAMES["mr"] == "मराठी"
    assert LANG_NAMES["en"] == "English"
