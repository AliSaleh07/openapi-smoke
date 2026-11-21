"""Safe OpenAPI YAML/JSON parser with protection against unsafe YAML deserialization."""

import json
import os
from typing import Dict, Any, List, Tuple
import yaml

from openapi_smoke.models import OperationSpec


class SpecParseError(Exception):
    """Raised when an OpenAPI document is invalid or unreadable."""
    pass


def load_spec_file(file_path: str) -> Dict[str, Any]:
    """Safely loads and deserializes an OpenAPI specification from YAML or JSON."""
    if not os.path.exists(file_path):
        raise SpecParseError(f"Spec file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as exc:
        raise SpecParseError(f"Failed to read spec file {file_path}: {exc}")

    # Use yaml.safe_load strictly (never FullLoader or unsafe loaders)
    try:
        if file_path.endswith(".json"):
            data = json.loads(content)
        else:
            data = yaml.safe_load(content)
    except Exception as exc:
        raise SpecParseError(f"Failed to parse OpenAPI syntax in {file_path}: {exc}")

    if not isinstance(data, dict):
        raise SpecParseError("OpenAPI spec root must be a valid mapping / dictionary")

    return data


def extract_operations(spec: Dict[str, Any]) -> List[OperationSpec]:
    """Extracts all callable HTTP operations from the parsed OpenAPI specification."""
    operations: List[OperationSpec] = []
    paths = spec.get("paths", {})

    if not isinstance(paths, dict):
        return operations

    http_methods = {"get", "post", "put", "delete", "patch", "head", "options"}

    for path_str, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        common_params = path_item.get("parameters", [])

        for method, op_data in path_item.items():
            if method.lower() not in http_methods or not isinstance(op_data, dict):
                continue

            op_params = op_data.get("parameters", [])
            merged_params = (
                common_params + op_params
                if isinstance(common_params, list) and isinstance(op_params, list)
                else []
            )

            # Extract expected status codes from responses
            responses = op_data.get("responses", {})
            status_codes = []
            if isinstance(responses, dict):
                for code_key in responses.keys():
                    if str(code_key).isdigit():
                        status_codes.append(int(code_key))

            operations.append(
                OperationSpec(
                    path=path_str,
                    method=method.upper(),
                    summary=op_data.get("summary", ""),
                    description=op_data.get("description", ""),
                    operation_id=op_data.get("operationId", ""),
                    tags=op_data.get("tags", []),
                    parameters=merged_params,
                    expected_status_codes=sorted(status_codes),
                )
            )

    return operations
