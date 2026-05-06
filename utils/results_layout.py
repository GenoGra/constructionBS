"""
Helpers for results layout creation and wrapped command generation.
"""

from __future__ import annotations

from pathlib import Path
import shlex

from utils.dataset_common import DatasetReport, MINIGRAPH_OUTPUT_FILENAME
from utils.input_resolution import get_tool_inputs


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


def get_tool_execution_log_path(dataset_name: str, tool_name: str) -> Path:
    """
    Return the execution log path for a tool inside a dataset.
    """
    return get_tool_logs_path(dataset_name, tool_name) / "execution.log"


def get_tool_timing_log_path(dataset_name: str, tool_name: str) -> Path:
    """
    Return the timing log path for a tool inside a dataset.
    """
    return get_tool_logs_path(dataset_name, tool_name) / "timing.log"


def get_minigraph_graph_output_path(dataset_name: str) -> Path:
    """
    Return the output graph path for a Minigraph construction run.
    """
    return get_tool_outputs_path(dataset_name, "Minigraph") / MINIGRAPH_OUTPUT_FILENAME


def get_tool_log_paths(dataset_name: str, tool_name: str) -> tuple[Path, Path]:
    """
    Return the standard execution and timing log paths for a tool run.
    """
    return (
        get_tool_execution_log_path(dataset_name, tool_name),
        get_tool_timing_log_path(dataset_name, tool_name),
    )


def create_results_structure(dataset_name: str, tool_names: list[str]) -> dict[str, dict[str, str]]:
    """
    Create the standard results structure for a dataset and a list of tools.
    """
    created_paths: dict[str, dict[str, str]] = {}

    dataset_path = get_dataset_results_path(dataset_name)
    dataset_path.mkdir(parents=True, exist_ok=True)

    for tool_name in tool_names:
        outputs_path = get_tool_outputs_path(dataset_name, tool_name)
        logs_path = get_tool_logs_path(dataset_name, tool_name)

        outputs_path.mkdir(parents=True, exist_ok=True)
        logs_path.mkdir(parents=True, exist_ok=True)

        execution_log_path, timing_log_path = get_tool_log_paths(dataset_name, tool_name)

        execution_log_path.touch(exist_ok=True)
        timing_log_path.touch(exist_ok=True)

        created_paths[tool_name] = {
            "outputs": str(outputs_path),
            "logs": str(logs_path),
            "execution_log": str(execution_log_path),
            "timing_log": str(timing_log_path),
        }

    return created_paths


def build_wrapped_command(
    dataset_name: str,
    tool_name: str,
    real_command: str,
) -> str:
    """
    Wrap a real tool command with standard execution/timing logging.
    """
    execution_log, timing_log = get_tool_log_paths(dataset_name, tool_name)

    quoted_real_command = shlex.quote(real_command)
    quoted_execution_log = shlex.quote(str(execution_log))
    quoted_timing_log = shlex.quote(str(timing_log))

    return (
        f"/usr/bin/time -v -o {quoted_timing_log} "
        f"bash -c {quoted_real_command} "
        f"> {quoted_execution_log} 2>&1"
    )


def get_wrapped_command_preview(
    dataset_name: str,
    tool_name: str,
    real_command: str,
) -> dict[str, str]:
    """
    Return a structured preview of the wrapped command and log destinations.
    """
    execution_log, timing_log = get_tool_log_paths(dataset_name, tool_name)

    return {
        "tool": tool_name,
        "dataset": dataset_name,
        "real_command": real_command,
        "wrapped_command": build_wrapped_command(dataset_name, tool_name, real_command),
        "execution_log": str(execution_log),
        "timing_log": str(timing_log),
    }


def build_minigraph_construction_command(dataset_report: DatasetReport) -> str:
    """
    Build the real Minigraph graph-construction command for a dataset.
    """
    dataset_name = dataset_report["dataset_name"]
    tool_inputs = get_tool_inputs("Minigraph", dataset_report)
    if not tool_inputs["resolved"]:
        reason = tool_inputs["reason"] or "unable to resolve Minigraph inputs"
        raise ValueError(reason)

    assemblies = tool_inputs["inputs"]["assemblies"]
    if not isinstance(assemblies, list) or len(assemblies) < 2:
        raise ValueError("Minigraph graph construction requires at least two assembly FASTA files")

    reference = assemblies[0]
    sample_assemblies = assemblies[1:]
    quoted_inputs = " ".join(shlex.quote(path) for path in [reference, *sample_assemblies])
    quoted_output = shlex.quote(str(get_minigraph_graph_output_path(dataset_name)))

    return (
        "cd /minigraph && "
        f"./minigraph -cxggs {quoted_inputs} > {quoted_output}"
    )


def get_minigraph_construction_command_preview(dataset_report: DatasetReport) -> dict[str, str]:
    """
    Return a structured preview for the Minigraph graph-construction command.
    """
    dataset_name = dataset_report["dataset_name"]
    real_command = build_minigraph_construction_command(dataset_report)
    wrapped_preview = get_wrapped_command_preview(dataset_name, "Minigraph", real_command)

    return {
        **wrapped_preview,
        "output_graph": str(get_minigraph_graph_output_path(dataset_name)),
    }
