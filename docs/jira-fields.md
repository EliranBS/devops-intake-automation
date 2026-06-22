# Jira Fields

Jira issue creation is config-driven.

## Default fields

- `project.key`
- `issuetype.name`
- `summary`
- Atlassian Document Format `description`
- `priority.name`
- labels: `devops-intake` and category label

## Custom fields

Map extracted field names to Jira custom field IDs in `jira.custom_field_mapping`.

Example:

```json
{"project": "customfield_10010", "approver": "customfield_10011"}
```

## Existing issue updates

If a Jira key appears in the subject or body, the intake decision is `update`; callers should add a comment or transition the existing issue rather than creating a new issue.
