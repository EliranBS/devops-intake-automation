import json
from pathlib import Path

from src.classifier.rules import classify_email
from src.correlation.strategy import SQLiteCorrelationStore, correlate
from src.outlook.normalizer import normalize_outlook_message

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def classify_payload(payload, mailbox="devops@example.com"):
    email = normalize_outlook_message(payload, mailbox)
    return email, classify_email(email)


def test_sqlite_duplicate_detection_survives_store_recreation(tmp_path):
    db_path = tmp_path / "correlation.sqlite3"
    email, cls = classify_payload(load("vm_request.json"), "m")

    first_store = SQLiteCorrelationStore(db_path)
    first = correlate(email, cls, first_store)
    first_store.close()

    restarted_store = SQLiteCorrelationStore(db_path)
    second = correlate(email, cls, restarted_store)
    restarted_store.close()

    assert first[0] == "create"
    assert second[0] == "duplicate"
    assert second[2] is not None


def test_sqlite_conversation_id_suppresses_duplicate_after_restart(tmp_path):
    db_path = tmp_path / "correlation.sqlite3"
    first_email, first_cls = classify_payload(load("vm_request.json"), "m")
    first_store = SQLiteCorrelationStore(db_path)
    first = correlate(first_email, first_cls, first_store)
    first_store.close()

    reply_payload = load("vm_request.json") | {
        "id": "different-message-id",
        "internetMessageId": "<different-internet-message-id@example>",
        "subject": "Re: VM request for analytics",
    }
    reply_email, reply_cls = classify_payload(reply_payload, "m")
    restarted_store = SQLiteCorrelationStore(db_path)
    second = correlate(reply_email, reply_cls, restarted_store)
    restarted_store.close()

    assert first[0] == "create"
    assert second[0] == "duplicate"
    assert second[2] is not None


def test_sqlite_fingerprint_suppresses_duplicate_after_restart(tmp_path):
    db_path = tmp_path / "correlation.sqlite3"
    first_payload = load("vm_request.json") | {"conversationId": "thread-one", "internetMessageId": "<one@example>"}
    first_email, first_cls = classify_payload(first_payload, "m")
    first_store = SQLiteCorrelationStore(db_path)
    first = correlate(first_email, first_cls, first_store)
    first_store.close()

    same_request_payload = load("vm_request.json") | {"id": "new-id", "conversationId": "thread-two", "internetMessageId": "<two@example>"}
    same_request_email, same_request_cls = classify_payload(same_request_payload, "m")
    restarted_store = SQLiteCorrelationStore(db_path)
    second = correlate(same_request_email, same_request_cls, restarted_store)
    restarted_store.close()

    assert first[0] == "create"
    assert second[0] == "duplicate"
    assert second[2] is not None
