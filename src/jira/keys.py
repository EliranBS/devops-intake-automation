import re
JIRA_KEY_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")

def find_jira_keys(*texts: str | None) -> list[str]:
    found: list[str] = []
    for text in texts:
        if text:
            found.extend(JIRA_KEY_RE.findall(text.upper()))
    return sorted(set(found))
