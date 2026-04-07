"""FinanceAI — WhatsApp-Native GST Invoice Bot."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from adapters.web import router as web_router
from adapters.whatsapp import router as wa_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(
    title="FinanceAI",
    description="WhatsApp-native GST invoice bot powered by Sarvam AI",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(web_router)
app.include_router(wa_router)

# Static files (landing page + chat UI) — mounted last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
