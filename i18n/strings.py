"""Localised UI strings for BillKaro.

Setup flow stays in English (we don't know the seller's language until they
send their first invoice input). Everything after language confirmation
routes through ``t(key, lang)``. Missing keys fall back to English so the
bot is never silent.

Translations are Claude-authored baselines. Verify via Sarvam Translate or a
native speaker before demo — see TODOS.md.
"""

from __future__ import annotations


# Native-script language names shown to the user in the confirmation prompt.
LANG_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "हिंदी",
    "ta": "தமிழ்",
    "ml": "മലയാളം",
    "bn": "বাংলা",
    "mr": "मराठी",
}


STRINGS: dict[str, dict[str, str]] = {
    # --- English (canonical, used as fallback) ---
    "en": {
        "lang_confirm": "I'll reply in English. Tap below to switch.",
        "btn_lang_keep": "Keep English",
        "btn_lang_switch": "Switch language",
        "lang_set": "Done. I'll reply in English from now on.",
        "reset_ack": "Session reset. Send a voice note or text to create a new invoice.",
        "input_unclear": "I couldn't understand that. Please send a voice note or text with invoice details.",
        "missing_prompt": "Almost there! I need a few more details.\n\nPlease provide the **{field}**:",
        "missing_next": "Got it. Now please provide the **{field}**:",
        "field_buyer": "buyer name",
        "field_items": "item details (description, quantity, rate)",
        "field_gst": "GST rate (enter 5, 12, 18, or 28)",
        "edit_ack": "No problem. Send me the updated details and I'll create a new draft.",
        "new_ack": "Ready for a new invoice. Send me details via voice or text.",
        "btn_fallback": "Please confirm or edit the current draft.",
        "busy": "Processing your previous request. Please wait...",
        "pdf_fail": "Failed to generate PDF. Please try confirming again.",
        "invoice_done": "Invoice **{number}** generated for **{buyer}**.\nTotal: Rs. {total} (incl. {rate}% GST)",
        "btn_confirm": "Confirm",
        "btn_edit": "Edit",
        "btn_new": "New Invoice",
        "draft_header": "Invoice Draft",
        "draft_buyer": "Buyer",
        "draft_gstin": "GSTIN",
        "draft_gstin_none": "Not provided",
        "draft_items": "Items",
        "draft_subtotal": "Subtotal",
        "draft_gst": "GST",
        "draft_total": "Total",
    },

    # --- Hindi (हिंदी) ---
    "hi": {
        "lang_confirm": "मैं हिंदी में जवाब दूं?",
        "btn_lang_keep": "हां, हिंदी में",
        "btn_lang_switch": "भाषा बदलें",
        "lang_set": "हो गया। अब मैं हिंदी में जवाब दूंगा।",
        "reset_ack": "सेशन रीसेट हो गया। नया इनवॉइस बनाने के लिए वॉइस नोट या टेक्स्ट भेजें।",
        "input_unclear": "मुझे समझ नहीं आया। कृपया इनवॉइस के डिटेल्स वॉइस या टेक्स्ट में भेजें।",
        "missing_prompt": "लगभग हो गया! कुछ और डिटेल्स चाहिए।\n\nकृपया **{field}** बताएं:",
        "missing_next": "ठीक है। अब कृपया **{field}** बताएं:",
        "field_buyer": "खरीदार का नाम",
        "field_items": "आइटम डिटेल्स (सामान, मात्रा, रेट)",
        "field_gst": "GST दर (5, 12, 18 या 28 डालें)",
        "edit_ack": "कोई बात नहीं। नई डिटेल्स भेजें और मैं नया ड्राफ्ट बनाऊंगा।",
        "new_ack": "नए इनवॉइस के लिए तैयार। वॉइस या टेक्स्ट में डिटेल्स भेजें।",
        "btn_fallback": "कृपया मौजूदा ड्राफ्ट को कन्फर्म या एडिट करें।",
        "busy": "आपकी पिछली रिक्वेस्ट प्रोसेस हो रही है। कृपया रुकें...",
        "pdf_fail": "PDF नहीं बन पाई। कृपया फिर से कन्फर्म करें।",
        "invoice_done": "इनवॉइस **{number}** **{buyer}** के लिए बन गई।\nकुल: Rs. {total} ({rate}% GST सहित)",
        "btn_confirm": "कन्फर्म",
        "btn_edit": "एडिट",
        "btn_new": "नया इनवॉइस",
        "draft_header": "इनवॉइस ड्राफ्ट",
        "draft_buyer": "खरीदार",
        "draft_gstin": "GSTIN",
        "draft_gstin_none": "नहीं दिया गया",
        "draft_items": "सामान",
        "draft_subtotal": "सब-टोटल",
        "draft_gst": "GST",
        "draft_total": "कुल",
    },

    # --- Tamil (தமிழ்) ---
    "ta": {
        "lang_confirm": "நான் தமிழில் பதில் சொல்லட்டுமா?",
        "btn_lang_keep": "ஆம், தமிழில்",
        "btn_lang_switch": "மொழி மாற்று",
        "lang_set": "சரி. இனி தமிழில் பதில் சொல்கிறேன்.",
        "reset_ack": "செஷன் ரீசெட் ஆகிவிட்டது. புதிய இன்வாய்ஸ் உருவாக்க குரல் குறிப்பு அல்லது உரையை அனுப்புங்கள்.",
        "input_unclear": "புரியவில்லை. தயவுசெய்து இன்வாய்ஸ் விவரங்களை குரல் அல்லது உரையாக அனுப்புங்கள்.",
        "missing_prompt": "கிட்டத்தட்ட முடிந்தது! இன்னும் சில விவரங்கள் தேவை.\n\nதயவுசெய்து **{field}** கொடுங்கள்:",
        "missing_next": "சரி. இப்போது தயவுசெய்து **{field}** கொடுங்கள்:",
        "field_buyer": "வாங்குபவர் பெயர்",
        "field_items": "பொருள் விவரங்கள் (விளக்கம், அளவு, விலை)",
        "field_gst": "GST விகிதம் (5, 12, 18 அல்லது 28 உள்ளிடவும்)",
        "edit_ack": "பரவாயில்லை. புதுப்பிக்கப்பட்ட விவரங்களை அனுப்புங்கள், நான் புதிய வரைவை உருவாக்குகிறேன்.",
        "new_ack": "புதிய இன்வாய்ஸுக்கு தயார். குரல் அல்லது உரையில் விவரங்களை அனுப்புங்கள்.",
        "btn_fallback": "தயவுசெய்து தற்போதைய வரைவை உறுதிப்படுத்துங்கள் அல்லது திருத்துங்கள்.",
        "busy": "உங்கள் முந்தைய கோரிக்கை செயலாக்கப்படுகிறது. காத்திருக்கவும்...",
        "pdf_fail": "PDF உருவாக்க முடியவில்லை. மீண்டும் உறுதிப்படுத்த முயற்சிக்கவும்.",
        "invoice_done": "இன்வாய்ஸ் **{number}** **{buyer}** க்கு உருவாக்கப்பட்டது.\nமொத்தம்: Rs. {total} ({rate}% GST உட்பட)",
        "btn_confirm": "உறுதிப்படுத்து",
        "btn_edit": "திருத்து",
        "btn_new": "புதிய இன்வாய்ஸ்",
        "draft_header": "இன்வாய்ஸ் வரைவு",
        "draft_buyer": "வாங்குபவர்",
        "draft_gstin": "GSTIN",
        "draft_gstin_none": "வழங்கப்படவில்லை",
        "draft_items": "பொருட்கள்",
        "draft_subtotal": "கூட்டுத்தொகை",
        "draft_gst": "GST",
        "draft_total": "மொத்தம்",
    },

    # --- Malayalam (മലയാളം) ---
    "ml": {
        "lang_confirm": "ഞാൻ മലയാളത്തിൽ മറുപടി നൽകട്ടെ?",
        "btn_lang_keep": "ശരി, മലയാളത്തിൽ",
        "btn_lang_switch": "ഭാഷ മാറ്റുക",
        "lang_set": "ശരി. ഇനി മുതൽ മലയാളത്തിൽ മറുപടി നൽകാം.",
        "reset_ack": "സെഷൻ റീസെറ്റ് ചെയ്തു. പുതിയ ഇൻവോയ്സ് ഉണ്ടാക്കാൻ വോയ്സ് നോട്ട് അല്ലെങ്കിൽ ടെക്സ്റ്റ് അയയ്ക്കുക.",
        "input_unclear": "മനസ്സിലായില്ല. ദയവായി ഇൻവോയ്സ് വിവരങ്ങൾ വോയ്സ് അല്ലെങ്കിൽ ടെക്സ്റ്റായി അയയ്ക്കുക.",
        "missing_prompt": "ഏകദേശം പൂർത്തിയായി! കുറച്ച് വിവരങ്ങൾ കൂടി വേണം.\n\nദയവായി **{field}** നൽകുക:",
        "missing_next": "ശരി. ഇനി ദയവായി **{field}** നൽകുക:",
        "field_buyer": "വാങ്ങുന്നയാളുടെ പേര്",
        "field_items": "ഇന വിവരങ്ങൾ (വിവരണം, അളവ്, നിരക്ക്)",
        "field_gst": "GST നിരക്ക് (5, 12, 18 അല്ലെങ്കിൽ 28 നൽകുക)",
        "edit_ack": "പ്രശ്നമില്ല. പുതിയ വിവരങ്ങൾ അയയ്ക്കുക, ഞാൻ പുതിയ ഡ്രാഫ്റ്റ് ഉണ്ടാക്കാം.",
        "new_ack": "പുതിയ ഇൻവോയ്സിനായി തയ്യാറാണ്. വോയ്സ് അല്ലെങ്കിൽ ടെക്സ്റ്റായി വിവരങ്ങൾ അയയ്ക്കുക.",
        "btn_fallback": "ദയവായി നിലവിലെ ഡ്രാഫ്റ്റ് സ്ഥിരീകരിക്കുക അല്ലെങ്കിൽ തിരുത്തുക.",
        "busy": "നിങ്ങളുടെ മുൻ അഭ്യർത്ഥന പ്രോസസ്സ് ചെയ്യുന്നു. കാത്തിരിക്കുക...",
        "pdf_fail": "PDF ഉണ്ടാക്കാൻ കഴിഞ്ഞില്ല. വീണ്ടും സ്ഥിരീകരിക്കാൻ ശ്രമിക്കുക.",
        "invoice_done": "ഇൻവോയ്സ് **{number}** **{buyer}** നായി ഉണ്ടാക്കി.\nആകെ: Rs. {total} ({rate}% GST ഉൾപ്പെടെ)",
        "btn_confirm": "സ്ഥിരീകരിക്കുക",
        "btn_edit": "തിരുത്തുക",
        "btn_new": "പുതിയ ഇൻവോയ്സ്",
        "draft_header": "ഇൻവോയ്സ് ഡ്രാഫ്റ്റ്",
        "draft_buyer": "വാങ്ങുന്നയാൾ",
        "draft_gstin": "GSTIN",
        "draft_gstin_none": "നൽകിയിട്ടില്ല",
        "draft_items": "ഇനങ്ങൾ",
        "draft_subtotal": "സബ്ടോട്ടൽ",
        "draft_gst": "GST",
        "draft_total": "ആകെ",
    },

    # --- Bengali (বাংলা) ---
    "bn": {
        "lang_confirm": "আমি কি বাংলায় উত্তর দেব?",
        "btn_lang_keep": "হ্যাঁ, বাংলায়",
        "btn_lang_switch": "ভাষা পরিবর্তন করুন",
        "lang_set": "ঠিক আছে। এখন থেকে আমি বাংলায় উত্তর দেব।",
        "reset_ack": "সেশন রিসেট হয়েছে। নতুন ইনভয়েস তৈরি করতে ভয়েস নোট বা টেক্সট পাঠান।",
        "input_unclear": "বুঝতে পারিনি। অনুগ্রহ করে ইনভয়েসের বিবরণ ভয়েস বা টেক্সট হিসেবে পাঠান।",
        "missing_prompt": "প্রায় হয়ে গেছে! আরও কিছু বিবরণ দরকার।\n\nঅনুগ্রহ করে **{field}** দিন:",
        "missing_next": "ঠিক আছে। এবার অনুগ্রহ করে **{field}** দিন:",
        "field_buyer": "ক্রেতার নাম",
        "field_items": "আইটেমের বিবরণ (বিবরণ, পরিমাণ, দর)",
        "field_gst": "GST হার (5, 12, 18 বা 28 লিখুন)",
        "edit_ack": "কোনো সমস্যা নেই। নতুন বিবরণ পাঠান, আমি নতুন খসড়া তৈরি করব।",
        "new_ack": "নতুন ইনভয়েসের জন্য প্রস্তুত। ভয়েস বা টেক্সটে বিবরণ পাঠান।",
        "btn_fallback": "অনুগ্রহ করে বর্তমান খসড়া নিশ্চিত করুন বা সম্পাদনা করুন।",
        "busy": "আপনার আগের অনুরোধ প্রক্রিয়া করা হচ্ছে। অনুগ্রহ করে অপেক্ষা করুন...",
        "pdf_fail": "PDF তৈরি করা যায়নি। অনুগ্রহ করে আবার নিশ্চিত করুন।",
        "invoice_done": "ইনভয়েস **{number}** **{buyer}** এর জন্য তৈরি হয়েছে।\nমোট: Rs. {total} ({rate}% GST সহ)",
        "btn_confirm": "নিশ্চিত করুন",
        "btn_edit": "সম্পাদনা",
        "btn_new": "নতুন ইনভয়েস",
        "draft_header": "ইনভয়েস খসড়া",
        "draft_buyer": "ক্রেতা",
        "draft_gstin": "GSTIN",
        "draft_gstin_none": "দেওয়া হয়নি",
        "draft_items": "আইটেম",
        "draft_subtotal": "সাব-টোটাল",
        "draft_gst": "GST",
        "draft_total": "মোট",
    },

    # --- Marathi (मराठी) ---
    "mr": {
        "lang_confirm": "मी मराठीत उत्तर देऊ का?",
        "btn_lang_keep": "हो, मराठीत",
        "btn_lang_switch": "भाषा बदला",
        "lang_set": "ठीक आहे. आता मी मराठीत उत्तर देईन.",
        "reset_ack": "सेशन रीसेट झाले. नवीन इनव्हॉइस तयार करण्यासाठी व्हॉइस नोट किंवा टेक्स्ट पाठवा.",
        "input_unclear": "मला समजले नाही. कृपया इनव्हॉइसचे तपशील व्हॉइस किंवा टेक्स्टमध्ये पाठवा.",
        "missing_prompt": "जवळजवळ झाले! आणखी काही तपशील हवेत.\n\nकृपया **{field}** द्या:",
        "missing_next": "ठीक आहे. आता कृपया **{field}** द्या:",
        "field_buyer": "खरेदीदाराचे नाव",
        "field_items": "वस्तूंचे तपशील (वर्णन, प्रमाण, दर)",
        "field_gst": "GST दर (5, 12, 18 किंवा 28 टाका)",
        "edit_ack": "काही हरकत नाही. नवीन तपशील पाठवा, मी नवीन मसुदा तयार करेन.",
        "new_ack": "नवीन इनव्हॉइससाठी तयार. व्हॉइस किंवा टेक्स्टमध्ये तपशील पाठवा.",
        "btn_fallback": "कृपया सध्याचा मसुदा निश्चित करा किंवा संपादित करा.",
        "busy": "तुमची मागील विनंती प्रक्रिया होत आहे. कृपया प्रतीक्षा करा...",
        "pdf_fail": "PDF तयार करता आली नाही. कृपया पुन्हा निश्चित करा.",
        "invoice_done": "इनव्हॉइस **{number}** **{buyer}** साठी तयार झाली.\nएकूण: Rs. {total} ({rate}% GST सह)",
        "btn_confirm": "निश्चित करा",
        "btn_edit": "संपादित करा",
        "btn_new": "नवीन इनव्हॉइस",
        "draft_header": "इनव्हॉइस मसुदा",
        "draft_buyer": "खरेदीदार",
        "draft_gstin": "GSTIN",
        "draft_gstin_none": "दिलेले नाही",
        "draft_items": "वस्तू",
        "draft_subtotal": "उप-बेरीज",
        "draft_gst": "GST",
        "draft_total": "एकूण",
    },
}


