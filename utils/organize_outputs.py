"""
Normalize output layout for supported pangenome workflows.

The helper keeps a stable top-level primary output file for each tool and moves
original workflow artifacts into an artifacts/ subdirectory.

Supported tools:
  - Cactus
  - PGGB
  - MinigraphCactus
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
    canonical_output_name: str
    exclude_suffixes: tuple[str, ...] = ()
    compressed: bool = False
    canonical_output_gz_name: str | None = None


TOOL_SPECS = {
    "Cactus": ToolOutputSpec(
        tool_name="Cactus",
        final_output_pattern="*.hal",
        canonical_output_name="cactus_alignment.hal",
        compressed=False,
    ),
    "PGGB": ToolOutputSpec(
        tool_name="PGGB",
        final_output_pattern="*.smooth.final.gfa",
        canonical_output_name="pggb_graph.gfa",
        compressed=False,
    ),
    "MinigraphCactus": ToolOutputSpec(
        tool_name="MinigraphCactus",
        final_output_pattern="*.gfa.gz",
        canonical_output_name="minigraphcactus_graph.gfa",
        canonical_output_gz_name="minigraphcactus_graph.gfa.gz",
        exclude_suffixes=(".sv.gfa.gz",),
        compressed=True,
    ),
}


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


def remove_existing_canonical_files(outputs_dir: Path, spec: ToolOutputSpec) -> None:
    """
    Remove previously normalized top-level output files.
    """
    canonical_paths = [outputs_dir / spec.canonical_output_name]

    if spec.canonical_output_gz_name is not None:
        canonical_paths.append(outputs_dir / spec.canonical_output_gz_name)

    for path in canonical_paths:
        if path.exists():
            path.unlink()


def move_raw_artifacts(outputs_dir: Path, spec: ToolOutputSpec, artifacts_dir: Path) -> None:
    """
    Move original workflow artifacts into artifacts/.
    """
    protected_names = {
        ARTIFACTS_DIRNAME,
        spec.canonical_output_name,
    }

    if spec.canonical_output_gz_name is not None:
        protected_names.add(spec.canonical_output_gz_name)

    for path in list(outputs_dir.iterdir()):
        if path.name in protected_names:
            continue
        shutil.move(str(path), artifacts_dir / path.name)


def organize_outputs(tool: str, outputs_dir: Path) -> list[Path]:
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

    final_output = find_final_output(outputs_dir, spec)
    artifacts_dir = reset_artifacts_dir(outputs_dir)
    remove_existing_canonical_files(outputs_dir, spec)
    move_raw_artifacts(outputs_dir, spec, artifacts_dir)

    moved_final_output = artifacts_dir / final_output.name
    created_paths: list[Path] = []

    canonical_output = outputs_dir / spec.canonical_output_name

    if spec.compressed:
        if spec.canonical_output_gz_name is None:
            raise RuntimeError(f"{tool} is marked as compressed but has no canonical gz name")

        canonical_output_gz = outputs_dir / spec.canonical_output_gz_name
        shutil.copy2(moved_final_output, canonical_output_gz)
        write_decompressed_copy(moved_final_output, canonical_output)

        created_paths.extend([canonical_output, canonical_output_gz])
    else:
        shutil.copy2(moved_final_output, canonical_output)
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

    args = parser.parse_args()

    created_paths = organize_outputs(
        tool=args.tool,
        outputs_dir=Path(args.outputs_dir),
    )

    for path in created_paths:
        print(path)


if __name__ == "__main__":
    main()
