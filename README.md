# DevOps Intake Automation

MVP backend logic for converting Outlook/Microsoft Graph email payloads into structured Jira intake decisions. The default supported local development and operation environment is **Windows with Windows PowerShell**. The Python modules use cross-platform standard library code, but project instructions and scripts are Windows-first.

## What is included

- Outlook payload normalization with attachment metadata, recipients, message IDs, conversation IDs, and URL extraction.
- Deterministic rules for CI failures, VM requests, access requests, license requests, new-project requests, incidents, organizational mail, general support, and manual triage.
- Jira key detection using `\b[A-Z][A-Z0-9]+-\d+\b`.
- Duplicate correlation by mailbox/message ID, conversation ID, and normalized fingerprints, backed by local SQLite durability by default.
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

## Windows CI

GitHub Actions validation is Windows-only and runs on `windows-latest`. The workflow installs development dependencies, runs the Python test suite, executes the fixture pipeline, and then runs the supported PowerShell validation and local demo scripts. No Linux or Bash workflow is required for supported development.

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

### SQLite correlation store

The default local correlation store is SQLite. It allows duplicate detection to survive process restarts during Windows-first local development. By default, the database is created at `.data\correlation.sqlite3` when commands are run from the repository root. Override the path with `INTAKE_CORRELATION_DB_PATH`:

```powershell
$env:INTAKE_CORRELATION_DB_PATH = "C:\\dev\\devops-intake\\correlation.sqlite3"
python -m src.intake.pipeline
```

To reset local duplicate-tracking state, remove the database and SQLite sidecar files:

```powershell
Remove-Item .\.data\correlation.sqlite3* -ErrorAction SilentlyContinue
```

See `docs/durable-correlation-store.md` for the stored fields, locking behavior, and limitations.

## Limitations and assumptions

- This MVP does not call Microsoft Graph, Jira, Jenkins, Terraform, or other external APIs directly.
- Correlation uses a SQLite store for the local pipeline demo. The in-memory store remains only for focused tests. The SQLite store is suitable for the single-process MVP workflow, not a hosted multi-worker production deployment.
- Classification is deterministic and rules-based; low-confidence messages route to manual triage.
- VM provisioning, Terraform execution, and destructive actions are intentionally out of scope.
