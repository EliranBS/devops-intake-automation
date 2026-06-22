from __future__ import annotations
import hashlib, re
from dataclasses import dataclass, field
from src.intake.models import NormalizedEmail, ClassificationResult
from src.jira.keys import find_jira_keys

@dataclass
class InMemoryCorrelationStore:
    by_message: dict[str, str] = field(default_factory=dict)
    by_fingerprint: dict[str, str] = field(default_factory=dict)

def normalized_fingerprint(email: NormalizedEmail, classification: ClassificationResult) -> str:
    parts = [email.source_mailbox, classification.category, classification.extracted_fields.get("project", ""), email.sender_email,
             classification.extracted_fields.get("build_url", ""), re.sub(r"\s+", " ", email.subject.lower()).strip()]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()

def message_key(email: NormalizedEmail) -> str | None:
    mid = email.internet_message_id or email.immutable_message_id or email.message_id
    return f"{email.source_mailbox}:{mid}" if mid else None

def correlate(email: NormalizedEmail, classification: ClassificationResult, store: InMemoryCorrelationStore) -> tuple[str, str | None, str | None, str]:
    jira_keys = find_jira_keys(email.subject, email.body)
    fp = normalized_fingerprint(email, classification)
    if jira_keys:
        return "update", jira_keys[0], None, fp
    mk = message_key(email)
    if mk and mk in store.by_message:
        return "duplicate", None, store.by_message[mk], fp
    if fp in store.by_fingerprint:
        return "duplicate", None, store.by_fingerprint[fp], fp
    intake_id = hashlib.sha1((mk or fp).encode()).hexdigest()[:12]
    if mk:
        store.by_message[mk] = intake_id
    store.by_fingerprint[fp] = intake_id
    return "create", None, None, fp
