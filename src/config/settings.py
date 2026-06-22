from __future__ import annotations
import json, os
from pathlib import Path

DEFAULT_CONFIG = {"jira":{"base_url":"https://jira.example.invalid","project_key":"OPS","issue_type_mapping":{},"priority_mapping":{},"custom_field_mapping":{}},"outlook":{"source_mailbox":"devops-intake@example.invalid"}}

def load_config(path: str | None = None) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if path and Path(path).exists():
        loaded = json.loads(Path(path).read_text())
        for section, values in loaded.items():
            cfg.setdefault(section, {}).update(values if isinstance(values, dict) else {})
    cfg["jira"]["base_url"] = os.getenv("JIRA_BASE_URL", cfg["jira"]["base_url"])
    cfg["jira"]["project_key"] = os.getenv("JIRA_PROJECT_KEY", cfg["jira"]["project_key"])
    cfg["outlook"]["source_mailbox"] = os.getenv("OUTLOOK_SOURCE_MAILBOX", cfg["outlook"]["source_mailbox"])
    return cfg
