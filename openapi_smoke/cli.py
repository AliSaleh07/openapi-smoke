"""Command-line interface entrypoint for OpenAPI Smoke."""

import argparse
import sys
import os

from openapi_smoke.parser import load_spec_file, extract_operations, SpecParseError
from openapi_smoke.validator import validate_spec
from openapi_smoke.runner import run_smoke_tests
from openapi_smoke.reporter import format_terminal, format_json, format_junit_xml


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openapi-smoke",
        description="OpenAPI Smoke: Automated validation and smoke testing CLI for OpenAPI specifications.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate Subcommand
    val_cmd = subparsers.add_parser("validate", help="Validate an OpenAPI specification structure")
    val_cmd.add_argument("spec", help="Path to OpenAPI spec file (YAML or JSON)")
    val_cmd.add_argument("--format", choices=["text", "json"], default="text")

    # Test Subcommand
    test_cmd = subparsers.add_parser("test", help="Execute smoke tests against specified endpoints")
    test_cmd.add_argument("spec", help="Path to OpenAPI spec file (YAML or JSON)")
    test_cmd.add_argument("--base-url", default="http://localhost:8000", help="Target API server base URL")
    test_cmd.add_argument("--dry-run", action="store_true", help="Validate paths without sending network traffic")
    test_cmd.add_argument("--header", action="append", help="HTTP headers in 'Key: Value' format")
    test_cmd.add_argument("--method", help="Filter operations by HTTP method (GET, POST, etc.)")
    test_cmd.add_argument("--tag", help="Filter operations by tag")
    test_cmd.add_argument("--format", choices=["text", "json", "junit"], default="text")
    test_cmd.add_argument("--output", "-o", help="Write report to output file")
    test_cmd.add_argument("--strict", action="store_true", help="Exit code 1 on any failure")
    test_cmd.add_argument("--no-color", action="store_true", help="Disable colored output")

    return parser


def parse_header_list(header_list) -> dict:
    headers = {}
    if header_list:
        for item in header_list:
            if ":" in item:
                k, v = item.split(":", 1)
                headers[k.strip()] = v.strip()
    return headers


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command in ("validate", "test"):
        try:
            spec_data = load_spec_file(args.spec)
            operations = extract_operations(spec_data)
            validation_issues = validate_spec(spec_data, operations)
        except SpecParseError as err:
            sys.stderr.write(f"Spec Parse Error: {err}\n")
            return 2

        if args.command == "validate":
            errors = [i for i in validation_issues if i.severity.value == "ERROR"]
            if args.format == "json":
                out = [
                    {"severity": i.severity.value, "path": i.path, "message": i.message}
                    for i in validation_issues
                ]
                import json
                print(json.dumps({"valid": len(errors) == 0, "issues": out}, indent=2))
            else:
                if not validation_issues:
                    print("✅ Specification structure is valid with 0 issues.")
                else:
                    for i in validation_issues:
                        print(f"[{i.severity.value}] {i.path}: {i.message}")
            return 1 if errors else 0

        elif args.command == "test":
            custom_headers = parse_header_list(args.header)
            report = run_smoke_tests(
                operations=operations,
                base_url=args.base_url,
                spec_path=os.path.abspath(args.spec),
                validation_issues=validation_issues,
                dry_run=args.dry_run,
                headers=custom_headers,
                method_filter=args.method,
                tag_filter=args.tag,
            )

            if args.format == "json":
                out = format_json(report)
            elif args.format == "junit":
                out = format_junit_xml(report)
            else:
                out = format_terminal(report, use_color=not args.no_color)

            if args.output:
                try:
                    with open(args.output, "w", encoding="utf-8") as f:
                        f.write(out + "\n")
                    print(f"Report written to: {args.output}")
                except Exception as e:
                    sys.stderr.write(f"Failed to write output to {args.output}: {e}\n")
                    return 1
            else:
                print(out)

            if args.strict and not report.is_success:
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
