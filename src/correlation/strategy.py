from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from src.intake.models import ClassificationResult, NormalizedEmail
from src.jira.keys import find_jira_keys

THREAD_PREFIX_RE = re.compile(r"^\s*((re|fw|fwd)\s*:\s*)+", re.IGNORECASE)
JIRA_KEY_INLINE_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b", re.IGNORECASE)
DEFAULT_DB_PATH = Path(".data") / "correlation.sqlite3"
DB_PATH_ENV_VAR = "INTAKE_CORRELATION_DB_PATH"


@dataclass(frozen=True)
class CorrelationRecord:
    intake_id: str
    mailbox: str
    message_id: str | None
    internet_message_id: str | None
    conversation_id: str | None
    normalized_fingerprint: str
    detected_jira_key: str | None
    category: str
    requester: str
    created_timestamp: datetime
    last_seen_timestamp: datetime


class CorrelationStore(Protocol):
    def find_duplicate(self, email: NormalizedEmail, fingerprint: str) -> str | None: ...
    def record_seen(self, email: NormalizedEmail, classification: ClassificationResult, fingerprint: str, detected_jira_key: str | None = None) -> str: ...


@dataclass
class InMemoryCorrelationStore:
    by_message: dict[str, str] = field(default_factory=dict)
    by_conversation: dict[str, str] = field(default_factory=dict)
    by_fingerprint: dict[str, str] = field(default_factory=dict)
    records: dict[str, CorrelationRecord] = field(default_factory=dict)

    def find_duplicate(self, email: NormalizedEmail, fingerprint: str) -> str | None:
        mk = message_key(email)
        ck = conversation_key(email)
        if mk and mk in self.by_message:
            return self.by_message[mk]
        if ck and ck in self.by_conversation:
            return self.by_conversation[ck]
        return self.by_fingerprint.get(fingerprint)

    def record_seen(self, email: NormalizedEmail, classification: ClassificationResult, fingerprint: str, detected_jira_key: str | None = None) -> str:
        intake_id = make_intake_id(email, fingerprint)
        now = datetime.now(UTC)
        existing = self.records.get(intake_id)
        self.records[intake_id] = CorrelationRecord(
            intake_id=intake_id,
            mailbox=email.source_mailbox,
            message_id=email.message_id or email.immutable_message_id,
            internet_message_id=email.internet_message_id,
            conversation_id=email.conversation_id,
            normalized_fingerprint=fingerprint,
            detected_jira_key=detected_jira_key,
            category=classification.category,
            requester=email.sender_email,
            created_timestamp=existing.created_timestamp if existing else now,
            last_seen_timestamp=now,
        )
        mk = message_key(email)
        ck = conversation_key(email)
        if mk:
            self.by_message[mk] = intake_id
        if ck:
            self.by_conversation[ck] = intake_id
        self.by_fingerprint[fingerprint] = intake_id
        return intake_id


class SQLiteCorrelationStore:
    """SQLite-backed local durable correlation store."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or os.getenv(DB_PATH_ENV_VAR) or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA busy_timeout=30000")
        self._init_schema()

    def close(self) -> None:
        self._connection.close()

    def _init_schema(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS correlation_records (
                intake_id TEXT PRIMARY KEY,
                mailbox TEXT NOT NULL,
                message_id TEXT,
                internet_message_id TEXT,
                conversation_id TEXT,
                normalized_fingerprint TEXT NOT NULL,
                detected_jira_key TEXT,
                category TEXT NOT NULL,
                requester TEXT NOT NULL,
                created_timestamp TEXT NOT NULL,
                last_seen_timestamp TEXT NOT NULL
            )
            """
        )
        self._connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_corr_message ON correlation_records(mailbox, message_id) WHERE message_id IS NOT NULL")
        self._connection.execute("CREATE INDEX IF NOT EXISTS ix_corr_internet_message ON correlation_records(mailbox, internet_message_id) WHERE internet_message_id IS NOT NULL")
        self._connection.execute("CREATE INDEX IF NOT EXISTS ix_corr_conversation ON correlation_records(mailbox, conversation_id) WHERE conversation_id IS NOT NULL")
        self._connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_corr_fingerprint ON correlation_records(mailbox, normalized_fingerprint)")

    def find_duplicate(self, email: NormalizedEmail, fingerprint: str) -> str | None:
        candidates = [
            ("message_id = ?", email.internet_message_id or email.immutable_message_id or email.message_id),
            ("internet_message_id = ?", email.internet_message_id),
            ("conversation_id = ?", email.conversation_id),
            ("normalized_fingerprint = ?", fingerprint),
        ]
        for clause, value in candidates:
            if not value:
                continue
            row = self._connection.execute(
                f"SELECT intake_id FROM correlation_records WHERE mailbox = ? AND {clause} ORDER BY created_timestamp LIMIT 1",
                (email.source_mailbox, value),
            ).fetchone()
            if row:
                self._touch(row[0])
                return str(row[0])
        return None

    def record_seen(self, email: NormalizedEmail, classification: ClassificationResult, fingerprint: str, detected_jira_key: str | None = None) -> str:
        intake_id = make_intake_id(email, fingerprint)
        now = datetime.now(UTC).isoformat()
        msg_id = email.internet_message_id or email.immutable_message_id or email.message_id
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            self._connection.execute(
                """
                INSERT INTO correlation_records (
                    intake_id, mailbox, message_id, internet_message_id, conversation_id,
                    normalized_fingerprint, detected_jira_key, category, requester,
                    created_timestamp, last_seen_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(intake_id) DO UPDATE SET last_seen_timestamp=excluded.last_seen_timestamp,
                    detected_jira_key=COALESCE(excluded.detected_jira_key, correlation_records.detected_jira_key)
                """,
                (intake_id, email.source_mailbox, msg_id, email.internet_message_id, email.conversation_id,
                 fingerprint, detected_jira_key, classification.category, email.sender_email, now, now),
            )
            self._connection.execute("COMMIT")
        except sqlite3.IntegrityError:
            self._connection.execute("ROLLBACK")
            duplicate = self.find_duplicate(email, fingerprint)
            if duplicate:
                return duplicate
            raise
        except Exception:
            self._connection.execute("ROLLBACK")
            raise
        return intake_id

    def _touch(self, intake_id: str) -> None:
        self._connection.execute("UPDATE correlation_records SET last_seen_timestamp = ? WHERE intake_id = ?", (datetime.now(UTC).isoformat(), intake_id))


def correlation_db_path_from_env() -> Path:
    return Path(os.getenv(DB_PATH_ENV_VAR) or DEFAULT_DB_PATH)


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


def make_intake_id(email: NormalizedEmail, fingerprint: str) -> str:
    mk = message_key(email)
    ck = conversation_key(email)
    return hashlib.sha1((mk or ck or fingerprint).encode()).hexdigest()[:12]


def correlate(email: NormalizedEmail, classification: ClassificationResult, store: CorrelationStore) -> tuple[str, str | None, str | None, str]:
    jira_keys = find_jira_keys(email.subject, email.body)
    fp = normalized_fingerprint(email, classification)
    if jira_keys:
        store.record_seen(email, classification, fp, detected_jira_key=jira_keys[0])
        return "update", jira_keys[0], None, fp

    duplicate_of = store.find_duplicate(email, fp)
    if duplicate_of:
        return "duplicate", None, duplicate_of, fp

    store.record_seen(email, classification, fp)
    return "create", None, None, fp
