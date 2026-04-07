"""Base message adapter — abstract interface for all surfaces."""

from abc import ABC, abstractmethod
from models.invoice import BotResponse, IncomingMessage


class MessageAdapter(ABC):
    """Adapter interface. Each surface (web, WhatsApp) implements this."""

    @abstractmethod
    async def parse_incoming(self, raw_data: dict) -> IncomingMessage:
        """Parse raw request data into an IncomingMessage."""
        ...

    @abstractmethod
    async def send_response(self, response: BotResponse, recipient: str) -> None:
        """Send a BotResponse back to the user."""
        ...
