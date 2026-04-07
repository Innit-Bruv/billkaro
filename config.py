from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Sarvam AI
    sarvam_api_key: str = ""
    sarvam_stt_url: str = "https://api.sarvam.ai/speech-to-text"
    sarvam_chat_url: str = "https://api.sarvam.ai/v1/chat/completions"
    sarvam_stt_model: str = "saaras:v3"
    sarvam_chat_model: str = "sarvam-30b"

    # WhatsApp Cloud API
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "billkaro-verify"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Seller info (used in GST invoices)
    seller_name: str = "BillKaro Demo Pvt Ltd"
    seller_gstin: str = "27AADCB2230M1ZT"  # Maharashtra demo GSTIN

    # App
    app_name: str = "BillKaro"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
