from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class CIEnrichmentRequest:
    ci_tool: str
    build_url: str
    repository: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    jira_issue_key: str | None = None
    intake_request_id: str | None = None

@dataclass(frozen=True)
class CIEnrichmentResult:
    status: str
    failing_stage: str | None = None
    failure_signature: str | None = None
    log_excerpt: list[str] | None = None
    external_run_id: str | None = None

class CIEnricher(Protocol):
    def enrich(self, request: CIEnrichmentRequest) -> CIEnrichmentResult: ...

class StubCIEnricher:
    def enrich(self, request: CIEnrichmentRequest) -> CIEnrichmentResult:
        return CIEnrichmentResult(status="not_implemented", failure_signature=f"{request.ci_tool} enrichment stub")

JenkinsEnricher = GitHubActionsEnricher = GitLabCIEnricher = AzureDevOpsEnricher = StubCIEnricher
