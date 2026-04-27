"""
Normalize PGGB output layout for a dataset results directory.

PGGB writes many files into the output directory. This helper keeps a stable
top-level graph file named ``pggb_graph.gfa`` and moves the original PGGB
artifacts into an ``artifacts/`` subdirectory.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import shutil


CANONICAL_GRAPH_NAME = "pggb_graph.gfa"
ARTIFACTS_DIRNAME = "artifacts"


def find_final_graph(outputs_dir: Path) -> Path:
    """
    Return the unique PGGB final graph in the output directory.
    """
    matches = sorted(outputs_dir.glob("*.smooth.final.gfa"))
    if not matches:
        raise FileNotFoundError(f"no '*.smooth.final.gfa' file found in {outputs_dir}")
    if len(matches) > 1:
        raise RuntimeError(
            "multiple PGGB final graphs found; clean the directory or pick one manually: "
            + ", ".join(path.name for path in matches)
        )
    return matches[0]


def organize_outputs(outputs_dir: Path) -> tuple[Path, Path]:
    """
    Move raw PGGB artifacts into artifacts/ and create a stable top-level GFA.
    """
    if not outputs_dir.exists() or not outputs_dir.is_dir():
        raise FileNotFoundError(f"output directory not found: {outputs_dir}")

    final_graph = find_final_graph(outputs_dir)
    artifacts_dir = outputs_dir / ARTIFACTS_DIRNAME
    artifacts_dir.mkdir(exist_ok=True)

    canonical_graph = outputs_dir / CANONICAL_GRAPH_NAME
    if canonical_graph.exists():
        canonical_graph.unlink()

    for path in list(outputs_dir.iterdir()):
        if path.name in {ARTIFACTS_DIRNAME, CANONICAL_GRAPH_NAME}:
            continue
        shutil.move(str(path), artifacts_dir / path.name)

    shutil.copy2(artifacts_dir / final_graph.name, canonical_graph)
    return canonical_graph, artifacts_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Keep PGGB final graph at top level and move other outputs to artifacts/."
    )
    parser.add_argument("outputs_dir", help="PGGB outputs directory to normalize")
    args = parser.parse_args()

    outputs_dir = Path(args.outputs_dir)
    canonical_graph, artifacts_dir = organize_outputs(outputs_dir)

    print(f"Canonical graph: {canonical_graph}")
    print(f"Artifacts dir: {artifacts_dir}")


if __name__ == "__main__":
    main()
