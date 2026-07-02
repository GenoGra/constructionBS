"""
Command-line helper that inspects datasets under ``input_data`` and prints
human-readable reports about structure, metadata, valid files, and tool
readiness.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable
import argparse
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from utils.dataset_inspection import find_datasets, inspect_dataset
except ModuleNotFoundError:
    # Allow direct execution via `python utils/check_inputs.py`.
    from dataset_inspection import find_datasets, inspect_dataset


def format_bool(value: bool) -> str:
    """
    Convert a boolean to a formatted string representation.
    """
    return "true" if value else "false"


def format_directory_line(name: str, info: dict[str, Any]) -> str:
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


def format_valid_files_line(dirname: str, info: dict[str, Any]) -> str:
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


def format_tool_runnability_line(tool_name: str, info: dict[str, Any]) -> str:
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


def format_resolved_inputs_line(tool_name: str, info: dict[str, Any]) -> str:
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


def format_workflow_line(name: str, _: Any = None) -> str:
    """
    Format a workflow entry for display.
    """
    return f"- {name}: {format_bool(bool(_))}"


def _print_section(
    title: str,
    items: dict[str, Any] | Iterable[Any],
    format_fn: Callable[[str, Any], str],
    empty_msg: str = "- none",
) -> None:
    """
    Print a report section with a title, formatted items, and empty message.
    """
    print(f"{title}:")
    if isinstance(items, dict):
        if items:
            for key, value in items.items():
                print(format_fn(key, value))
        else:
            print(empty_msg)
    elif items:
        for item in items:
            print(format_fn(str(item), True))
    else:
        print(empty_msg)
    print()


def _normalize_supported_workflows(value: Any) -> dict[str, bool] | list[str]:
    """
    Normalize supported_workflows metadata into a display-friendly shape.
    """
    if isinstance(value, dict):
        return value

    if isinstance(value, list):
        return [str(item) for item in value]

    return {}


def print_dataset_report(report: dict[str, Any]) -> None:
    """
    Print a formatted dataset inspection report.
    """
    supported_workflows = _normalize_supported_workflows(report["supported_workflows"])

    print(f"=== Dataset check: {report['dataset_name']} ===")
    print(f"Path: {report['dataset_path']}")
    print(f"Status: {report['status']}")
    print(f"Description: {report['description']}")
    print()

    # Directories
    print("Directories:")
    for dirname, info in report["structure"]["directories"].items():
        print(format_directory_line(dirname, info))
    print()

    # Metadata
    print("Metadata:")
    print(f"- metadata_exists: {format_bool(report['metadata_info']['metadata_exists'])}")
    print(f"- metadata_path: {report['metadata_info']['metadata_path']}")
    print()

    # Expected inputs
    _print_section(
        "Expected inputs",
        report["expected_inputs"],
        lambda k, v: f"- {k}: {format_bool(bool(v))}",
        "- none declared",
    )

    # Supported workflows
    _print_section(
        "Supported workflows",
        supported_workflows,
        format_workflow_line,
        "- none declared",
    )

    # Valid files by directory
    _print_section(
        "Valid files by directory",
        report.get("file_checks", {}),
        format_valid_files_line,
        "- no file checks available",
    )

    # Tool runnability
    _print_section(
        "Tool runnability",
        report.get("tool_runnability", {}),
        format_tool_runnability_line,
        "- no tool runnability information available",
    )

    # Resolved inputs by tool
    _print_section(
        "Resolved inputs by tool",
        report.get("resolved_inputs", {}),
        format_resolved_inputs_line,
        "- no resolved input information available",
    )

    # Overall result
    print("Overall result:")
    print(f"- structure_ok: {format_bool(report['structure']['structure_ok'])}")
    print(f"- ready_for_real_runs: {format_bool(report['ready_for_real_runs'])}")
    print()


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
