# AGENTS.md

## Project Context

This repository implements a DevOps Intake Automation Platform.

The system is based on the architecture document:

docs/automated-devops-intake-from-outlook-to-jira.md

Before implementing or changing anything, read the architecture document fully and treat it as the main product specification.

## Main Goal

Build a production-ready DevOps intake system that receives Outlook emails, classifies them, creates or updates Jira issues, manages approvals, enriches CI failures, and triggers controlled infrastructure workflows.

## Expected Engineering Standards

- Prefer small, maintainable services over one large script.
- Keep integrations modular.
- Do not hardcode credentials, URLs, tokens, mailbox names, Jira project keys, or CI endpoints.
- Use environment variables or configuration files for all external settings.
- Add clear README documentation for every component.
- Add tests for all parsing, classification, deduplication, and Jira payload logic.
- Add structured logging and correlation IDs.
- Handle retries, rate limits, idempotency, and duplicate messages.
- Assume production use, not a demo-only script.

## Security Requirements

- Never store secrets in source code.
- Do not log access tokens, API tokens, email bodies containing secrets, or sensitive user data.
- Use least privilege for Microsoft Graph, Jira, CI, and infrastructure integrations.
- Sanitize email content before sending it to Jira comments or logs.
- Add clear notes where admin permissions are required.

## Implementation Priority

Start with an MVP:

1. Outlook email payload normalization.
2. Email classification.
3. Duplicate detection and correlation.
4. Jira issue payload generation.
5. Missing-information detection.
6. Auto-reply template generation.
7. CI failure enrichment interface.
8. Basic tests.
9. Documentation.

Do not start with VM provisioning or Terraform execution before the intake and Jira layers are stable.

## Required Output Style

When completing a task:

- Summarize what was changed.
- List files changed.
- Explain how to test.
- Mention limitations or assumptions.
- Do not claim production readiness unless tests, configuration, error handling, and documentation exist.