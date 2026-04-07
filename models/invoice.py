from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field


# --- Invoice Models ---

class LineItem(BaseModel):
    description: str
    quantity: float
    unit: str = "pcs"
    rate: float

    @computed_field
    @property
    def amount(self) -> float:
        return round(self.quantity * self.rate, 2)


class Invoice(BaseModel):
    invoice_number: str = ""
    date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    seller_gstin: str = ""
    seller_name: str = ""
    buyer_name: str = ""
    buyer_gstin: str = ""
    items: list[LineItem] = []
    gst_rate: float = 0.0
    notes: str = ""

    @computed_field
    @property
    def subtotal(self) -> float:
        return round(sum(item.amount for item in self.items), 2)

    @computed_field
    @property
    def is_interstate(self) -> bool:
        """True if buyer is in a different state than seller → IGST. False → CGST + SGST."""
        if not self.buyer_gstin or not self.seller_gstin:
            return False  # default to intra-state
        return self.seller_gstin[:2] != self.buyer_gstin[:2]

    @computed_field
    @property
    def gst_amount(self) -> float:
        return round(self.subtotal * self.gst_rate / 100, 2)

    @computed_field
    @property
    def cgst(self) -> float:
        return round(self.gst_amount / 2, 2) if not self.is_interstate else 0.0

    @computed_field
    @property
    def sgst(self) -> float:
        return round(self.gst_amount / 2, 2) if not self.is_interstate else 0.0

    @computed_field
    @property
    def igst(self) -> float:
        return self.gst_amount if self.is_interstate else 0.0

    @computed_field
    @property
    def total(self) -> float:
        return round(self.subtotal + self.gst_amount, 2)


# --- Extraction Result ---

class ExtractionResult(BaseModel):
    buyer_name: str = ""
    amount: Optional[float] = None
    items: list[LineItem] = []
    gst_rate: Optional[float] = None
    buyer_gstin: str = ""
    notes: str = ""


# --- Session / State Machine ---

class FlowState(str, Enum):
    IDLE = "IDLE"
    EXTRACTING = "EXTRACTING"
    AWAITING_FIELDS = "AWAITING_FIELDS"
    CONFIRMING = "CONFIRMING"
    GENERATING = "GENERATING"
    DONE = "DONE"


class Session(BaseModel):
    session_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    state: FlowState = FlowState.IDLE
    invoice: Invoice = Field(default_factory=Invoice)
    missing_fields: list[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    def touch(self):
        self.updated_at = datetime.now().isoformat()


# --- Message ---

class MessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    BUTTON = "button"


class IncomingMessage(BaseModel):
    session_id: str
    type: MessageType = MessageType.TEXT
    text: str = ""
    audio_data: Optional[bytes] = None
    audio_filename: str = "audio.webm"
    button_payload: str = ""

    model_config = {"arbitrary_types_allowed": True}


class BotResponse(BaseModel):
    text: str
    pdf_bytes: Optional[bytes] = None
    buttons: list[dict] = []

    model_config = {"arbitrary_types_allowed": True}