def t(key: str, lang: str | None = "en", **fmt) -> str:
    """Look up a localised string. Falls back to English on missing lang/key."""
    code = lang if lang in STRINGS else "en"
    value = STRINGS[code].get(key) or STRINGS["en"].get(key) or key
    if fmt:
        try:
            return value.format(**fmt)
        except (KeyError, IndexError):
            return value
    return value


def detect_script_language(text: str) -> str | None:
    """Detect language from the dominant Unicode script in ``text``.

    Returns a language code (hi/ta/ml/bn/mr) or ``None`` if Latin-dominant.
    Used for typed input where Sarvam STT language metadata is unavailable.
    Hindi and Marathi share Devanagari — we default that bucket to Hindi
    and let the user correct via the switch button if needed.
    """
    counts = {"devanagari": 0, "tamil": 0, "malayalam": 0, "bengali": 0, "latin": 0}
    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:
            counts["devanagari"] += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            counts["tamil"] += 1
        elif 0x0D00 <= cp <= 0x0D7F:
            counts["malayalam"] += 1
        elif 0x0980 <= cp <= 0x09FF:
            counts["bengali"] += 1
        elif 0x0041 <= cp <= 0x007A:
            counts["latin"] += 1

    non_latin = {k: v for k, v in counts.items() if k != "latin"}
    top = max(non_latin, key=non_latin.get)
    if non_latin[top] == 0:
        return None
    return {
        "devanagari": "hi",
        "tamil": "ta",
        "malayalam": "ml",
        "bengali": "bn",
    }[top]
