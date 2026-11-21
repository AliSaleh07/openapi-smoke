"""Execution runner for live HTTP and dry-run OpenAPI smoke tests."""

import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
import httpx

from openapi_smoke.models import (
    OperationSpec,
    SmokeSuiteReport,
    TestResult,
    TestStatus,
    ValidationIssue,
)


def run_smoke_tests(
    operations: List[OperationSpec],
    base_url: str,
    spec_path: str,
    validation_issues: List[ValidationIssue],
    dry_run: bool = False,
    headers: Optional[Dict[str, str]] = None,
    timeout_seconds: float = 10.0,
    method_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
) -> SmokeSuiteReport:
    """Executes smoke tests across the defined operations against the target base URL."""
    start_time = time.time()
    results: List[TestResult] = []
    custom_headers = headers or {}

    filtered_ops = operations
    if method_filter:
        filtered_ops = [op for op in filtered_ops if op.method == method_filter.upper()]
    if tag_filter:
        filtered_ops = [op for op in filtered_ops if tag_filter in op.tags]

    passed = 0
    failed = 0
    skipped = 0

    if dry_run:
        for op in filtered_ops:
            results.append(
                TestResult(
                    operation=op,
                    status=TestStatus.PASSED,
                    status_code=None,
                    latency_ms=0.0,
                    error_message="Dry-run validation successful (no HTTP request sent).",
                )
            )
            passed += 1
    else:
        with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout_seconds) as client:
            for op in filtered_ops:
                # If path contains unresolved variables and no dummy substituted, skip
                if "{" in op.path:
                    results.append(
                        TestResult(
                            operation=op,
                            status=TestStatus.SKIPPED,
                            error_message="Requires dynamic path parameters; skipped during generic smoke run.",
                        )
                    )
                    skipped += 1
                    continue

                url = op.path
                t0 = time.time()
                try:
                    resp = client.request(
                        method=op.method,
                        url=url,
                        headers=custom_headers,
                    )
                    latency = round((time.time() - t0) * 1000, 2)
                    status_code = resp.status_code

                    # If spec specified expected status codes, check adherence
                    is_expected = (
                        status_code in op.expected_status_codes
                        if op.expected_status_codes
                        else (200 <= status_code < 400)
                    )

                    if is_expected:
                        results.append(
                            TestResult(
                                operation=op,
                                status=TestStatus.PASSED,
                                status_code=status_code,
                                latency_ms=latency,
                                response_headers=dict(resp.headers),
                            )
                        )
                        passed += 1
                    else:
                        results.append(
                            TestResult(
                                operation=op,
                                status=TestStatus.FAILED,
                                status_code=status_code,
                                latency_ms=latency,
                                error_message=f"Received unexpected status {status_code}. Expected one of: {op.expected_status_codes}",
                                response_headers=dict(resp.headers),
                            )
                        )
                        failed += 1
                except Exception as exc:
                    latency = round((time.time() - t0) * 1000, 2)
                    results.append(
                        TestResult(
                            operation=op,
                            status=TestStatus.FAILED,
                            status_code=None,
                            latency_ms=latency,
                            error_message=f"Network/Request error: {str(exc)}",
                        )
                    )
                    failed += 1

    total_duration = round(time.time() - start_time, 3)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return SmokeSuiteReport(
        spec_path=spec_path,
        base_url=base_url,
        total_operations=len(operations),
        executed_tests=len(results),
        passed_tests=passed,
        failed_tests=failed,
        skipped_tests=skipped,
        validation_issues=validation_issues,
        results=results,
        duration_seconds=total_duration,
        timestamp=now_str,
    )
