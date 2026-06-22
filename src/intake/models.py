from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass(frozen=True)
class AttachmentMetadata:
    name: str
    content_type: str | None = None
    size: int | None = None
    is_inline: bool = False

@dataclass(frozen=True)
class NormalizedEmail:
    source_mailbox: str
    sender_email: str
    sender_display_name: str | None
    recipients: list[str]
    subject: str
    body_preview: str
    body: str
    message_id: str | None
    immutable_message_id: str | None
    internet_message_id: str | None
    conversation_id: str | None
    received_datetime: datetime | None
    attachments: list[AttachmentMetadata] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

@dataclass(frozen=True)
class ClassificationResult:
    category: str
    confidence: float
    reason: str
    extracted_fields: dict[str, Any]
    missing_fields: list[str]
    classifier_version: str = "rules-v1"

@dataclass(frozen=True)
class IntakeDecision:
    action: str
    category: str
    jira_key: str | None
    duplicate_of: str | None
    fingerprint: str
    classification: ClassificationResult
