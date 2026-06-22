from src.intake.models import ClassificationResult

def render_reply(kind: str, requester: str, jira_key: str | None = None, classification: ClassificationResult | None = None, duplicate_of: str | None = None) -> str:
    greeting = f"Hello {requester or 'there'},"
    if kind == "created": return f"{greeting}\n\nYour request has been captured as {jira_key}. We will track updates in Jira."
    if kind == "missing_info": return f"{greeting}\n\nWe need more information before proceeding with your {classification.category if classification else 'request'}:\n- " + "\n- ".join(classification.missing_fields if classification else [])
    if kind == "duplicate": return f"{greeting}\n\nThis appears to duplicate an existing intake request ({duplicate_of}). We will keep work consolidated there."
    if kind == "rejected": return f"{greeting}\n\nYour request was rejected. Please review the Jira comments for details."
    if kind == "approval_required": return f"{greeting}\n\nYour request requires approval before DevOps can proceed."
    if kind == "automation_failed": return f"{greeting}\n\nAutomation failed safely. A DevOps engineer has been notified."
    if kind == "completed": return f"{greeting}\n\nYour ticket {jira_key or ''} has been completed."
    raise ValueError(f"unknown reply kind: {kind}")
