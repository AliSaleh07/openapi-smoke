"""Integration tests for OpenAPI Smoke CLI."""

import os
import json
from openapi_smoke.cli import main


def test_cli_validate_success():
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_taskforge_spec.yaml")
    code = main(["validate", path])
    assert code == 0


def test_cli_test_dry_run_success():
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_petstore.yaml")
    code = main(["test", path, "--dry-run", "--strict"])
    assert code == 0


def test_cli_junit_xml_format(capsys):
    path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_petstore.yaml")
    code = main(["test", path, "--dry-run", "--format", "junit"])
    assert code == 0
    captured = capsys.readouterr()
    assert '<?xml version="1.0" encoding="UTF-8"?>' in captured.out
    assert '<testsuite' in captured.out
