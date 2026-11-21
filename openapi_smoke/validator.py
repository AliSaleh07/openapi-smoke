"""Validation engine for OpenAPI structural compliance and best practices."""

import re
from typing import List, Dict, Any
from openapi_smoke.models import ValidationIssue, IssueSeverity, OperationSpec

PATH_PARAM_PATTERN = re.compile(r"\{([a-zA-Z0-9_-]+)\}")


def validate_spec(spec: Dict[str, Any], operations: List[OperationSpec]) -> List[ValidationIssue]:
    """Validates an OpenAPI specification for required fields, path parameters, and conventions."""
    issues: List[ValidationIssue] = []

    # 1. Version Check
    version = spec.get("openapi") or spec.get("swagger")
    if not version:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.ERROR,
                path="root",
                message="Specification missing required 'openapi' or 'swagger' version tag.",
            )
        )

    # 2. Info Block
    info = spec.get("info")
    if not isinstance(info, dict):
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.ERROR,
                path="info",
                message="Missing required 'info' metadata object.",
            )
        )
    else:
        if not info.get("title"):
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.ERROR,
                    path="info.title",
                    message="Missing required API title in 'info.title'.",
                )
            )
        if not info.get("version"):
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    path="info.version",
                    message="Missing recommended semantic version in 'info.version'.",
                )
            )

    # 3. Operations & Path Parameters Validation
    if not operations:
        issues.append(
            ValidationIssue(
                severity=IssueSeverity.WARNING,
                path="paths",
                message="No executable operations defined in 'paths'.",
            )
        )

    for op in operations:
        op_label = f"{op.method} {op.path}"

        # Responses check
        if not op.expected_status_codes:
            issues.append(
                ValidationIssue(
                    severity=IssueSeverity.WARNING,
                    path=op_label,
                    message=f"Operation {op_label} does not specify any explicit numeric response status codes.",
                )
            )

        # Path parameter template check
        declared_path_vars = set(PATH_PARAM_PATTERN.findall(op.path))
        if declared_path_vars:
            param_names = {
                p.get("name")
                for p in op.parameters
                if isinstance(p, dict) and p.get("in") == "path"
            }
            for missing_var in declared_path_vars - param_names:
                issues.append(
                    ValidationIssue(
                        severity=IssueSeverity.ERROR,
                        path=op_label,
                        message=f"Path template variable '{{{missing_var}}}' is not declared in 'parameters'.",
                    )
                )

    return issues
