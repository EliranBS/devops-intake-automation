# Codex Task: Build DevOps Intake Automation Platform

You are working on a new repository named:

devops-intake-automation

The complete product architecture is documented here:

docs/automated-devops-intake-from-outlook-to-jira.md

Read the full document before implementing anything.

## Objective

Create the first production-grade MVP of the DevOps Intake Automation Platform.

The platform should support an organization where:

- Outlook is the main intake channel.
- Jira is the system of record.
- There is a lot of CI and almost no CD.
- DevOps receives many emails from developers.
- Emails may belong to projects, personal requests, license requests, incidents, VM requests, CI failures, organizational emails, or new project requests.
- The goal is to reduce manual triage and convert emails into structured Jira work.

## MVP Scope

Implement the core backend logic first.

Do not build a full UI yet.

Do not implement real destructive infrastructure actions yet.

Focus on:

1. Normalize Outlook email payloads.
2. Classify emails into DevOps request categories.
3. Detect existing Jira keys in subject/body.
4. Detect duplicates using message IDs and normalized fingerprints.
5. Generate Jira issue payloads.
6. Detect missing required fields by request type.
7. Generate automatic reply templates.
8. Provide extension points for CI enrichment.
9. Add strong tests.
10. Document setup and usage.

## Required Categories

Support these categories:

- CI Failure
- VM Request
- Access Request
- License Request
- New Project Request
- Incident / Support
- Organizational Mail
- General DevOps Support
- Needs Manual Triage

## Required Repository Structure

Create a clean structure similar to:

src/
  intake/
  classifier/
  jira/
  outlook/
  correlation/
  responders/
  ci/
  config/
  logging/

tests/
  unit/
  fixtures/

docs/
  mvp-design.md
  configuration.md
  jira-fields.md
  outlook-integration.md

scripts/
  run-local-demo.*
  validate.*

## Functional Requirements

### Email normalization

Create a normalized internal object from an Outlook/Microsoft Graph-like email payload.

It should include:

- source mailbox
- sender email
- sender display name
- recipients
- subject
- body preview
- full body if available
- message id
- immutable message id if available
- internet message id
- conversation id
- received datetime
- attachment metadata
- links found in subject/body

### Classification

Implement deterministic classification first.

Use rules based on:

- subject prefixes
- sender
- keywords
- detected URLs
- CI build links
- Jira keys
- VM-related words
- license-related words
- access-related words
- project onboarding words
- incident/support words

Return:

- category
- confidence
- reason
- extracted fields
- missing fields

### Jira correlation

If a Jira key exists in subject or body, update the existing issue instead of creating a new one.

Detect Jira keys using a regex like:

\b[A-Z][A-Z0-9]+-\d+\b

### Duplicate detection

Create a correlation strategy using:

- mailbox + internetMessageId
- conversationId
- normalized fingerprint
- category
- project
- requester
- build URL if CI-related

Do not create duplicate Jira issues for the same request.

### Jira payload generation

Generate Jira issue payloads for each category.

Support configurable:

- Jira base URL
- project key
- issue type mapping
- priority mapping
- custom field mapping

Do not hardcode company-specific values.

### Missing information logic

For each category, define required fields.

Examples:

VM Request:
- project
- environment
- OS
- CPU
- RAM
- disk
- expiry date
- approver

CI Failure:
- repository
- branch
- build URL
- CI tool
- commit SHA if available

License Request:
- product
- requester
- justification
- project
- approver or cost owner

New Project Request:
- project name
- owner
- repo platform
- CI type
- environment needs
- approver

If required fields are missing, generate a Waiting for Info response.

### Auto-reply templates

Generate clear email templates for:

- new ticket created
- missing information
- duplicate request detected
- request rejected
- approval required
- automation failed
- ticket completed

### CI enrichment extension

Create interfaces or stubs for:

- Jenkins
- GitHub Actions
- GitLab CI
- Azure DevOps

Do not fully implement every API yet unless the structure is ready.

### Observability

Add structured logging with:

- intakeRequestId
- jiraIssueKey if available
- category
- classifierVersion
- action
- status
- error code
- duration

### Security

- Never log secrets.
- Redact tokens/passwords from email bodies.
- Add helper functions for redaction.
- Document required permissions but do not include real secrets.

## Non-Functional Requirements

- Clean modular code.
- Unit tests for classification, parsing, Jira key detection, missing fields, duplicate fingerprints, and reply templates.
- Config-driven design.
- Clear error handling.
- Retry-aware API client design.
- No destructive side effects in MVP.
- All external calls should be abstracted behind interfaces so they can be mocked.

## Deliverables

Create:

1. Source code for the MVP.
2. Test fixtures with sample Outlook emails.
3. Unit tests.
4. README.md explaining the project.
5. docs/mvp-design.md
6. docs/configuration.md
7. docs/jira-fields.md
8. docs/outlook-integration.md
9. Example configuration file.
10. Local demo script.

## Acceptance Criteria

The MVP is considered complete when:

- Sample CI failure email is classified correctly.
- Sample VM request email is classified correctly.
- Sample license request email is classified correctly.
- Sample access request email is classified correctly.
- Sample new project request email is classified correctly.
- Organizational mail is not incorrectly opened as a high-priority DevOps task.
- Existing Jira key in email causes update flow instead of create flow.
- Duplicate email is detected.
- Missing required fields produce a clear response template.
- Jira payloads are generated without hardcoded secrets.
- All unit tests pass.
- Documentation explains how to connect the logic later to Outlook, Power Automate, Jira REST API, and CI systems.

## Important

Before writing code, produce a short implementation plan.

Then implement the MVP in small commits.

After implementation, run tests and summarize:

- What was implemented
- What was not implemented yet
- How to run locally
- How to test
- Recommended next phase