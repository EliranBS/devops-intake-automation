from __future__ import annotations
from datetime import datetime
import re
from html import unescape
from src.intake.models import AttachmentMetadata, NormalizedEmail
from src.intake.security import redact_mapping, redact_secrets

URL_RE = re.compile(r"https?://[^\s<>'\"]+")

def _addr(item: dict) -> str:
    return (((item or {}).get("emailAddress") or {}).get("address") or "").lower()

def _display(item: dict) -> str | None:
    return ((item or {}).get("emailAddress") or {}).get("name")

def _body(payload: dict) -> str:
    body = (payload.get("body") or {}).get("content") or payload.get("bodyPreview") or ""
    return redact_secrets(unescape(re.sub(r"<[^>]+>", " ", body)))

def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def normalize_outlook_message(payload: dict, source_mailbox: str) -> NormalizedEmail:
    subject = payload.get("subject") or ""
    body = _body(payload)
    text_for_links = f"{subject}\n{body}\n{payload.get('bodyPreview') or ''}"
    recipients = [_addr(r) for r in (payload.get("toRecipients") or []) + (payload.get("ccRecipients") or []) if _addr(r)]
    attachments = [AttachmentMetadata(
        name=a.get("name") or "attachment",
        content_type=a.get("contentType"),
        size=a.get("size"),
        is_inline=bool(a.get("isInline", False)),
    ) for a in payload.get("attachments", [])]
    return NormalizedEmail(
        source_mailbox=source_mailbox.lower(),
        sender_email=_addr(payload.get("from") or payload.get("sender") or {}),
        sender_display_name=_display(payload.get("from") or payload.get("sender") or {}),
        recipients=recipients,
        subject=subject.strip(),
        body_preview=redact_secrets(payload.get("bodyPreview") or body[:250]),
        body=body,
        message_id=payload.get("id"),
        immutable_message_id=payload.get("immutableId") or payload.get("immutableMessageId"),
        internet_message_id=payload.get("internetMessageId"),
        conversation_id=payload.get("conversationId"),
        received_datetime=_dt(payload.get("receivedDateTime")),
        attachments=attachments,
        links=sorted(set(URL_RE.findall(text_for_links))),
        raw=redact_mapping(payload),
    )
