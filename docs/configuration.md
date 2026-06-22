# Configuration

Configuration is loaded from JSON plus environment variables. The example file is `config.example.json`. Windows PowerShell is the default shell for local setup and examples.

## Recommended Windows setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Required runtime values

```powershell
$env:JIRA_BASE_URL = "https://your-domain.atlassian.net"
$env:JIRA_PROJECT_KEY = "OPS"
$env:OUTLOOK_SOURCE_MAILBOX = "devops-intake@example.com"
```

## Secrets

Do not put tokens in JSON files. Use managed identity, Key Vault, CI secret stores, or platform environment secrets. Never log tokens or full sensitive email bodies.
