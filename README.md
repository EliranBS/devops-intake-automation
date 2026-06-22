# DevOps Intake Automation

MVP backend logic for converting Outlook/Microsoft Graph email payloads into structured Jira intake decisions. The code is intentionally side-effect free: it normalizes mail, classifies requests, detects Jira keys and duplicates, generates Jira payloads, renders auto-replies, and exposes CI enrichment stubs.

## What is included

- Outlook payload normalization with attachment metadata, recipients, message IDs, conversation IDs, and URL extraction.
- Deterministic rules for CI failures, VM requests, access requests, license requests, new-project requests, incidents, organizational mail, general support, and manual triage.
- Jira key detection using `\b[A-Z][A-Z0-9]+-\d+\b`.
- Duplicate correlation by mailbox/message ID and normalized fingerprints.
- Config-driven Jira issue payload generation.
- Required-field and missing-information logic.
- Auto-reply templates for common lifecycle events.
- Jenkins, GitHub Actions, GitLab CI, and Azure DevOps enrichment extension points.
- Structured logging helpers with secret redaction.

## Quick start

```bash
python -m pytest
./scripts/run-local-demo.sh
```

## Configuration

Copy `config.example.json` and override with environment variables where needed:

- `JIRA_BASE_URL`
- `JIRA_PROJECT_KEY`
- `OUTLOOK_SOURCE_MAILBOX`

Do not store API tokens, mailbox credentials, or CI credentials in source. Future API adapters should load secrets from the deployment platform or a secret manager.

## Limitations and assumptions

- This MVP does not call Microsoft Graph, Jira, or CI APIs directly.
- Correlation uses an in-memory store for tests/demo; production should use durable storage with locks.
- Classification is deterministic and rules-based; low-confidence messages route to manual triage.
- VM provisioning, Terraform execution, and destructive actions are intentionally out of scope.
