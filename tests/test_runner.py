"""Tests for smoke test execution and dry-run mode."""

import os
import pytest
from openapi_smoke.parser import load_spec_file, extract_operations
from openapi_smoke.runner import run_smoke_tests
from openapi_smoke.models import TestStatus


def test_dry_run_execution():
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_taskforge_spec.yaml")
    spec_data = load_spec_file(path)
    ops = extract_operations(spec_data)

    report = run_smoke_tests(
        operations=ops,
        base_url="http://localhost:8000",
        spec_path=path,
        validation_issues=[],
        dry_run=True,
    )
    assert report.executed_tests == 3
    assert report.passed_tests == 3
    assert report.failed_tests == 0
    assert report.is_success is True


def test_tag_filter():
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_taskforge_spec.yaml")
    spec_data = load_spec_file(path)
    ops = extract_operations(spec_data)

    report = run_smoke_tests(
        operations=ops,
        base_url="http://localhost:8000",
        spec_path=path,
        validation_issues=[],
        dry_run=True,
        tag_filter="System",
    )
    assert report.executed_tests == 1
    assert report.results[0].operation.path == "/healthz"
