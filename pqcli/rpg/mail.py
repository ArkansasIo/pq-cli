from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class MailAttachment:
    item_id: str
    quantity: int = 1


@dataclass
class MailMessage:
    mail_id: str
    sender_id: str
    recipient_id: str
    subject: str
    body: str
    attachments: list[MailAttachment] = field(default_factory=list)
    sent_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    read: bool = False


class MailService:
    def __init__(self) -> None:
        self.messages: dict[str, MailMessage] = {}

    def send(self, message: MailMessage) -> None:
        if not message.recipient_id or not message.sender_id:
            raise ValueError("sender and recipient are required")
        self.messages[message.mail_id] = message

    def inbox(self, recipient_id: str) -> list[MailMessage]:
        return [m for m in self.messages.values() if m.recipient_id == recipient_id]

    def mark_read(self, mail_id: str) -> None:
        self.messages[mail_id].read = True
