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


# ---------------------------------------------------------------------------
# Shared results-layout knowledge.
#
# Both summarizers (timing and output graphs) need the same view of "which
# tools exist, in which order" and "where each tool writes its artifacts".
# Keeping it here is the single source of truth so the two scripts cannot drift.
# ---------------------------------------------------------------------------

# Order used to render standalone tools in the dataset-wide summaries.
STANDARD_TOOL_ORDER = [
    "PGGB",
    "Minigraph",
    "MinigraphCactus",
    "MC_vg",
    "Cactus",
    "ProgressiveCactus",
    "POASTA",
    "Theseus",
]

# LCPan is expanded into these variants by input source and graph mode.
LCPAN_VARIANTS = ("pggb_vg", "pggb_vgx", "from_MC_vg", "from_MC_vgx")

# Derived single-encoding views excluded from canonical graph discovery.
EXCLUDED_GRAPH_SUFFIXES = (
    "_with_plines.gfa",
    "_with_wlines.gfa",
)

# Candidate timing.log paths per LCPan variant, relative to results/<DATASET>.
# Supports both the normalized layout and the legacy experiment directories.
LCPAN_TIMING_CANDIDATES = {
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

# Candidate canonical GFA paths per LCPan variant, relative to results/<DATASET>.
LCPAN_GRAPH_CANDIDATES = {
    "pggb_vg": (
        "LCPan/pggb_vg/outputs/lcpan_{dataset_short}.gfa",
        "LCPan/outputs/lcpan_{dataset_short}.gfa",
    ),
    "pggb_vgx": (
        "LCPan/pggb_vgx/outputs/lcpan_{dataset_short}.gfa",
        "LCPan/outputs_vgx/lcpan_{dataset_short}.gfa",
    ),
    "from_MC_vg": (
        "LCPan/mc_vg/outputs/lcpan_{dataset_short}.gfa",
        "LCPan/mc_vg/outputs/lcpan_from_cactus.gfa",
        "LCPan/cactus_vcf_test/outputs_vg/lcpan_from_cactus.gfa",
    ),
    "from_MC_vgx": (
        "LCPan/mc_vgx/outputs/lcpan_{dataset_short}.gfa",
        "LCPan/mc_vgx/outputs/lcpan_from_cactus.gfa",
        "LCPan/cactus_vcf_test/outputs_vgx/lcpan_from_cactus.gfa",
    ),
}

# Tools whose timing.log lives at a non-default relative path.
TOOL_TIMING_LOG_CANDIDATES = {
    "MC_vg": (
        "MC_vg/logs/timing.log",
        "MC_vg/logs/timing_cactus_pangenome.log",
    ),
}

# Canonical top-level GFA patterns per standalone tool, relative to
# results/<DATASET>/<TOOL>. {dataset_short} is filled per dataset.
CANONICAL_GRAPH_PATTERNS = {
    "PGGB": ("outputs/pggb_{dataset_short}.gfa",),
    "Minigraph": ("outputs/minigraph_{dataset_short}.gfa",),
    "MinigraphCactus": (
        "outputs/minigraphcactus_{dataset_short}.gfa",
        "outputs/minigraphcactus_graph.gfa",
    ),
    "MC_vg": ("outputs/result_cactus_new.gfa",),
    "Cactus": (
        "outputs/cactus_{dataset_short}.gfa",
        "outputs/cactus_alignment.gfa",
    ),
    "ProgressiveCactus": ("outputs/progressivecactus_{dataset_short}.gfa",),
    "POASTA": ("outputs/poasta_{dataset_short}.gfa",),
    "Theseus": ("outputs/theseus_{dataset_short}.gfa",),
    "LCPan": ("outputs/lcpan_{dataset_short}.gfa",),
}


def first_existing(base_dir: Path, relative_candidates: tuple[str, ...]) -> Path | None:
    """
    Return the first candidate path under base_dir that exists, or None.
    """
    for relative_path in relative_candidates:
        candidate = base_dir / relative_path
        if candidate.exists():
            return candidate
    return None


# ---------------------------------------------------------------------------
# Shared seqfile-generation helpers.
#
# Both seqfile generators (Cactus and Minigraph-Cactus) discover the same FASTA
# inputs, derive sample names the same way, and map host paths into containers
# the same way. Keeping these here is the single source of truth so the two
# scripts cannot drift (they previously held near-identical private copies that
# had already diverged).
# ---------------------------------------------------------------------------

# FASTA suffixes treated as per-sample assemblies.
VALID_FASTA_SUFFIXES = {".fa", ".fasta", ".fna"}

# Non-FASTA sidecar suffixes to skip outright.
IGNORED_FASTA_SIDECAR_SUFFIXES = {".fai"}

# Safety net for aggregate/helper FASTA files that must never be treated as
# per-sample assemblies. The input-layout convention keeps these under
# AUXILIARY_INPUTS/, so ASSEMBLIES/ is expected to be clean; this suffix filter
# only guards against a helper file accidentally left in ASSEMBLIES/.
NON_ASSEMBLY_STEM_SUFFIXES = ("_total", "_total_pansn", "_queries", "_reference")


def find_fasta_files(assemblies_dir: Path) -> list[Path]:
    """
    Return sorted per-sample FASTA files from one assemblies directory.

    Relies on the input-layout convention (per-sample assemblies in ASSEMBLIES/,
    aggregates/helpers in AUXILIARY_INPUTS/). The stem-suffix filter is only a
    safety net against helper files accidentally left in ASSEMBLIES/.
    """
    fasta_files: list[Path] = []
    for path in sorted(assemblies_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix in IGNORED_FASTA_SIDECAR_SUFFIXES:
            continue
        if path.stem.lower().endswith(NON_ASSEMBLY_STEM_SUFFIXES):
            continue
        if path.suffix.lower() in VALID_FASTA_SUFFIXES:
            fasta_files.append(path)
    return fasta_files


def normalize_sample_name(fasta_path: Path, rewrites: dict[str, str] | None = None) -> str:
    """
    Derive a stable sample name from a FASTA filename.

    ``rewrites`` is an ordered mapping of literal substring replacements applied
    to the filename stem, sourced per dataset from
    ``META/dataset_info.yml`` under ``seqfile.sample_name_rewrites``. When it is
    empty or None the stem is used unchanged, so the code holds no dataset-
    specific knowledge of its own.
    """
    sample_name = fasta_path.stem
    for old, new in (rewrites or {}).items():
        sample_name = sample_name.replace(old, new)
    return sample_name


def to_container_path(repo_root: Path, host_path: Path) -> str:
    """
    Convert one host path under input_data/ to the path visible in containers.
    """
    input_root = repo_root / "input_data"
    relative_path = host_path.relative_to(input_root)
    return f"/input_data/{relative_path.as_posix()}"


def get_sample_name_rewrites(repo_root: Path, dataset_name: str) -> dict[str, str]:
    """
    Read ``seqfile.sample_name_rewrites`` from one dataset's metadata.

    Returns an empty dict when the dataset declares no rewrites, so datasets
    that follow a clean naming convention need no metadata at all.
    """
    from utils.dataset_metadata import get_metadata_value, load_dataset_metadata_dict

    metadata = load_dataset_metadata_dict(repo_root / "input_data" / dataset_name)
    rewrites = get_metadata_value(metadata, "seqfile.sample_name_rewrites")
    if isinstance(rewrites, dict):
        return {str(key): str(value) for key, value in rewrites.items()}
    return {}


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
