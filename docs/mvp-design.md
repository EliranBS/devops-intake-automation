# MVP Design

The MVP follows the architecture document by keeping Outlook as the intake channel, Jira as the system of record, and side-effecting execution out of scope. The supported local workflow is Windows PowerShell.

## Flow

1. `outlook.normalizer` converts Microsoft Graph-like mail payloads into `NormalizedEmail`.
2. `classifier.rules` applies deterministic rules and extracts fields.
3. `jira.keys` detects existing Jira keys; matching messages should update instead of create.
4. `correlation.strategy` detects duplicates using mailbox/message IDs, conversation IDs, and normalized request fingerprints that remove reply/forward prefixes and embedded Jira keys.
5. `jira.payloads` builds Jira create payloads from configuration.
6. `responders.templates` generates requester replies.
7. `ci.enrichment` defines CI enrichment interfaces and safe stubs.

## Windows operation

Run the local checks from Windows PowerShell:

```powershell
python -m pytest
python -m src.intake.pipeline
.\scripts\validate.ps1
.\scripts\run-local-demo.ps1
```

The demo and tests use Python `pathlib` to resolve repository paths and do not require WSL, Git Bash, Linux paths, `chmod`, cron, systemd, apt, or yum.

## Security hardening notes

- Normalization redacts body content in diagnostic `raw` payload copies so tests and logs do not retain obvious tokens/passwords.
- Requester auto-replies explicitly tell users not to include passwords, tokens, or private keys.
- Redaction is a defense-in-depth helper, not a replacement for DLP and least-privilege mailbox/Jira access controls.

## Production hardening needed later

- Durable correlation store with uniqueness constraints and processing locks.
- Retry-aware Microsoft Graph and Jira adapters.
- Observability integration with Application Insights or equivalent.
- Approval workflow integration before any infrastructure execution.
