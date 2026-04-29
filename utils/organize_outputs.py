"""
Normalize output layout for supported pangenome workflows.

The helper keeps a stable top-level primary output file for each tool and moves
original workflow artifacts into an artifacts/ subdirectory.

Supported tools:
  - Cactus
  - LCPan
  - Minigraph
  - PGGB
  - MinigraphCactus
  - ProgressiveCactus
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import gzip
import shutil


ARTIFACTS_DIRNAME = "artifacts"


@dataclass(frozen=True)
class ToolOutputSpec:
    tool_name: str
    final_output_pattern: str
    canonical_uncompressed_suffix: str
    exclude_suffixes: tuple[str, ...] = ()
    compressed: bool = False
    canonical_compressed_suffix: str | None = None


TOOL_SPECS = {
    "Cactus": ToolOutputSpec(
        tool_name="Cactus",
        final_output_pattern="*.hal",
        canonical_uncompressed_suffix=".hal",
        compressed=False,
    ),
    "LCPan": ToolOutputSpec(
        tool_name="LCPan",
        final_output_pattern="*.gfa",
        canonical_uncompressed_suffix=".gfa",
        compressed=False,
    ),
    "Minigraph": ToolOutputSpec(
        tool_name="Minigraph",
        final_output_pattern="*.gfa",
        canonical_uncompressed_suffix=".gfa",
        compressed=False,
    ),
    "PGGB": ToolOutputSpec(
        tool_name="PGGB",
        final_output_pattern="*.smooth.final.gfa",
        canonical_uncompressed_suffix=".gfa",
        compressed=False,
    ),
    "MinigraphCactus": ToolOutputSpec(
        tool_name="MinigraphCactus",
        final_output_pattern="*.gfa.gz",
        canonical_uncompressed_suffix=".gfa",
        canonical_compressed_suffix=".gfa.gz",
        exclude_suffixes=(".sv.gfa.gz",),
        compressed=True,
    ),
    "ProgressiveCactus": ToolOutputSpec(
        tool_name="ProgressiveCactus",
        final_output_pattern="*.hal",
        canonical_uncompressed_suffix=".hal",
        compressed=False,
    ),
}


def infer_dataset_name(outputs_dir: Path) -> str:
    """
    Infer the dataset name from results/<dataset>/<tool>/outputs.
    """
    try:
        dataset_name = outputs_dir.resolve().parents[1].name
    except IndexError as error:
        raise RuntimeError(
            f"unable to infer dataset name from output directory: {outputs_dir}"
        ) from error

    if not dataset_name:
        raise RuntimeError(f"empty dataset name inferred from output directory: {outputs_dir}")

    return dataset_name


def infer_dataset_short(dataset_name: str) -> str:
    """
    Convert one dataset name into its canonical short token.
    """
    if dataset_name.endswith("_TEST"):
        return dataset_name[: -len("_TEST")]
    return dataset_name


def build_canonical_names(
    spec: ToolOutputSpec,
    dataset_short: str,
) -> tuple[str, str | None]:
    """
    Build canonical output filenames for one tool and dataset token.
    """
    base_name = f"{spec.tool_name.lower()}_{dataset_short}"
    canonical_output_name = f"{base_name}{spec.canonical_uncompressed_suffix}"

    canonical_output_gz_name = None
    if spec.canonical_compressed_suffix is not None:
        canonical_output_gz_name = f"{base_name}{spec.canonical_compressed_suffix}"

    return canonical_output_name, canonical_output_gz_name


def find_final_output(outputs_dir: Path, spec: ToolOutputSpec) -> Path:
    """
    Return the unique final output for the selected tool.
    """
    matches = sorted(
        path
        for path in outputs_dir.glob(spec.final_output_pattern)
        if not any(path.name.endswith(suffix) for suffix in spec.exclude_suffixes)
    )

    if not matches:
        raise FileNotFoundError(
            f"no final output matching '{spec.final_output_pattern}' found in {outputs_dir}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"multiple {spec.tool_name} final outputs found; "
            "clean the directory or pick one manually: "
            + ", ".join(path.name for path in matches)
        )

    return matches[0]


def write_decompressed_copy(source_gz: Path, target_gfa: Path) -> None:
    """
    Write an uncompressed GFA copy from a gzip-compressed source graph.
    """
    with gzip.open(source_gz, "rb") as src, target_gfa.open("wb") as dst:
        shutil.copyfileobj(src, dst)


def reset_artifacts_dir(outputs_dir: Path) -> Path:
    """
    Recreate artifacts/ from scratch.
    """
    artifacts_dir = outputs_dir / ARTIFACTS_DIRNAME

    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)

    artifacts_dir.mkdir()
    return artifacts_dir


def remove_existing_canonical_files(
    outputs_dir: Path,
    canonical_output_name: str,
    canonical_output_gz_name: str | None,
    preserve_names: set[str] | None = None,
) -> None:
    """
    Remove previously normalized top-level output files.
    """
    preserve_names = preserve_names or set()
    canonical_paths = [outputs_dir / canonical_output_name]

    if canonical_output_gz_name is not None:
        canonical_paths.append(outputs_dir / canonical_output_gz_name)

    for path in canonical_paths:
        if path.name in preserve_names:
            continue
        if path.exists():
            path.unlink()


def move_raw_artifacts(
    outputs_dir: Path,
    canonical_output_name: str,
    canonical_output_gz_name: str | None,
    artifacts_dir: Path,
) -> None:
    """
    Move original workflow artifacts into artifacts/.
    """
    protected_names = {
        ARTIFACTS_DIRNAME,
        canonical_output_name,
    }

    if canonical_output_gz_name is not None:
        protected_names.add(canonical_output_gz_name)

    for path in list(outputs_dir.iterdir()):
        if path.name in protected_names:
            continue
        shutil.move(str(path), artifacts_dir / path.name)


def organize_outputs(
    tool: str,
    outputs_dir: Path,
    dataset_short: str | None = None,
) -> list[Path]:
    """
    Normalize outputs for the selected workflow tool.
    """
    if tool not in TOOL_SPECS:
        raise ValueError(
            f"unsupported tool '{tool}'. Supported tools: {', '.join(TOOL_SPECS)}"
        )

    if not outputs_dir.exists() or not outputs_dir.is_dir():
        raise FileNotFoundError(f"output directory not found: {outputs_dir}")

    spec = TOOL_SPECS[tool]
    dataset_name = infer_dataset_name(outputs_dir)
    resolved_dataset_short = dataset_short or infer_dataset_short(dataset_name)
    canonical_output_name, canonical_output_gz_name = build_canonical_names(
        spec,
        resolved_dataset_short,
    )

    final_output = find_final_output(outputs_dir, spec)
    artifacts_dir = reset_artifacts_dir(outputs_dir)
    remove_existing_canonical_files(
        outputs_dir,
        canonical_output_name,
        canonical_output_gz_name,
        preserve_names={final_output.name},
    )
    move_raw_artifacts(
        outputs_dir,
        canonical_output_name,
        canonical_output_gz_name,
        artifacts_dir,
    )

    moved_final_output = artifacts_dir / final_output.name
    source_final_output = moved_final_output if moved_final_output.exists() else final_output
    created_paths: list[Path] = []

    canonical_output = outputs_dir / canonical_output_name

    if spec.compressed:
        if canonical_output_gz_name is None:
            raise RuntimeError(f"{tool} is marked as compressed but has no canonical gz name")

        canonical_output_gz = outputs_dir / canonical_output_gz_name
        if source_final_output.resolve() != canonical_output_gz.resolve():
            shutil.copy2(source_final_output, canonical_output_gz)
        write_decompressed_copy(source_final_output, canonical_output)

        created_paths.extend([canonical_output, canonical_output_gz])
    else:
        if source_final_output.resolve() != canonical_output.resolve():
            shutil.copy2(source_final_output, canonical_output)
        created_paths.append(canonical_output)

    created_paths.append(artifacts_dir)
    return created_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize output layout for supported workflow tools."
    )
    parser.add_argument(
        "tool",
        choices=sorted(TOOL_SPECS),
        help="Tool whose outputs should be normalized",
    )
    parser.add_argument(
        "outputs_dir",
        help="Tool outputs directory to normalize",
    )
    parser.add_argument(
        "--dataset-short",
        default=None,
        help=(
            "Override the dataset short token used in canonical output names "
            "(default: infer from results/<dataset>/... and strip trailing _TEST)"
        ),
    )

    args = parser.parse_args()

    created_paths = organize_outputs(
        tool=args.tool,
        outputs_dir=Path(args.outputs_dir),
        dataset_short=args.dataset_short,
    )

    for path in created_paths:
        print(path)


if __name__ == "__main__":
    main()
