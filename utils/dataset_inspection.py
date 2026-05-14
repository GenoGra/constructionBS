"""
Utilities for discovering datasets, validating layout, and computing reports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from run_config import EXPECTED_FILE_TYPES, TOOL_REQUIREMENTS
from utils.dataset_metadata import (
    get_dataset_short_name,
    get_metadata_value,
    infer_dataset_short_from_name,
)
from utils.dataset_common import (
    DatasetMetadataInfo,
    DatasetReport,
    DatasetStructure,
    DirectoryFileCheck,
    DirectoryState,
    INPUT_TO_DIR_MAPPING,
    METADATA_RELATIVE_PATH,
    STANDARD_DIRS,
    ToolRunnability,
)
from utils.input_resolution import get_tool_inputs


def load_yaml_file(path: Path) -> Dict[str, Any]:
    """
    Load a YAML file and return a dictionary.
    If the file does not exist, is empty, or has invalid YAML, return an empty dict.
    """
    if not path.exists() or not path.is_file():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError:
        return {}

    return data if isinstance(data, dict) else {}


def check_directory_state(path: Path) -> DirectoryState:
    """
    Return basic information about a directory:
    - exists
    - is_dir
    - empty
    - files_count
    """
    exists = path.exists()
    is_dir = path.is_dir()

    if not exists or not is_dir:
        return {
            "exists": exists,
            "is_dir": is_dir,
            "empty": None,
            "files_count": 0,
        }

    items = list(path.iterdir())
    return {
        "exists": True,
        "is_dir": True,
        "empty": len(items) == 0,
        "files_count": len(items),
    }


def check_dataset_structure(dataset_path: Path) -> DatasetStructure:
    """
    Check whether all standard directories exist inside the dataset path.
    """
    directories = {dirname: check_directory_state(dataset_path / dirname) for dirname in STANDARD_DIRS}

    structure_ok = all(
        directories[dirname]["exists"] and directories[dirname]["is_dir"]
        for dirname in STANDARD_DIRS
    )

    return {
        "directories": directories,
        "structure_ok": structure_ok,
    }


def get_metadata_path(dataset_path: Path) -> Path:
    """
    Return the expected metadata file path for a dataset.
    """
    return dataset_path / METADATA_RELATIVE_PATH


def load_dataset_metadata(dataset_path: Path) -> DatasetMetadataInfo:
    """
    Load dataset metadata from META/dataset_info.yml.
    """
    metadata_path = get_metadata_path(dataset_path)
    metadata = load_yaml_file(metadata_path)

    return {
        "metadata_path": str(metadata_path),
        "metadata_exists": metadata_path.exists(),
        "metadata": metadata,
    }


def infer_ready_for_real_runs(
    structure: DatasetStructure,
    metadata: DatasetMetadataInfo,
) -> bool:
    """
    Infer if a dataset is ready for real runs.
    Current policy:
    - structure must be OK
    - metadata must exist
    - status must not be 'placeholder'
    - if an expected input is marked True, the corresponding directory must be non-empty
    """
    if not structure["structure_ok"]:
        return False

    if not metadata["metadata_exists"]:
        return False

    meta = metadata["metadata"]
    status = meta.get("status", "unknown")
    if status == "placeholder":
        return False

    expected_inputs = meta.get("expected_inputs", {})
    directories = structure["directories"]

    for key, dirname in INPUT_TO_DIR_MAPPING.items():
        expected = expected_inputs.get(key, False)
        dir_info = directories[dirname]

        if expected:
            if not dir_info["exists"] or not dir_info["is_dir"] or dir_info["empty"]:
                return False

    return True


def find_matching_files(directory: Path, allowed_suffixes: list[str]) -> list[Path]:
    """
    Return files in a directory whose suffix matches one of the allowed suffixes.
    Matching is case-insensitive.
    """
    if not directory.exists() or not directory.is_dir():
        return []

    allowed = {suffix.lower() for suffix in allowed_suffixes}

    return sorted(
        [
            path for path in directory.iterdir()
            if path.is_file() and path.suffix.lower() in allowed
        ],
        key=lambda p: p.name.lower(),
    )


def inspect_directory_files(dirname: str, dataset_path: Path) -> DirectoryFileCheck:
    """
    Inspect valid files for one standard dataset directory.
    """
    dir_path = dataset_path / dirname
    expected_suffixes = EXPECTED_FILE_TYPES.get(dirname, [])

    matching_files = find_matching_files(dir_path, expected_suffixes)

    return {
        "directory": dirname,
        "path": str(dir_path),
        "expected_suffixes": expected_suffixes,
        "matching_files": [str(path) for path in matching_files],
        "matching_count": len(matching_files),
        "has_valid_files": len(matching_files) > 0,
    }


def inspect_dataset_files(dataset_path: Path) -> dict[str, DirectoryFileCheck]:
    """
    Inspect all standard dataset directories for expected file types.
    """
    return {dirname: inspect_directory_files(dirname, dataset_path) for dirname in STANDARD_DIRS}


def build_dataset_report_base(dataset_path: Path) -> DatasetReport:
    """
    Build the core dataset report before tool-specific enrichment.
    """
    structure = check_dataset_structure(dataset_path)
    metadata = load_dataset_metadata(dataset_path)
    meta = metadata["metadata"]
    file_checks = inspect_dataset_files(dataset_path)

    return {
        "dataset_name": dataset_path.name,
        "dataset_path": str(dataset_path),
        "structure": structure,
        "metadata_info": metadata,
        "status": meta.get("status", "unknown"),
        "description": meta.get("description"),
        "expected_inputs": meta.get("expected_inputs", {}),
        "supported_workflows": meta.get("supported_workflows", {}),
        "file_checks": file_checks,
        "ready_for_real_runs": infer_ready_for_real_runs(structure, metadata),
        "tool_runnability": {},
        "resolved_inputs": {},
    }


def _check_requirement(
    dirname: str,
    dir_info: DirectoryState | None,
    file_checks: dict[str, DirectoryFileCheck],
) -> str | None:
    """
    Check if a single directory requirement is satisfied.
    Return error reason if not satisfied, None if satisfied.
    """
    if dir_info is None:
        return f"{dirname} (not declared)"

    if not dir_info["exists"]:
        return f"{dirname} (missing)"

    if not dir_info["is_dir"]:
        return f"{dirname} (not a directory)"

    if dirname == "META":
        return None

    file_info = file_checks.get(dirname)
    if file_info is None:
        return f"{dirname} (no file check)"

    if not file_info.get("has_valid_files", False):
        return f"{dirname} (no valid files)"

    return None


def get_tool_runnability(tool_name: str, dataset_report: DatasetReport) -> ToolRunnability:
    """
    Determine whether a tool is runnable on a given dataset report.
    """
    result: ToolRunnability = {
        "tool": tool_name,
        "runnable": False,
        "missing_requirements": [],
        "reason": None,
    }

    if not dataset_report["structure"]["structure_ok"]:
        result["reason"] = "dataset structure is not valid"
        return result

    requirements = TOOL_REQUIREMENTS.get(tool_name)
    if requirements is None:
        result["reason"] = f"no requirements defined for tool {tool_name}"
        return result

    required_dirs = requirements.get("required_dirs", [])
    directories = dataset_report["structure"]["directories"]
    file_checks = dataset_report.get("file_checks", {})

    for dirname in required_dirs:
        dir_info = directories.get(dirname)
        requirement_error = _check_requirement(dirname, dir_info, file_checks)

        if requirement_error is not None:
            result["missing_requirements"].append(requirement_error)

    if result["missing_requirements"]:
        result["reason"] = "missing required inputs"
        return result

    tool_inputs = get_tool_inputs(tool_name, dataset_report)
    if not tool_inputs["resolved"]:
        result["missing_requirements"].extend(tool_inputs["missing"])
        result["reason"] = tool_inputs["reason"] or "required tool inputs could not be resolved"
        return result

    result["runnable"] = True
    return result


def attach_tool_runnability(report: DatasetReport) -> None:
    """
    Populate tool runnability information in-place.
    """
    report["tool_runnability"] = {
        tool_name: get_tool_runnability(tool_name, report)
        for tool_name in TOOL_REQUIREMENTS
    }


def attach_resolved_inputs(report: DatasetReport) -> None:
    """
    Populate resolved tool inputs in-place.
    """
    report["resolved_inputs"] = {
        tool_name: get_tool_inputs(tool_name, report)
        for tool_name in TOOL_REQUIREMENTS
    }


def inspect_dataset(dataset_path: Path) -> DatasetReport:
    """
    Build a complete inspection report for a dataset.
    """
    report = build_dataset_report_base(dataset_path)
    attach_tool_runnability(report)
    attach_resolved_inputs(report)
    return report


def find_datasets(input_data_path: Path) -> list[Path]:
    """
    Find first-level dataset directories inside input_data.
    """
    if not input_data_path.exists() or not input_data_path.is_dir():
        return []

    return sorted(
        [path for path in input_data_path.iterdir() if path.is_dir()],
        key=lambda p: p.name.lower(),
    )
