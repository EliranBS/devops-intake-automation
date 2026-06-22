from __future__ import annotations

import json
from pathlib import Path

from src.classifier.rules import classify_email
from src.correlation.strategy import InMemoryCorrelationStore, correlate
from src.intake.models import IntakeDecision
from src.outlook.normalizer import normalize_outlook_message


def process_message(payload: dict, source_mailbox: str, store: InMemoryCorrelationStore) -> IntakeDecision:
    email = normalize_outlook_message(payload, source_mailbox)
    classification = classify_email(email)
    action, jira_key, duplicate_of, fp = correlate(email, classification, store)
    return IntakeDecision(action, classification.category, jira_key, duplicate_of, fp, classification)


def run_fixture_demo(fixtures_dir: Path | None = None, source_mailbox: str = "devops-intake@example.com") -> list[IntakeDecision]:
    repo_root = Path(__file__).resolve().parents[2]
    fixture_root = fixtures_dir or repo_root / "tests" / "fixtures"
    store = InMemoryCorrelationStore()
    decisions: list[IntakeDecision] = []
    for fixture_path in sorted(fixture_root.glob("*.json")):
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        decision = process_message(payload, source_mailbox, store)
        decisions.append(decision)
        print(f"{fixture_path.name}\t{decision.action}\t{decision.category}\tmissing={decision.classification.missing_fields}")
    return decisions


if __name__ == "__main__":
    run_fixture_demo()
