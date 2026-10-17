from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ScanStatus = Literal["VALIDATING", "ANALYZING", "GENERATING_REPORT", "COMPLETED", "REJECTED"]
FindingStatus = Literal["Pass", "Issue", "Needs Human Review", "Could Not Evaluate"]
AnalysisMethod = Literal["Deterministic", "AI", "Human Review"]


@dataclass
class Finding:
    finding_id: str
    input_location: str
    issue_description: str
    WCAG_criterion: str
    analysis_method: AnalysisMethod
    status: FindingStatus
    remediation_guidance: str | None = None
    additional_details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanSummary:
    checks: int = 0
    passed: int = 0
    issues: int = 0
    human_review: int = 0
    could_not_evaluate: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanResult:
    scan_id: str
    file_or_url: str
    pages: int
    summary: ScanSummary
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    # Backward compatibility with existing scripts/tests expecting dictionary access
    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


@dataclass
class TestCaseResult:
    name: str
    passed: bool
    details: str
    requirement_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TestSuiteSummary:
    total: int
    passed: int
    failed: int
    results: list[TestCaseResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
