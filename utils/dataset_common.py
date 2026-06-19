"""
Shared dataset constants and report shape definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, TypedDict


STANDARD_DIRS = ["ASSEMBLIES", "GRAPH", "META"]
METADATA_RELATIVE_PATH = Path("META") / "dataset_info.yml"
VALID_INPUT_MODES = {"many", "single"}
MINIGRAPH_OUTPUT_FILENAME = "minigraph_graph.gfa"

INPUT_TO_DIR_MAPPING = {
    "assemblies": "ASSEMBLIES",
    "graph": "GRAPH",
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


class DirectoryState(TypedDict):
    exists: bool
    is_dir: bool
    empty: bool | None
    files_count: int


class DatasetStructure(TypedDict):
    directories: dict[str, DirectoryState]
    structure_ok: bool


class DatasetMetadataInfo(TypedDict):
    metadata_path: str
    metadata_exists: bool
    metadata: Dict[str, Any]


class DirectoryFileCheck(TypedDict):
    directory: str
    path: str
    expected_suffixes: list[str]
    matching_files: list[str]
    matching_count: int
    has_valid_files: bool


class DatasetReport(TypedDict):
    dataset_name: str
    dataset_path: str
    structure: DatasetStructure
    metadata_info: DatasetMetadataInfo
    status: str
    description: str | None
    expected_inputs: Dict[str, Any]
    supported_workflows: list[str] | Dict[str, Any]
    file_checks: dict[str, DirectoryFileCheck]
    ready_for_real_runs: bool
    tool_runnability: dict[str, ToolRunnability]
    resolved_inputs: dict[str, ToolInputs]
