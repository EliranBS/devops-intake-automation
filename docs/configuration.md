# Configuration

Configuration is loaded from JSON plus environment variables. The example file is `config.example.json`.

## Required runtime values

- Jira base URL: `JIRA_BASE_URL`
- Jira project key: `JIRA_PROJECT_KEY`
- Outlook source mailbox: `OUTLOOK_SOURCE_MAILBOX`

## Secrets

Do not put tokens in JSON files. Use managed identity, Key Vault, CI secret stores, or platform environment secrets. Never log tokens or full sensitive email bodies.
