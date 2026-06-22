from __future__ import annotations
import re
from src.intake.models import ClassificationResult, NormalizedEmail

CATEGORIES = {
    "ci": "CI Failure", "vm": "VM Request", "access": "Access Request", "license": "License Request",
    "project": "New Project Request", "incident": "Incident / Support", "org": "Organizational Mail",
    "general": "General DevOps Support", "triage": "Needs Manual Triage",
}
REQUIRED_FIELDS = {
    "VM Request": ["project", "environment", "os", "cpu", "ram", "disk", "expiry_date", "approver"],
    "CI Failure": ["repository", "branch", "build_url", "ci_tool", "commit_sha"],
    "License Request": ["product", "requester", "justification", "project", "approver"],
    "Access Request": ["system", "access_level", "requester", "justification", "approver"],
    "New Project Request": ["project_name", "owner", "repo_platform", "ci_type", "environment_needs", "approver"],
    "Incident / Support": ["impact", "service", "urgency"],
}

def _has(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)

def _extract(text: str, email: NormalizedEmail) -> dict:
    fields = {"requester": email.sender_email} if email.sender_email else {}
    patterns = {
        "project": r"project\s*[:=-]\s*([\w .-]+)", "environment": r"env(?:ironment)?\s*[:=-]\s*(\w+)",
        "os": r"\b(?:os|operating system)\s*[:=-]\s*([\w .-]+)", "cpu": r"\b(?:cpu|vcpus?)\s*[:=-]\s*(\d+)",
        "ram": r"\b(?:ram|memory)\s*[:=-]\s*([\w .-]+)", "disk": r"\bdisk\s*[:=-]\s*([\w .-]+)",
        "expiry_date": r"expir(?:y|es|ation)\s*[:=-]\s*([\w ./-]+)", "approver": r"approver\s*[:=-]\s*([\w .@-]+)",
        "repository": r"\b(?:repo|repository)\s*[:=-]\s*([\w ./:-]+)", "branch": r"branch\s*[:=-]\s*([\w ./-]+)",
        "commit_sha": r"(?:commit(?: sha)?\s*[:=-]\s*)?([0-9a-f]{7,40})", "product": r"product\s*[:=-]\s*([\w .-]+)",
        "justification": r"justification\s*[:=-]\s*([^\n]+)", "system": r"\b(?:system|app|application)\s*[:=-]\s*([\w .-]+)",
        "access_level": r"access(?: level)?\s*[:=-]\s*([\w .-]+)", "project_name": r"project name\s*[:=-]\s*([\w .-]+)",
        "owner": r"owner\s*[:=-]\s*([\w .@-]+)", "repo_platform": r"repo platform\s*[:=-]\s*([\w .-]+)",
        "ci_type": r"ci(?: type)?\s*[:=-]\s*([\w .-]+)", "environment_needs": r"environment needs\s*[:=-]\s*([^\n]+)",
        "impact": r"impact\s*[:=-]\s*([^\n]+)", "service": r"service\s*[:=-]\s*([\w .-]+)", "urgency": r"urgency\s*[:=-]\s*(\w+)",
    }
    for k, p in patterns.items():
        m = re.search(p, text, re.I)
        if m:
            fields[k] = m.group(1).strip() if m.lastindex else m.group(0)
    ci_tools = {"jenkins": "Jenkins", "github.com": "GitHub Actions", "gitlab": "GitLab CI", "dev.azure.com": "Azure DevOps"}
    for link in email.links:
        l = link.lower()
        for marker, tool in ci_tools.items():
            if marker in l:
                fields.setdefault("build_url", link)
                fields.setdefault("ci_tool", tool)
                break
    return fields

def classify_email(email: NormalizedEmail) -> ClassificationResult:
    text = f"{email.subject}\n{email.body}".lower()
    fields = _extract(f"{email.subject}\n{email.body}", email)
    if _has(text, ["newsletter", "maintenance window", "all hands", "policy update", "office closed"]): cat, conf, reason = CATEGORIES["org"], .9, "organizational keywords"
    elif _has(text, ["new project", "onboard project", "create repository", "bootstrap", "project onboarding"]): cat, conf, reason = CATEGORIES["project"], .85, "project onboarding keywords"
    elif _has(text, ["build failed", "pipeline failed", "ci failed", "jenkins", "github actions", "gitlab ci", "azure devops"]): cat, conf, reason = CATEGORIES["ci"], .92, "CI failure keywords or links"
    elif _has(text, ["vm", "virtual machine", "server request", "provision"]): cat, conf, reason = CATEGORIES["vm"], .88, "VM provisioning keywords"
    elif _has(text, ["license", "subscription", "seat"]): cat, conf, reason = CATEGORIES["license"], .86, "license keywords"
    elif _has(text, ["access", "permission", "role", "group membership"]): cat, conf, reason = CATEGORIES["access"], .84, "access keywords"
    elif _has(text, ["incident", "outage", "sev", "production down", "urgent support"]): cat, conf, reason = CATEGORIES["incident"], .89, "incident/support keywords"
    elif _has(text, ["devops", "help", "support"]): cat, conf, reason = CATEGORIES["general"], .65, "general support keywords"
    else: cat, conf, reason = CATEGORIES["triage"], .25, "no deterministic rule matched"
    missing = [f for f in REQUIRED_FIELDS.get(cat, []) if not fields.get(f)]
    return ClassificationResult(cat, conf, reason, fields, missing)
