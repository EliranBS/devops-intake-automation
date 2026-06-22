from __future__ import annotations

import re
from typing import Any

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(password|passwd|pwd|token|secret|api[_-]?key|client[_-]?secret)\b\s*[:=]\s*(['\"]?)[^\s,'\";]+\2"),
    re.compile(r"(?i)\b(authorization)\b\s*[:=]\s*bearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+"),
]

SENSITIVE_KEYS = {"body", "content", "bodyPreview", "authorization", "token", "password", "secret", "apiKey", "clientSecret"}


def redact_secrets(text: str | None) -> str:
    if not text:
        return ""
    redacted = text
    for pattern in SECRET_PATTERNS:
        def replacement(match: re.Match[str]) -> str:
            key = match.group(1) if match.lastindex else None
            if key and key.lower() != "authorization":
                return f"{key}=[REDACTED]"
            if key and key.lower() == "authorization":
                return "Authorization=[REDACTED]"
            return "Bearer [REDACTED]"
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_mapping(value: Any) -> Any:
    """Return a recursively redacted copy safe for diagnostics."""
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            if key in SENSITIVE_KEYS:
                safe[key] = "[REDACTED]"
            else:
                safe[key] = redact_mapping(item)
        return safe
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    if isinstance(value, str):
        return redact_secrets(value)
    return value


def safe_excerpt(text: str, limit: int = 2000) -> str:
    return redact_secrets(text).strip()[:limit]
