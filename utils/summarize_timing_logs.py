"""
Build a compact Markdown summary table from per-tool timing logs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from run_config import RESULTS_ROOT
try:
    from utils.dataset_common import (
        LCPAN_TIMING_CANDIDATES,
        STANDARD_TOOL_ORDER,
        TOOL_TIMING_LOG_CANDIDATES,
        first_existing,
    )
except ModuleNotFoundError:
    from dataset_common import (
        LCPAN_TIMING_CANDIDATES,
        STANDARD_TOOL_ORDER,
        TOOL_TIMING_LOG_CANDIDATES,
        first_existing,
    )


ELAPSED_PREFIX = "Elapsed (wall clock) time"
EXIT_STATUS_PREFIX = "Exit status"


@dataclass(frozen=True)
class TimingSummary:
    tool: str
    elapsed: str
    elapsed_seconds: float | None
    exit_status: str
    timing_log: Path


def parse_elapsed_to_seconds(value: str) -> float | None:
    """
    Convert a GNU time elapsed string into seconds.
    """
    cleaned = value.strip()
    if not cleaned:
        return None

    parts = cleaned.split(":")
    try:
        numbers = [float(part) for part in parts]
    except ValueError:
        return None

    if len(numbers) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds

    if len(numbers) == 3:
        hours, minutes, seconds = numbers
        return hours * 3600 + minutes * 60 + seconds

    return None


def format_seconds(value: float | None) -> str:
    """
    Format parsed seconds for a compact numeric comparison column.
    """
    if value is None:
        return "NA"
    return f"{value:.2f}"


def extract_value(line: str) -> str:
    """
    Return the value part after the first ': ' separator in one GNU time line.
    """
    separator = ": "
    if separator in line:
        return line.split(separator, 1)[1].strip()
    return line.strip()


def parse_timing_log(timing_log: Path, tool: str) -> TimingSummary:
    """
    Extract the timing fields we trust for cross-tool comparisons.
    """
    elapsed = "MISSING"
    exit_status = "MISSING"

    for raw_line in timing_log.read_text().splitlines():
        line = raw_line.strip()
        if line.startswith(ELAPSED_PREFIX):
            elapsed = extract_value(raw_line)
        elif line.startswith(EXIT_STATUS_PREFIX):
            exit_status = extract_value(raw_line)

    return TimingSummary(
        tool=tool,
        elapsed=elapsed,
        elapsed_seconds=parse_elapsed_to_seconds(elapsed) if elapsed != "MISSING" else None,
        exit_status=exit_status,
        timing_log=timing_log,
    )


def build_table(dataset_name: str, summaries: list[TimingSummary]) -> str:
    """
    Render one Markdown summary table.
    """
    lines = [
        f"# Timing Summary: {dataset_name}",
        "",
        "| Tool | Elapsed | Elapsed (s) | Exit status | Timing log |",
        "| --- | --- | ---: | ---: | --- |",
    ]

    for summary in summaries:
        rel_log = summary.timing_log.relative_to(RESULTS_ROOT)
        lines.append(
            "| "
            f"{summary.tool} | "
            f"{summary.elapsed} | "
            f"{format_seconds(summary.elapsed_seconds)} | "
            f"{summary.exit_status} | "
            f"`{rel_log}` |"
        )

    lines.extend(
        [
            "",
            "Notes:",
            "- `Elapsed` is the main metric to compare end-to-end runtime.",
            "- `Exit status` confirms whether the run completed successfully.",
            "- Timing is now measured inside the container around the tool itself, so the "
            "GNU time CPU%, User/System time, and peak RAM fields reflect the tool, not the docker client.",
            "- `MC_vg` is tracked as a standalone tool; `from_MC_vg` and `from_MC_vgx` are downstream LCPan variants.",
        ]
    )
    return "\n".join(lines) + "\n"


def discover_summaries(dataset_name: str) -> list[TimingSummary]:
    """
    Collect timing summaries for the standard tool directories in one dataset.
    LCPan runs are expanded into explicit input/mode variants when present.
    """
    dataset_dir = RESULTS_ROOT / dataset_name
    summaries: list[TimingSummary] = []

    for tool in STANDARD_TOOL_ORDER:
        candidates = TOOL_TIMING_LOG_CANDIDATES.get(tool, (f"{tool}/logs/timing.log",))
        timing_log = first_existing(dataset_dir, candidates)
        if timing_log is None:
            continue
        summaries.append(parse_timing_log(timing_log, tool))

    for tool, relative_candidates in LCPAN_TIMING_CANDIDATES.items():
        timing_log = first_existing(dataset_dir, relative_candidates)
        if timing_log is None:
            continue
        summaries.append(parse_timing_log(timing_log, tool))

    if not summaries:
        raise FileNotFoundError(f"no timing.log files found under {dataset_dir}")

    return summaries


def sanitize_dataset_name(value: str) -> str:
    """
    Allow only standard dataset tokens.
    """
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError(f"invalid dataset name: {value}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize timing.log files into a Markdown table."
    )
    parser.add_argument("dataset_name", help="Dataset under results/, for example C4_TEST")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional explicit output path (default: results/<DATASET>/timing_summary.md)",
    )
    args = parser.parse_args()

    dataset_name = sanitize_dataset_name(args.dataset_name)
    summaries = discover_summaries(dataset_name)
    dataset_dir = RESULTS_ROOT / dataset_name
    output_path = Path(args.output) if args.output else dataset_dir / "timing_summary.md"

    output_path.write_text(build_table(dataset_name, summaries))
    print(output_path)


if __name__ == "__main__":
    main()
