"""Unit tests for OpenAPI specification parser."""

import os
import pytest
from openapi_smoke.parser import load_spec_file, extract_operations, SpecParseError


def test_load_valid_spec():
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_taskforge_spec.yaml")
    data = load_spec_file(path)
    assert data["openapi"] == "3.1.0"
    assert data["info"]["title"] == "TaskForge API"


def test_extract_operations():
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_taskforge_spec.yaml")
    data = load_spec_file(path)
    ops = extract_operations(data)
    assert len(ops) == 3

    paths = {op.path for op in ops}
    assert "/healthz" in paths
    assert "/api/v1/auth/me" in paths
    assert "/api/v1/tasks/{task_id}" in paths


def test_missing_spec_raises_error():
    with pytest.raises(SpecParseError, match="not found"):
        load_spec_file("non_existent_spec_file.yaml")
