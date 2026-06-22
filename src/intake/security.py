import re

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|pwd|token|secret|api[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"),
]

def redact_secrets(text: str | None) -> str:
    if not text:
        return ""
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda m: m.group(1) + "=[REDACTED]" if m.lastindex else "[REDACTED]", redacted)
    return redacted

def safe_excerpt(text: str, limit: int = 2000) -> str:
    return redact_secrets(text).strip()[:limit]
