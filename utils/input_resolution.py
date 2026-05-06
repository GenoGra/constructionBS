"""
Helpers for resolving tool-specific dataset inputs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import fnmatch

from run_config import TOOL_INPUT_SPECS
from utils.dataset_common import DatasetReport, DirectoryFileCheck, ToolInputs, VALID_INPUT_MODES


def _resolve_input_spec(
    input_key: str,
    spec: dict[str, Any],
    file_checks: dict[str, DirectoryFileCheck],
) -> tuple[bool, Any | None, str | None]:
    """
    Resolve a single input specification.

    Returns:
      (resolved, value, error_reason)

    Where:
      - resolved=False, value=None, error_reason=<reason> if input could not be resolved
      - resolved=True, value=<file or files>, error_reason=None if input was resolved
    """
    source_dir = spec["source"]
    mode = spec["mode"]
    min_count = spec.get("min_count")

    dir_info = file_checks.get(source_dir)
    if dir_info is None:
        return (False, None, "missing source directory information")

    matching_files = dir_info.get("matching_files", [])
    name_pattern = spec.get("name_pattern")
    if name_pattern:
        matching_files = [
            file_path
            for file_path in matching_files
            if fnmatch.fnmatch(Path(file_path).name, name_pattern)
        ]

    if mode == "many":
        if min_count is not None and len(matching_files) < min_count:
            return (
                False,
                None,
                f"expected at least {min_count} valid files, found {len(matching_files)}",
            )
        if matching_files:
            return (True, matching_files, None)
        return (False, None, "no valid files")

    if mode == "single":
        if len(matching_files) == 1:
            return (True, matching_files[0], None)
        if len(matching_files) == 0:
            return (False, None, "no valid files")
        return (False, None, "ambiguous: multiple valid files found")

    return (False, None, f"invalid mode '{mode}'")


def get_tool_inputs(tool_name: str, dataset_report: DatasetReport) -> ToolInputs:
    """
    Resolve concrete input file paths for a given tool using dataset file checks.

    Returns:
        ToolInputs dict.
    """
    result: ToolInputs = {
        "tool": tool_name,
        "resolved": False,
        "inputs": {},
        "missing": [],
        "reason": None,
    }

    specs = TOOL_INPUT_SPECS.get(tool_name)
    if specs is None:
        result["reason"] = f"no input specs defined for tool {tool_name}"
        return result

    file_checks = dataset_report.get("file_checks", {})

    for input_key, spec in specs.items():
        resolved, value, error_reason = _resolve_input_spec(input_key, spec, file_checks)

        if resolved:
            result["inputs"][input_key] = value
        else:
            mode = spec.get("mode")
            if mode not in VALID_INPUT_MODES:
                result["missing"].append(f"{input_key} (invalid mode '{mode}')")
            elif error_reason is not None:
                result["missing"].append(f"{input_key} ({error_reason})")
            else:
                result["missing"].append(input_key)

    if result["missing"]:
        result["reason"] = "one or more required inputs could not be resolved"
        return result

    result["resolved"] = True
    return result
