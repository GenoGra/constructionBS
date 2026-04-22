from __future__ import annotations
from run_config import TOOL_REQUIREMENTS, EXPECTED_FILE_TYPES, TOOL_INPUT_SPECS

from pathlib import Path
from typing import Any, Dict, TypedDict
import yaml


STANDARD_DIRS = ["ASSEMBLIES", "GRAPH", "META", "READS", "TREE"]
METADATA_RELATIVE_PATH = Path("META") / "dataset_info.yml"

INPUT_TO_DIR_MAPPING = {
    "assemblies": "ASSEMBLIES",
    "graph": "GRAPH",
    "reads": "READS",
    "tree": "TREE",
}


class ToolRunnability(TypedDict):
    tool: str
    runnable: bool
    missing_requirements: list[str]
    reason: str | None


class ToolInputs(TypedDict):
    tool: str
    resolved: bool
    inputs: Dict[str, Any]
    missing: list[str]
    reason: str | None


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


def check_directory_state(path: Path) -> Dict[str, Any]:
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


def check_dataset_structure(dataset_path: Path) -> Dict[str, Any]:
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


def load_dataset_metadata(dataset_path: Path) -> Dict[str, Any]:
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


def infer_ready_for_real_runs(structure: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
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


def inspect_dataset(dataset_path: Path) -> Dict[str, Any]:
    """
    Build a complete inspection report for a dataset.
    """
    structure = check_dataset_structure(dataset_path)
    metadata = load_dataset_metadata(dataset_path)
    meta = metadata["metadata"]
    file_checks = inspect_dataset_files(dataset_path)

    report = {
        "dataset_name": dataset_path.name,
        "dataset_path": str(dataset_path),
        "structure": structure,
        "metadata_info": metadata,
        "status": meta.get("status", "unknown"),
        "description": meta.get("description", None),
        "expected_inputs": meta.get("expected_inputs", {}),
        "supported_workflows": meta.get("supported_workflows", {}),
        "file_checks": file_checks,
    }

    report["ready_for_real_runs"] = infer_ready_for_real_runs(structure, metadata)

    tool_runnability = {
        tool_name: get_tool_runnability(tool_name, report)
        for tool_name in TOOL_REQUIREMENTS
    }
    report["tool_runnability"] = tool_runnability

    resolved_inputs = {
        tool_name: get_tool_inputs(tool_name, report)
        for tool_name in TOOL_INPUT_SPECS
    }
    report["resolved_inputs"] = resolved_inputs

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

def _check_requirement(dirname: str, dir_info: dict[str, Any] | None, file_checks: dict[str, Any]) -> str | None:
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

    # META is structural: it is required to exist, but not to contain "valid input files"
    if dirname == "META":
        return None

    file_info = file_checks.get(dirname)
    if file_info is None:
        return f"{dirname} (no file check)"

    if not file_info.get("has_valid_files", False):
        return f"{dirname} (no valid files)"

    return None


def get_tool_runnability(tool_name: str, dataset_report: dict[str, Any]) -> ToolRunnability:
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

    result["runnable"] = True
    return result


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


def inspect_directory_files(dirname: str, dataset_path: Path) -> dict[str, Any]:
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

def inspect_dataset_files(dataset_path: Path) -> dict[str, Any]:
    """
    Inspect all standard dataset directories for expected file types.
    """
    return {dirname: inspect_directory_files(dirname, dataset_path) for dirname in STANDARD_DIRS}


def _resolve_input_spec(input_key: str, spec: dict[str, Any], file_checks: dict[str, Any]) -> tuple[bool, Any | None]:
    """
    Resolve a single input specification.
    Return (resolved, value) where:
      - resolved=False, value=None if input could not be resolved
      - resolved=True, value=<file or files> if input was resolved
    """
    source_dir = spec["source"]
    mode = spec["mode"]

    dir_info = file_checks.get(source_dir)
    if dir_info is None:
        return (False, None)

    matching_files = dir_info.get("matching_files", [])

    if mode == "many":
        return (bool(matching_files), matching_files if matching_files else None)
    elif mode == "single":
        return (bool(matching_files), matching_files[0] if matching_files else None)
    else:
        return (False, None)


def get_tool_inputs(tool_name: str, dataset_report: dict[str, Any]) -> ToolInputs:
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
        resolved, value = _resolve_input_spec(input_key, spec, file_checks)

        if resolved:
            result["inputs"][input_key] = value
        else:
            mode = spec.get("mode")
            if mode not in ["many", "single"]:
                result["missing"].append(f"{input_key} (invalid mode '{mode}')")
            else:
                result["missing"].append(input_key)

    if result["missing"]:
        result["reason"] = "one or more required inputs could not be resolved"
        return result

    result["resolved"] = True
    return result

def get_results_root() -> Path:
    """
    Return the root results directory.
    """
    return Path("results")


def get_dataset_results_path(dataset_name: str) -> Path:
    """
    Return the results path for a dataset.
    """
    return get_results_root() / dataset_name


def get_tool_results_path(dataset_name: str, tool_name: str) -> Path:
    """
    Return the results path for a tool inside a dataset.
    """
    return get_dataset_results_path(dataset_name) / tool_name


def get_tool_outputs_path(dataset_name: str, tool_name: str) -> Path:
    """
    Return the outputs directory for a tool inside a dataset.
    """
    return get_tool_results_path(dataset_name, tool_name) / "outputs"


def get_tool_logs_path(dataset_name: str, tool_name: str) -> Path:
    """
    Return the logs directory for a tool inside a dataset.
    """
    return get_tool_results_path(dataset_name, tool_name) / "logs"


def create_results_structure(dataset_name: str, tool_names: list[str]) -> dict[str, dict[str, str]]:
    """
    Create the standard results structure for a dataset and a list of tools.

    Structure:
        results/
          DATASET_NAME/
            TOOL_NAME/
              outputs/
              logs/

    Returns a dictionary with created paths.
    """
    created_paths: dict[str, dict[str, str]] = {}

    dataset_path = get_dataset_results_path(dataset_name)
    dataset_path.mkdir(parents=True, exist_ok=True)

    for tool_name in tool_names:
        outputs_path = get_tool_outputs_path(dataset_name, tool_name)
        logs_path = get_tool_logs_path(dataset_name, tool_name)

        outputs_path.mkdir(parents=True, exist_ok=True)
        logs_path.mkdir(parents=True, exist_ok=True)

        created_paths[tool_name] = {
            "outputs": str(outputs_path),
            "logs": str(logs_path),
        }

    return created_paths