"""
Build a compact Markdown summary table from canonical graph outputs.
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
    "Cactus",
    "ProgressiveCactus",
]

LCPAN_GRAPH_CANDIDATES = {
    "LCPan_PGGB_vg": (
        "LCPan/pggb_vg/outputs/lcpan_{dataset_short}.gfa",
        "LCPan/outputs/lcpan_{dataset_short}.gfa",
    ),
    "LCPan_PGGB_vgx": (
        "LCPan/pggb_vgx/outputs/lcpan_{dataset_short}.gfa",
        "LCPan/outputs_vgx/lcpan_{dataset_short}.gfa",
    ),
    "LCPan_MC_vg": (
        "LCPan/mc_vg/outputs/lcpan_{dataset_short}.gfa",
        "LCPan/cactus_vcf_test/outputs_vg/lcpan_from_cactus.gfa",
    ),
    "LCPan_MC_vgx": (
        "LCPan/mc_vgx/outputs/lcpan_{dataset_short}.gfa",
        "LCPan/cactus_vcf_test/outputs_vgx/lcpan_from_cactus.gfa",
    ),
}

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = REPO_ROOT / "results"

CANONICAL_GRAPH_PATTERNS = {
    "PGGB": ("outputs/pggb_{dataset_short}.gfa",),
    "Minigraph": ("outputs/minigraph_{dataset_short}.gfa",),
    "MinigraphCactus": (
        "outputs/minigraphcactus_{dataset_short}.gfa",
        "outputs/minigraphcactus_graph.gfa",
    ),
    "Cactus": (
        "outputs/cactus_{dataset_short}.gfa",
        "outputs/cactus_alignment.gfa",
    ),
    "ProgressiveCactus": ("outputs/progressivecactus_{dataset_short}.gfa",),
    "LCPan": ("outputs/lcpan_{dataset_short}.gfa",),
}

EXCLUDED_SUFFIXES = (
    "_with_plines.gfa",
    "_with_wlines.gfa",
)


@dataclass(frozen=True)
class GraphSummary:
    tool: str
    graph_path: Path
    file_size_bytes: int
    s_count: int
    l_count: int
    p_count: int
    w_count: int


def sanitize_dataset_name(value: str) -> str:
    """
    Allow only standard dataset tokens.
    """
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError(f"invalid dataset name: {value}")
    return value


def format_size_bytes(value: int) -> str:
    """
    Keep the main size column simple and exact.
    """
    return str(value)


def dataset_short_name(dataset_dir: Path) -> str:
    """
    Convert a dataset directory name like MHC_TEST into MHC.
    """
    return re.sub(r"_TEST$", "", dataset_dir.name)


def find_canonical_graph(dataset_dir: Path, tool: str) -> Path | None:
    """
    Return the canonical top-level GFA for one tool, excluding derived variants.
    Prefer dataset-specific renamed outputs when both renamed and legacy files exist.
    """
    patterns = CANONICAL_GRAPH_PATTERNS[tool]
    dataset_short = dataset_short_name(dataset_dir)

    empty_match: Path | None = None

    for pattern in patterns:
        resolved_pattern = pattern.format(dataset_short=dataset_short)
        matches = sorted(
            path
            for path in (dataset_dir / tool).glob(resolved_pattern)
            if not any(path.name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES)
        )

        if not matches:
            continue

        if len(matches) > 1:
            raise RuntimeError(
                f"multiple canonical graph candidates found for {tool}: "
                + ", ".join(path.name for path in matches)
            )

        match = matches[0]
        if match.stat().st_size > 0:
            return match
        if empty_match is None:
            empty_match = match

    return empty_match


def find_lcpan_variant_graph(dataset_dir: Path, tool: str) -> Path | None:
    """
    Return one explicit LCPan variant graph, supporting both normalized and
    legacy experiment directory layouts.
    """
    dataset_short = dataset_short_name(dataset_dir)

    for pattern in LCPAN_GRAPH_CANDIDATES[tool]:
        candidate = dataset_dir / pattern.format(dataset_short=dataset_short)
        if candidate.exists() and not any(
            candidate.name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES
        ):
            return candidate

    return None


def count_gfa_records(graph_path: Path) -> tuple[int, int, int, int]:
    """
    Count S/L/P/W records in one GFA file.
    """
    s_count = 0
    l_count = 0
    p_count = 0
    w_count = 0

    with graph_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("S\t"):
                s_count += 1
            elif line.startswith("L\t"):
                l_count += 1
            elif line.startswith("P\t"):
                p_count += 1
            elif line.startswith("W\t"):
                w_count += 1

    return s_count, l_count, p_count, w_count


def summarize_graph(tool: str, graph_path: Path) -> GraphSummary:
    """
    Collect the structural summary for one canonical graph.
    """
    s_count, l_count, p_count, w_count = count_gfa_records(graph_path)
    return GraphSummary(
        tool=tool,
        graph_path=graph_path,
        file_size_bytes=graph_path.stat().st_size,
        s_count=s_count,
        l_count=l_count,
        p_count=p_count,
        w_count=w_count,
    )


def discover_summaries(dataset_name: str) -> list[GraphSummary]:
    """
    Collect graph summaries for the standard tool directories in one dataset.
    LCPan runs are expanded into explicit input/mode variants when present.
    """
    dataset_dir = RESULTS_ROOT / dataset_name
    summaries: list[GraphSummary] = []

    for tool in STANDARD_TOOL_ORDER:
        graph_path = find_canonical_graph(dataset_dir, tool)
        if graph_path is None:
            continue
        summaries.append(summarize_graph(tool, graph_path))

    for tool in LCPAN_GRAPH_CANDIDATES:
        graph_path = find_lcpan_variant_graph(dataset_dir, tool)
        if graph_path is None:
            continue
        summaries.append(summarize_graph(tool, graph_path))

    if not summaries:
        raise FileNotFoundError(f"no canonical GFA outputs found under {dataset_dir}")

    return summaries


def build_table(dataset_name: str, summaries: list[GraphSummary]) -> str:
    """
    Render one Markdown output-summary table.
    """
    lines = [
        f"# Output Summary: {dataset_name}",
        "",
        "| Tool | Graph file | Size (bytes) | S | L | P | W |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    for summary in summaries:
        rel_graph = summary.graph_path.relative_to(RESULTS_ROOT)
        lines.append(
            "| "
            f"{summary.tool} | "
            f"`{rel_graph}` | "
            f"{format_size_bytes(summary.file_size_bytes)} | "
            f"{summary.s_count} | "
            f"{summary.l_count} | "
            f"{summary.p_count} | "
            f"{summary.w_count} |"
        )

    lines.extend(
        [
            "",
            "Notes:",
            "- Counts are computed from the canonical top-level GFA for each tool.",
            "- Derived `_with_plines.gfa` and `_with_wlines.gfa` files are excluded.",
            "- LCPan rows are expanded by input source and mode when matching runs are present.",
            "- File paths used for the summaries live under `results/<DATASET>/...`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize canonical GFA outputs into a Markdown table."
    )
    parser.add_argument("dataset_name", help="Dataset under results/, for example C4_TEST")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional explicit output path (default: results/<DATASET>/output_summary.md)",
    )
    args = parser.parse_args()

    dataset_name = sanitize_dataset_name(args.dataset_name)
    summaries = discover_summaries(dataset_name)
    dataset_dir = RESULTS_ROOT / dataset_name
    output_path = Path(args.output) if args.output else dataset_dir / "output_summary.md"

    output_path.write_text(build_table(dataset_name, summaries))
    print(output_path)


if __name__ == "__main__":
    main()
