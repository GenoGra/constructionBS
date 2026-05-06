"""
Compatibility facade for dataset discovery, validation, input resolution, and
results-layout helpers.
"""

from __future__ import annotations

from utils.dataset_common import (
    DatasetMetadataInfo,
    DatasetReport,
    DatasetStructure,
    DirectoryFileCheck,
    DirectoryState,
    INPUT_TO_DIR_MAPPING,
    METADATA_RELATIVE_PATH,
    MINIGRAPH_OUTPUT_FILENAME,
    STANDARD_DIRS,
    ToolInputs,
    ToolRunnability,
    VALID_INPUT_MODES,
)
from utils.dataset_inspection import (
    attach_resolved_inputs,
    attach_tool_runnability,
    build_dataset_report_base,
    check_dataset_structure,
    check_directory_state,
    find_datasets,
    find_matching_files,
    get_metadata_path,
    get_tool_runnability,
    infer_ready_for_real_runs,
    inspect_dataset,
    inspect_dataset_files,
    inspect_directory_files,
    load_dataset_metadata,
    load_yaml_file,
)
from utils.input_resolution import get_tool_inputs
from utils.results_layout import (
    build_minigraph_construction_command,
    build_wrapped_command,
    create_results_structure,
    get_dataset_results_path,
    get_minigraph_construction_command_preview,
    get_minigraph_graph_output_path,
    get_results_root,
    get_tool_execution_log_path,
    get_tool_log_paths,
    get_tool_logs_path,
    get_tool_outputs_path,
    get_tool_results_path,
    get_tool_timing_log_path,
    get_wrapped_command_preview,
)
