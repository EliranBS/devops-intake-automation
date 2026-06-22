# Durable correlation store

Phase 2A replaces the demo-only in-memory correlation store with a local SQLite-backed store for Windows-first development.

## What is stored

Each correlation record stores enough metadata to avoid creating duplicate Jira issues across process restarts:

- mailbox
- message id, preferring `internetMessageId`, then immutable message id, then provider message id
- internet message id
- conversation id
- normalized fingerprint
- detected Jira key, when a message already references a Jira issue
- category
- requester
- created timestamp
- last seen timestamp

The SQLite implementation is local-only and does not call Microsoft Graph, Jira, Jenkins, Terraform, Ansible, or VM tooling.

## Configure the database path

The default path is `.data\correlation.sqlite3` relative to the repository root when commands are run from the root.

Override it from Windows PowerShell with:

```powershell
$env:INTAKE_CORRELATION_DB_PATH = "C:\\dev\\devops-intake\\correlation.sqlite3"
python -m src.intake.pipeline
```

Use a path outside the repository if you want the database to survive clean checkouts. Do not store secrets in the database path or in source-controlled configuration.

## Reset local correlation state

To force the local demo to treat fixture messages as new requests again, delete the SQLite files:

```powershell
Remove-Item .\.data\correlation.sqlite3* -ErrorAction SilentlyContinue
```

SQLite may create `-wal` and `-shm` sidecar files when write-ahead logging is enabled, so the wildcard is intentional.

## Locking and local safety

The store uses SQLite transactions with `BEGIN IMMEDIATE`, a busy timeout, and write-ahead logging. This is suitable for the current single-process local MVP workflow. It is not a multi-worker service design and should be revisited before hosted production use.

## Test-only in-memory store

`InMemoryCorrelationStore` remains available for fast unit tests and focused pure-Python checks. Runtime pipeline demos use `SQLiteCorrelationStore` by default.
