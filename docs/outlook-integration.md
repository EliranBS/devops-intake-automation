# Outlook Integration

The MVP expects Microsoft Graph-like message JSON. Power Automate or an Azure Function can pass message metadata into `normalize_outlook_message`. The default operating environment for local tooling is Windows PowerShell.

## Recommended fields

- `id`, preferably with immutable ID behavior where possible
- `internetMessageId`
- `conversationId`
- `receivedDateTime`
- `from`, `toRecipients`, `ccRecipients`
- `subject`, `bodyPreview`, `body.content`
- attachment metadata only; avoid storing full attachment contents in intake logs

## Local validation from Windows PowerShell

```powershell
python -m src.intake.pipeline
.\scripts\run-local-demo.ps1
```

## Permissions notes

Use least privilege for mailbox read/send operations and scope app access to the shared intake mailbox. Admin consent and mailbox scoping are deployment responsibilities; do not embed credentials in code.
