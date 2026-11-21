"""Tests for OpenAPI validation rules."""

import pytest
from openapi_smoke.models import IssueSeverity, OperationSpec
from openapi_smoke.validator import validate_spec


def test_validate_spec_missing_version():
    spec = {"info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}
    issues = validate_spec(spec, [])
    assert any(i.severity == IssueSeverity.ERROR and "version tag" in i.message for i in issues)


def test_validate_spec_undeclared_path_param():
    spec = {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}
    op = OperationSpec(
        path="/items/{item_id}",
        method="GET",
        parameters=[],  # item_id is missing from parameters!
        expected_status_codes=[200],
    )
    issues = validate_spec(spec, [op])
    assert any(i.severity == IssueSeverity.ERROR and "{item_id}" in i.message for i in issues)
