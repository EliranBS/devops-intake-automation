from src.classifier.rules import classify_email
from src.correlation.strategy import InMemoryCorrelationStore, correlate
from src.intake.models import IntakeDecision
from src.outlook.normalizer import normalize_outlook_message

def process_message(payload: dict, source_mailbox: str, store: InMemoryCorrelationStore) -> IntakeDecision:
    email = normalize_outlook_message(payload, source_mailbox)
    classification = classify_email(email)
    action, jira_key, duplicate_of, fp = correlate(email, classification, store)
    return IntakeDecision(action, classification.category, jira_key, duplicate_of, fp, classification)
