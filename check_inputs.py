# Detailed report tool

from __future__ import annotations

from pathlib import Path
import argparse

from dataset_utils import find_datasets, inspect_dataset


def format_bool(value: bool) -> str:
    """
    Convert a boolean to a formatted string representation.
    """
    return "true" if value else "false"


def format_directory_line(name: str, info: dict) -> str:
    """
    Format a directory status line for display.
    """
    if not info["exists"]:
        return f"- {name}: missing"

    if not info["is_dir"]:
        return f"- {name}: exists but is not a directory"

    if info["empty"]:
        return f"- {name}: present, empty"

    return f"- {name}: present, not empty ({info['files_count']} items)"


def format_valid_files_line(dirname: str, info: dict) -> str:
    """
    Format a line describing the status of valid files in a dataset directory.
    """
    if info["has_valid_files"]:
        return (
            f"- {dirname}: valid files found "
            f"({info['matching_count']})"
        )

    suffixes = ", ".join(info["expected_suffixes"]) if info["expected_suffixes"] else "none"
    return f"- {dirname}: no valid files found (expected: {suffixes})"


def format_tool_runnability_line(tool_name: str, info: dict) -> str:
    """
    Format a line describing the runnability status of a tool for a dataset.
    """
    if info["runnable"]:
        return f"- {tool_name}: runnable"

    if info["missing_requirements"]:
        missing = "; ".join(info["missing_requirements"])
        return f"- {tool_name}: not runnable ({missing})"

    reason = info["reason"] if info["reason"] else "unknown reason"
    return f"- {tool_name}: not runnable ({reason})"


def print_dataset_report(report: dict) -> None:
    """
    Print a formatted dataset inspection report.
    """
    print(f"=== Dataset check: {report['dataset_name']} ===")
    print(f"Path: {report['dataset_path']}")
    print(f"Status: {report['status']}")
    print(f"Description: {report['description']}")
    print()

    print("Directories:")
    for dirname, info in report["structure"]["directories"].items():
        print(format_directory_line(dirname, info))
    print()

    print("Metadata:")
    print(f"- metadata_exists: {format_bool(report['metadata_info']['metadata_exists'])}")
    print(f"- metadata_path: {report['metadata_info']['metadata_path']}")
    print()

    print("Expected inputs:")
    expected_inputs = report["expected_inputs"]
    if expected_inputs:
        for key, value in expected_inputs.items():
            print(f"- {key}: {format_bool(bool(value))}")
    else:
        print("- none declared")
    print()

    print("Supported workflows:")
    supported_workflows = report["supported_workflows"]
    if supported_workflows:
        for key, value in supported_workflows.items():
            print(f"- {key}: {format_bool(bool(value))}")
    else:
        print("- none declared")
    print()

    print("Valid files by directory:")
    file_checks = report.get("file_checks", {})
    if file_checks:
        for dirname, info in file_checks.items():
            print(format_valid_files_line(dirname, info))
    else:
        print("- no file checks available")
    print()

    print("Tool runnability:")
    tool_runnability = report.get("tool_runnability", {})
    if tool_runnability:
        for tool_name, info in tool_runnability.items():
            print(format_tool_runnability_line(tool_name, info))
    else:
        print("- no tool runnability information available")
    print()

    print("Resolved inputs by tool:")
    resolved_inputs = report.get("resolved_inputs", {})
    if resolved_inputs:
        for tool_name, info in resolved_inputs.items():
            print(format_resolved_inputs_line(tool_name, info))
    else:
        print("- no resolved input information available")
    print()

    print("Overall result:")
    print(f"- structure_ok: {format_bool(report['structure']['structure_ok'])}")
    print(f"- ready_for_real_runs: {format_bool(report['ready_for_real_runs'])}")
    print()


def format_resolved_inputs_line(tool_name: str, info: dict) -> str:
    """
    Format a line describing the resolved inputs status for a tool.
    """
    if info["resolved"]:
        input_keys = ", ".join(info["inputs"].keys())
        return f"- {tool_name}: resolved ({input_keys})"

    if info["missing"]:
        missing = ", ".join(info["missing"])
        return f"- {tool_name}: unresolved (missing: {missing})"

    reason = info["reason"] if info["reason"] else "unknown reason"
    return f"- {tool_name}: unresolved ({reason})"


def main() -> None:
    """
    Main entry point: parse arguments and inspect datasets.
    """
    parser = argparse.ArgumentParser(description="Inspect input_data datasets structure.")
    parser.add_argument(
        "--input-data",
        default="input_data",
        help="Path to the input_data directory (default: input_data)",
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Optional dataset name to inspect only one dataset",
    )
    args = parser.parse_args()

    input_data_path = Path(args.input_data)

    if not input_data_path.exists() or not input_data_path.is_dir():
        print(f"[ERROR] input_data directory not found: {input_data_path}")
        return

    datasets = find_datasets(input_data_path)

    if args.dataset is not None:
        datasets = [path for path in datasets if path.name == args.dataset]

    if not datasets:
        print("[INFO] No datasets found.")
        return

    for dataset_path in datasets:
        try:
            report = inspect_dataset(dataset_path)
            print_dataset_report(report)
        except Exception as e:
            print(f"[ERROR] Failed to inspect dataset {dataset_path.name}: {e}")
            print()


if __name__ == "__main__":
    main()