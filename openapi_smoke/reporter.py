"""Reporting tools for OpenAPI Smoke: terminal, JSON, and JUnit XML outputs."""

import json
from openapi_smoke.models import SmokeSuiteReport, TestStatus, IssueSeverity

COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_GRAY = "\033[90m"
COLOR_BOLD = "\033[1m"
COLOR_RESET = "\033[0m"


def format_terminal(report: SmokeSuiteReport, use_color: bool = True) -> str:
    lines = []
    c_bold = COLOR_BOLD if use_color else ""
    c_reset = COLOR_RESET if use_color else ""
    c_red = COLOR_RED if use_color else ""
    c_green = COLOR_GREEN if use_color else ""
    c_yellow = COLOR_YELLOW if use_color else ""
    c_gray = COLOR_GRAY if use_color else ""

    lines.append(f"{c_bold}OpenAPI Smoke Test Suite Results{c_reset}")
    lines.append(f"{c_gray}Spec File:{c_reset}     {report.spec_path}")
    lines.append(f"{c_gray}Target Base:{c_reset}  {report.base_url}")
    lines.append(f"{c_gray}Duration:{c_reset}     {report.duration_seconds:.2f}s ({report.timestamp})\n")

    if report.validation_issues:
        lines.append(f"{c_bold}Spec Validation Issues ({len(report.validation_issues)}):{c_reset}")
        for issue in report.validation_issues:
            col = c_red if issue.severity == IssueSeverity.ERROR else c_yellow
            lines.append(f"  [{col}{issue.severity.value}{c_reset}] {issue.path}: {issue.message}")
        lines.append("")

    lines.append(f"{c_bold}Endpoint Execution Results:{c_reset}")
    lines.append("-" * 75)
    for res in report.results:
        op = res.operation
        op_label = f"{op.method:<6} {op.path}"
        if res.status == TestStatus.PASSED:
            code_str = f"({res.status_code})" if res.status_code else "(dry-run)"
            lines.append(f"  [{c_green}PASS{c_reset}] {op_label:<35} {code_str:<8} {res.latency_ms:>6.1f}ms")
        elif res.status == TestStatus.SKIPPED:
            lines.append(f"  [{c_yellow}SKIP{c_reset}] {op_label:<35} {res.error_message}")
        else:
            lines.append(f"  [{c_red}FAIL{c_reset}] {op_label:<35} Status: {res.status_code} - {res.error_message}")

    lines.append("-" * 75)
    lines.append(
        f"{c_bold}Summary:{c_reset} Total: {report.executed_tests} | "
        f"{c_green}Passed: {report.passed_tests}{c_reset} | "
        f"{c_red}Failed: {report.failed_tests}{c_reset} | "
        f"{c_yellow}Skipped: {report.skipped_tests}{c_reset}"
    )
    lines.append("")
    return "\n".join(lines)


def format_json(report: SmokeSuiteReport) -> str:
    data = {
        "spec_path": report.spec_path,
        "base_url": report.base_url,
        "timestamp": report.timestamp,
        "duration_seconds": report.duration_seconds,
        "is_success": report.is_success,
        "summary": {
            "total_operations": report.total_operations,
            "executed": report.executed_tests,
            "passed": report.passed_tests,
            "failed": report.failed_tests,
            "skipped": report.skipped_tests,
        },
        "validation_issues": [
            {"severity": i.severity.value, "path": i.path, "message": i.message}
            for i in report.validation_issues
        ],
        "results": [
            {
                "method": r.operation.method,
                "path": r.operation.path,
                "status": r.status.value,
                "status_code": r.status_code,
                "latency_ms": r.latency_ms,
                "error": r.error_message,
            }
            for r in report.results
        ],
    }
    return json.dumps(data, indent=2)


def format_junit_xml(report: SmokeSuiteReport) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<testsuite name="OpenAPISmoke" tests="{report.executed_tests}" failures="{report.failed_tests}" skipped="{report.skipped_tests}" time="{report.duration_seconds}">',
    ]
    for r in report.results:
        classname = f"OpenAPI.{r.operation.method}"
        name = r.operation.path
        time_sec = r.latency_ms / 1000.0
        lines.append(f'  <testcase classname="{classname}" name="{name}" time="{time_sec:.3f}">')
        if r.status == TestStatus.FAILED:
            lines.append(f'    <failure message="{r.error_message}">{r.error_message}</failure>')
        elif r.status == TestStatus.SKIPPED:
            lines.append(f'    <skipped message="{r.error_message}"/>')
        lines.append("  </testcase>")
    lines.append("</testsuite>")
    return "\n".join(lines)
