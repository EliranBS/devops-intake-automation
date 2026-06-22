# DevOps Intake Automation

MVP backend logic for converting Outlook/Microsoft Graph email payloads into structured Jira intake decisions. The default supported local development and operation environment is **Windows with Windows PowerShell**. The Python modules use cross-platform standard library code, but project instructions and scripts are Windows-first.

## What is included

- Outlook payload normalization with attachment metadata, recipients, message IDs, conversation IDs, and URL extraction.
- Deterministic rules for CI failures, VM requests, access requests, license requests, new-project requests, incidents, organizational mail, general support, and manual triage.
- Jira key detection using `\b[A-Z][A-Z0-9]+-\d+\b`.
- Duplicate correlation by mailbox/message ID, conversation ID, and normalized fingerprints.
- Config-driven Jira issue payload generation.
- Required-field and missing-information logic.
- Auto-reply templates for common lifecycle events.
- Jenkins, GitHub Actions, GitLab CI, and Azure DevOps enrichment extension points.
- Structured logging helpers plus secret redaction for common password/token/header patterns.

## Windows quick start

Run these commands from Windows PowerShell at the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
python -m src.intake.pipeline
.\scripts\validate.ps1
.\scripts\run-local-demo.ps1
```

If your PowerShell execution policy blocks local scripts, run this for the current process only and retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Optional non-Windows helpers

Bash scripts are retained only as optional convenience wrappers for non-Windows environments. They are not required for normal development or operation. Use the `.ps1` scripts above for the supported workflow.

## Configuration

Copy `config.example.json` and override with environment variables where needed:

```powershell
$env:JIRA_BASE_URL = "https://your-domain.atlassian.net"
$env:JIRA_PROJECT_KEY = "OPS"
$env:OUTLOOK_SOURCE_MAILBOX = "devops-intake@example.com"
```

Do not store API tokens, mailbox credentials, or CI credentials in source. Future API adapters should load secrets from the deployment platform or a secret manager.

## Limitations and assumptions

- This MVP does not call Microsoft Graph, Jira, Jenkins, Terraform, or other external APIs directly.
- Correlation uses an in-memory store for tests/demo; production should use durable storage with locks.
- Classification is deterministic and rules-based; low-confidence messages route to manual triage.
- VM provisioning, Terraform execution, and destructive actions are intentionally out of scope.
