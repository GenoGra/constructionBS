"""
Central configuration describing expected dataset file types, tool input
requirements, and the canonical repository root paths.
"""

from __future__ import annotations

import os
from pathlib import Path

from tool_registry import TOOL_INPUT_SPECS, TOOL_REQUIREMENTS


REPO_ROOT = Path(__file__).resolve().parent


def _root_from_env(env_var: str, default: Path) -> Path:
    """
    Resolve a repository root from an environment override or a default.
    """
    override = os.environ.get(env_var)
    return Path(override) if override else default


RESULTS_ROOT = _root_from_env("CONSTRUCTIONBS_RESULTS", REPO_ROOT / "results")
INPUT_DATA_ROOT = _root_from_env("CONSTRUCTIONBS_INPUT_DATA", REPO_ROOT / "input_data")


EXPECTED_FILE_TYPES = {
    "ASSEMBLIES": [".fa", ".fasta", ".fna"],
    "GRAPH": [".fa", ".fasta", ".fna", ".gfa", ".rgfa", ".vcf"],
}
