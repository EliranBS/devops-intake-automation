from __future__ import annotations

from src.intake.models import ClassificationResult


def _missing_list(classification: ClassificationResult | None) -> str:
    missing = classification.missing_fields if classification else []
    return "\n".join(f"- {field}" for field in missing) if missing else "- Additional details requested by DevOps"


def render_reply(
    kind: str,
    requester: str,
    jira_key: str | None = None,
    classification: ClassificationResult | None = None,
    duplicate_of: str | None = None,
) -> str:
    greeting = f"Hello {requester or 'there'},"
    category = classification.category if classification else "request"
    ticket = jira_key or "the Jira ticket"

    if kind == "created":
        return f"{greeting}\n\nYour {category} has been captured as {ticket}. Please use that Jira issue for updates and avoid sending secrets in email replies."
    if kind == "missing_info":
        return f"{greeting}\n\nWe received your {category}, but need the following information before DevOps can proceed:\n{_missing_list(classification)}\n\nPlease reply with only the requested business/technical details and do not include passwords, tokens, or private keys."
    if kind == "duplicate":
        return f"{greeting}\n\nThis appears to duplicate an existing intake request ({duplicate_of or 'already tracked'}). We will keep work consolidated there to avoid duplicate Jira issues."
    if kind == "rejected":
        return f"{greeting}\n\nYour request was rejected or cannot proceed as submitted. Please review the Jira comments for the reason and next steps."
    if kind == "approval_required":
        return f"{greeting}\n\nYour {category} requires approval before DevOps can proceed. The ticket will remain waiting for approval until an authorized approver responds."
    if kind == "automation_failed":
        return f"{greeting}\n\nAutomation failed safely and no destructive retry was attempted. A DevOps engineer has been notified and will continue from {ticket}."
    if kind == "completed":
        return f"{greeting}\n\nYour ticket {ticket} has been completed. Please reopen or reply on the Jira issue if the outcome is not correct."
    raise ValueError(f"unknown reply kind: {kind}")
