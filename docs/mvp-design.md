# MVP Design

The MVP follows the architecture document by keeping Outlook as the intake channel, Jira as the system of record, and side-effecting execution out of scope.

## Flow

1. `outlook.normalizer` converts Microsoft Graph-like mail payloads into `NormalizedEmail`.
2. `classifier.rules` applies deterministic rules and extracts fields.
3. `jira.keys` detects existing Jira keys; matching messages should update instead of create.
4. `correlation.strategy` detects duplicates using mailbox/message IDs and request fingerprints.
5. `jira.payloads` builds Jira create payloads from configuration.
6. `responders.templates` generates requester replies.
7. `ci.enrichment` defines CI enrichment interfaces and safe stubs.

## Production hardening needed later

- Durable correlation store with uniqueness constraints and processing locks.
- Retry-aware Microsoft Graph and Jira adapters.
- Observability integration with Application Insights or equivalent.
- Approval workflow integration before any infrastructure execution.
