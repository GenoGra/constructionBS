"""
Build a compact Markdown summary table from per-tool timing logs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re


STANDARD_TOOL_ORDER = [
    "PGGB",
    "Minigraph",
    "MinigraphCactus",
    "MC_vg",
    "Cactus",
    "ProgressiveCactus",
]

LCPAN_TIMING_CANDIDATES = {
    "LCPan_PGGB_vg": (
        "LCPan/pggb_vg/logs/timing.log",
        "LCPan/logs/timing.log",
    ),
    "LCPan_PGGB_vgx": (
        "LCPan/pggb_vgx/logs/timing.log",
        "LCPan/logs_vgx/timing.log",
    ),
    "LCPan_from_MC_vg": (
        "LCPan/mc_vg/logs/timing.log",
        "LCPan/cactus_vcf_test/logs_vg/timing.log",
    ),
    "LCPan_from_MC_vgx": (
        "LCPan/mc_vgx/logs/timing.log",
        "LCPan/cactus_vcf_test/logs_vgx/timing.log",
    ),
}

TOOL_TIMING_SUMMARY_CONFIG = (
    ("PGGB", "pggb_timing_summary.md", "PGGB", ()),
    ("Minigraph", "minigraph_timing_summary.md", "Minigraph", ()),
    ("LCPan", "lcpan_timing_summary.md", "LCPan", ("pggb_vg", "pggb_vgx", "from_MC_vg", "from_MC_vgx")),
)

LCPAN_TOOL_SUMMARY_CANDIDATES = {
    "pggb_vg": (
        "LCPan/pggb_vg/logs/timing.log",
        "LCPan/logs/timing.log",
    ),
    "pggb_vgx": (
        "LCPan/pggb_vgx/logs/timing.log",
        "LCPan/logs_vgx/timing.log",
    ),
    "from_MC_vg": (
        "LCPan/mc_vg/logs/timing.log",
        "LCPan/cactus_vcf_test/logs_vg/timing.log",
    ),
    "from_MC_vgx": (
        "LCPan/mc_vgx/logs/timing.log",
        "LCPan/cactus_vcf_test/logs_vgx/timing.log",
    ),
}

THREAD_FLAG_PATTERNS = (
    re.compile(r"(?:^|\s)-t\s+(\d+)(?:\s|$)"),
    re.compile(r"(?:^|\s)--threads\s+(\d+)(?:\s|$)"),
)

THREAD_LABEL_PATTERNS = (
    re.compile(r"(?:^|[_-])t(\d+)(?:$|[_-])", re.IGNORECASE),
    re.compile(r"(?:^|[_-])threads?[_-]?(\d+)(?:$|[_-])", re.IGNORECASE),
)

ELAPSED_PREFIX = "Elapsed (wall clock) time"
EXIT_STATUS_PREFIX = "Exit status"
REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = REPO_ROOT / "results"

TOOL_TIMING_LOG_CANDIDATES = {
    "MC_vg": (
        "MC_vg/logs/timing.log",
        "MC_vg/logs/timing_cactus_pangenome.log",
    ),
}


@dataclass(frozen=True)
class TimingSummary:
    tool: str
    elapsed: str
    elapsed_seconds: float | None
    exit_status: str
    timing_log: Path


@dataclass(frozen=True)
class ToolTimingRun:
    tool: str
    variant: str | None
    run_label: str
    threads: str
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


def infer_threads_from_text(value: str) -> str | None:
    """
    Extract a thread count from one command line when the flag is present.
    """
    for pattern in THREAD_FLAG_PATTERNS:
        match = pattern.search(value)
        if match:
            return match.group(1)
    return None


def infer_threads_from_label(run_label: str) -> str | None:
    """
    Extract a thread count from a run label such as t32 or threads-32.
    """
    for pattern in THREAD_LABEL_PATTERNS:
        match = pattern.search(run_label)
        if match:
            return match.group(1)
    return None


def infer_threads(run_dir: Path, timing_log: Path) -> str:
    """
    Prefer execution.log for thread detection and fall back to the run label.
    """
    execution_log = timing_log.parent / "execution.log"
    if execution_log.exists():
        threads = infer_threads_from_text(execution_log.read_text(errors="replace"))
        if threads is not None:
            return threads

    threads = infer_threads_from_label(run_dir.name)
    if threads is not None:
        return threads

    return "default"


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
            "- CPU and RAM fields from these Docker-wrapped logs are not reliable for cross-tool comparisons.",
            "- `MC_vg` is tracked as a standalone tool; `LCPan_from_MC_vg` and `LCPan_from_MC_vgx` are downstream LCPan variants.",
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
        timing_log = next(
            (
                dataset_dir / relative_path
                for relative_path in TOOL_TIMING_LOG_CANDIDATES.get(tool, (f"{tool}/logs/timing.log",))
                if (dataset_dir / relative_path).exists()
            ),
            None,
        )
        if timing_log is None:
            continue
        summaries.append(parse_timing_log(timing_log, tool))

    for tool, relative_candidates in LCPAN_TIMING_CANDIDATES.items():
        timing_log = next(
            (dataset_dir / candidate for candidate in relative_candidates if (dataset_dir / candidate).exists()),
            None,
        )
        if timing_log is None:
            continue
        summaries.append(parse_timing_log(timing_log, tool))

    if not summaries:
        raise FileNotFoundError(f"no timing.log files found under {dataset_dir}")

    return summaries


def build_tool_timing_table(dataset_name: str, tool: str, runs: list[ToolTimingRun]) -> str:
    """
    Render one Markdown timing table for one tool across multiple runs.
    """
    include_variant = any(run.variant for run in runs)
    lines = [f"# {tool} Timing Summary: {dataset_name}", ""]

    if include_variant:
        lines.extend(
            [
                "| Variant | Run | Threads | Elapsed | Elapsed (s) | Exit status | Timing log |",
                "| --- | --- | ---: | --- | ---: | ---: | --- |",
            ]
        )
    else:
        lines.extend(
            [
                "| Run | Threads | Elapsed | Elapsed (s) | Exit status | Timing log |",
                "| --- | ---: | --- | ---: | ---: | --- |",
            ]
        )

    for run in runs:
        rel_log = run.timing_log.relative_to(RESULTS_ROOT)
        if include_variant:
            lines.append(
                "| "
                f"{run.variant or 'default'} | "
                f"{run.run_label} | "
                f"{run.threads} | "
                f"{run.elapsed} | "
                f"{format_seconds(run.elapsed_seconds)} | "
                f"{run.exit_status} | "
                f"`{rel_log}` |"
            )
        else:
            lines.append(
                "| "
                f"{run.run_label} | "
                f"{run.threads} | "
                f"{run.elapsed} | "
                f"{format_seconds(run.elapsed_seconds)} | "
                f"{run.exit_status} | "
                f"`{rel_log}` |"
            )

    lines.extend(
        [
            "",
            "Notes:",
            "- The standard dataset-wide `timing_summary.md` is still generated unchanged.",
            "- Multithread studies can be stored under `threads/<run-label>/logs/timing.log`.",
            "- `Threads` is inferred from `execution.log` when available, otherwise from the run label.",
        ]
    )
    return "\n".join(lines) + "\n"


def collect_tool_run(tool: str, variant: str | None, run_dir: Path, timing_log: Path) -> ToolTimingRun:
    """
    Parse one timing.log entry for a tool-specific summary.
    """
    parsed = parse_timing_log(timing_log, tool)
    run_label = run_dir.name if run_dir.parent.name == "threads" else "default"
    return ToolTimingRun(
        tool=tool,
        variant=variant,
        run_label=run_label,
        threads=infer_threads(run_dir, timing_log),
        elapsed=parsed.elapsed,
        elapsed_seconds=parsed.elapsed_seconds,
        exit_status=parsed.exit_status,
        timing_log=timing_log,
    )


def discover_tool_runs(tool: str, base_dir: Path, variants: tuple[str, ...]) -> list[ToolTimingRun]:
    """
    Discover standard and multithread timing runs for one tool.
    """
    runs: list[ToolTimingRun] = []
    candidate_dirs = [(base_dir, None)] if not variants else [(base_dir / variant, variant) for variant in variants]

    for run_root, variant in candidate_dirs:
        timing_log = run_root / "logs" / "timing.log"
        if timing_log.exists():
            runs.append(collect_tool_run(tool, variant, run_root, timing_log))

        threads_dir = run_root / "threads"
        if not threads_dir.exists():
            continue

        for thread_run_dir in sorted(path for path in threads_dir.iterdir() if path.is_dir()):
            thread_timing_log = thread_run_dir / "logs" / "timing.log"
            if thread_timing_log.exists():
                runs.append(collect_tool_run(tool, variant, thread_run_dir, thread_timing_log))

    return sorted(
        runs,
        key=lambda run: (
            run.variant or "",
            0 if run.threads.isdigit() else 1,
            int(run.threads) if run.threads.isdigit() else run.threads,
            run.run_label,
        ),
    )


def discover_lcpan_tool_runs(dataset_name: str, base_dir: Path, variants: tuple[str, ...]) -> list[ToolTimingRun]:
    """
    Discover LCPan timing runs across both legacy and variant-specific layouts.
    """
    dataset_dir = RESULTS_ROOT / dataset_name
    runs: list[ToolTimingRun] = []

    for variant in variants:
        candidate_log = next(
            (
                dataset_dir / relative_path
                for relative_path in LCPAN_TOOL_SUMMARY_CANDIDATES[variant]
                if (dataset_dir / relative_path).exists()
            ),
            None,
        )
        if candidate_log is not None:
            runs.append(collect_tool_run("LCPan", variant, candidate_log.parents[1], candidate_log))

        variant_dir = base_dir / variant
        threads_dir = variant_dir / "threads"
        if not threads_dir.exists():
            continue

        for thread_run_dir in sorted(path for path in threads_dir.iterdir() if path.is_dir()):
            thread_timing_log = thread_run_dir / "logs" / "timing.log"
            if thread_timing_log.exists():
                runs.append(collect_tool_run("LCPan", variant, thread_run_dir, thread_timing_log))

    return sorted(
        runs,
        key=lambda run: (
            run.variant or "",
            0 if run.threads.isdigit() else 1,
            int(run.threads) if run.threads.isdigit() else run.threads,
            run.run_label,
        ),
    )


def write_tool_timing_summaries(dataset_name: str) -> list[Path]:
    """
    Write additional timing summaries specific to PGGB, Minigraph, and LCPan.
    """
    dataset_dir = RESULTS_ROOT / dataset_name
    written_paths: list[Path] = []

    for tool, filename, subdir, variants in TOOL_TIMING_SUMMARY_CONFIG:
        if tool == "LCPan":
            runs = discover_lcpan_tool_runs(dataset_name, dataset_dir / subdir, variants)
        else:
            runs = discover_tool_runs(tool, dataset_dir / subdir, variants)
        if not runs:
            continue

        output_path = dataset_dir / filename
        output_path.write_text(build_tool_timing_table(dataset_name, tool, runs))
        written_paths.append(output_path)

    return written_paths


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
    for tool_output_path in write_tool_timing_summaries(dataset_name):
        print(tool_output_path)


if __name__ == "__main__":
    main()
