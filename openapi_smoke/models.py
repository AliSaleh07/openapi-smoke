"""Data models for OpenAPI specifications, operations, and smoke test results."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class IssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class TestStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

TestStatus.__test__ = False


@dataclass
class OperationSpec:
    path: str
    method: str
    summary: str = ""
    description: str = ""
    operation_id: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    expected_status_codes: List[int] = field(default_factory=list)


@dataclass
class ValidationIssue:
    severity: IssueSeverity
    path: str
    message: str


@dataclass
class TestResult:
    operation: OperationSpec
    status: TestStatus
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    response_headers: Dict[str, str] = field(default_factory=dict)

TestResult.__test__ = False


@dataclass
class SmokeSuiteReport:
    spec_path: str
    base_url: str
    total_operations: int
    executed_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    results: List[TestResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: str = ""

    @property
    def is_success(self) -> bool:
        return self.failed_tests == 0 and not any(
            i.severity == IssueSeverity.ERROR for i in self.validation_issues
        )
