"""
Lightweight helpers for reading optional dataset metadata overrides.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


def load_dataset_metadata_dict(dataset_path: Path) -> Dict[str, Any]:
    """
    Load a dataset's config and return a dictionary, or {} on any failure.

    The path is resolved by resolve_metadata_path: the version-controlled
    config/datasets/<DS>.yml when present, else the legacy META/dataset_info.yml.
    """
    try:
        from utils.dataset_common import resolve_metadata_path
    except ModuleNotFoundError:
        from dataset_common import resolve_metadata_path

    metadata_path = resolve_metadata_path(dataset_path)
    if not metadata_path.exists() or not metadata_path.is_file():
        return {}

    try:
        with metadata_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except yaml.YAMLError:
        return {}

    return data if isinstance(data, dict) else {}


def infer_dataset_short_from_name(dataset_name: str) -> str:
    """
    Convert one dataset directory name like MHC_TEST into its legacy short token.
    """
    if dataset_name.endswith("_TEST"):
        return dataset_name[: -len("_TEST")]
    return dataset_name


def get_metadata_value(metadata: Dict[str, Any], dotted_key: str) -> Any:
    """
    Read one nested metadata value using a dotted path like lcpan.reference_fasta.
    """
    current: Any = metadata
    for key in dotted_key.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def get_dataset_short_name(dataset_path: Path) -> str:
    """
    Return the dataset short token, preferring the optional metadata override.
    """
    metadata = load_dataset_metadata_dict(dataset_path)
    override = get_metadata_value(metadata, "dataset_short")
    if isinstance(override, str) and override.strip():
        return override.strip()
    return infer_dataset_short_from_name(dataset_path.name)
