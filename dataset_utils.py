from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml


STANDARD_DIRS = ["ASSEMBLIES", "GRAPH", "META", "READS", "TREE"]
METADATA_RELATIVE_PATH = Path("META") / "dataset_info.yml"


def load_yaml_file(path: Path) -> Dict[str, Any]:
    """
    Load a YAML file and return a dictionary.
    If the file does not exist or is empty, return an empty dict.
    """
    if not path.exists() or not path.is_file():
        return {}

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

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
    directories: Dict[str, Dict[str, Any]] = {}

    for dirname in STANDARD_DIRS:
        dir_path = dataset_path / dirname
        directories[dirname] = check_directory_state(dir_path)

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

    mapping = {
        "assemblies": "ASSEMBLIES",
        "graph": "GRAPH",
        "reads": "READS",
        "tree": "TREE",
    }

    for key, dirname in mapping.items():
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

    report = {
        "dataset_name": dataset_path.name,
        "dataset_path": str(dataset_path),
        "structure": structure,
        "metadata_info": metadata,
        "status": meta.get("status", "unknown"),
        "description": meta.get("description", None),
        "expected_inputs": meta.get("expected_inputs", {}),
        "supported_workflows": meta.get("supported_workflows", {}),
    }

    report["ready_for_real_runs"] = infer_ready_for_real_runs(structure, metadata)

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

def is_tool_runnable(tool_name: str, dataset_report: dict) -> bool:
    """
    Check if a tool can run on the given dataset based on required directories.
    """
    requirements = TOOL_REQUIREMENTS.get(tool_name, {})
    required_dirs = requirements.get("required_dirs", [])

    directories = dataset_report["structure"]["directories"]

    for dirname in required_dirs:
        dir_info = directories.get(dirname, {})
        if not dir_info.get("exists") or not dir_info.get("is_dir") or dir_info.get("empty"):
            return False

    return True