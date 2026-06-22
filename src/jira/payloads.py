from __future__ import annotations
from src.intake.models import NormalizedEmail, ClassificationResult
from src.intake.security import safe_excerpt

DEFAULT_ISSUE_TYPES = {"CI Failure":"Bug","Incident / Support":"Incident","Organizational Mail":"Task","Needs Manual Triage":"Task"}
DEFAULT_PRIORITIES = {"CI Failure":"High","Incident / Support":"High","Organizational Mail":"Low","Needs Manual Triage":"Medium"}

def adf(text: str) -> dict:
    return {"type":"doc","version":1,"content":[{"type":"paragraph","content":[{"type":"text","text": text}]}]}

def build_issue_payload(email: NormalizedEmail, classification: ClassificationResult, config: dict) -> dict:
    project_key = config["jira"]["project_key"]
    issue_types = {**DEFAULT_ISSUE_TYPES, **config.get("jira", {}).get("issue_type_mapping", {})}
    priorities = {**DEFAULT_PRIORITIES, **config.get("jira", {}).get("priority_mapping", {})}
    fields = {
        "project": {"key": project_key},
        "issuetype": {"name": issue_types.get(classification.category, "Task")},
        "summary": f"[{classification.category}] {email.subject}"[:255],
        "description": adf(f"Request captured from Outlook intake.\n\nRequester: {email.sender_email}\nCategory: {classification.category}\nReason: {classification.reason}\n\n{safe_excerpt(email.body)}"),
        "priority": {"name": priorities.get(classification.category, "Medium")},
        "labels": ["devops-intake", classification.category.lower().replace(" / ", "-").replace(" ", "-")],
    }
    for name, value in config.get("jira", {}).get("custom_field_mapping", {}).items():
        if name in classification.extracted_fields:
            fields[value] = classification.extracted_fields[name]
    return {"fields": fields}
