from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from src.intake.models import ClassificationResult, NormalizedEmail
from src.jira.keys import find_jira_keys

THREAD_PREFIX_RE = re.compile(r"^\s*((re|fw|fwd)\s*:\s*)+", re.IGNORECASE)
JIRA_KEY_INLINE_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b", re.IGNORECASE)


@dataclass
class InMemoryCorrelationStore:
    by_message: dict[str, str] = field(default_factory=dict)
    by_conversation: dict[str, str] = field(default_factory=dict)
    by_fingerprint: dict[str, str] = field(default_factory=dict)


def normalize_subject_for_fingerprint(subject: str) -> str:
    normalized = THREAD_PREFIX_RE.sub("", subject or "")
    normalized = JIRA_KEY_INLINE_RE.sub("", normalized)
    return re.sub(r"\s+", " ", normalized.lower()).strip(" -:[]")


def normalized_fingerprint(email: NormalizedEmail, classification: ClassificationResult) -> str:
    parts = [
        email.source_mailbox,
        classification.category,
        str(classification.extracted_fields.get("project", "")).lower(),
        email.sender_email.lower(),
        str(classification.extracted_fields.get("build_url", "")).lower(),
        normalize_subject_for_fingerprint(email.subject),
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def message_key(email: NormalizedEmail) -> str | None:
    mid = email.internet_message_id or email.immutable_message_id or email.message_id
    return f"{email.source_mailbox}:{mid}" if mid else None


def conversation_key(email: NormalizedEmail) -> str | None:
    return f"{email.source_mailbox}:conversation:{email.conversation_id}" if email.conversation_id else None


def correlate(email: NormalizedEmail, classification: ClassificationResult, store: InMemoryCorrelationStore) -> tuple[str, str | None, str | None, str]:
    jira_keys = find_jira_keys(email.subject, email.body)
    fp = normalized_fingerprint(email, classification)
    if jira_keys:
        return "update", jira_keys[0], None, fp

    mk = message_key(email)
    ck = conversation_key(email)
    if mk and mk in store.by_message:
        return "duplicate", None, store.by_message[mk], fp
    if ck and ck in store.by_conversation:
        return "duplicate", None, store.by_conversation[ck], fp
    if fp in store.by_fingerprint:
        return "duplicate", None, store.by_fingerprint[fp], fp

    intake_id = hashlib.sha1((mk or ck or fp).encode()).hexdigest()[:12]
    if mk:
        store.by_message[mk] = intake_id
    if ck:
        store.by_conversation[ck] = intake_id
    store.by_fingerprint[fp] = intake_id
    return "create", None, None, fp
