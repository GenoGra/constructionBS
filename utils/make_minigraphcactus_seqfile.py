"""
Generate a Minigraph-Cactus seqfile from one dataset assemblies directory.

The seqfile format is a tab-delimited mapping:
    SAMPLE_NAME <tab> /input_data/.../assembly.fa

Sample names are derived from FASTA filenames with small normalizations so the
reference names are easier to reuse on the command line.
"""

from __future__ import annotations

from pathlib import Path
import argparse


VALID_FASTA_SUFFIXES = {".fa", ".fasta", ".fna"}
IGNORED_SUFFIXES = {".fai"}
IGNORED_STEMS = {
    "c4_total",
    "mhc_total",
    "kir_total",
    "monkeypox_100_seq",
    "salmonella_total",
    "salmonella_total_pansn",
    "c4_queries",
    "c4_reference",
}
IGNORED_STEM_SUFFIXES = ("_total", "_total_pansn", "_queries", "_reference")
SANITIZED_DIRNAME = "ASSEMBLIES_CACTUS_SANITIZED"


def normalize_sample_name(fasta_path: Path) -> str:
    """
    Convert one FASTA filename into a stable Minigraph-Cactus sample name.
    """
    sample_name = fasta_path.stem
    sample_name = sample_name.replace("00GRCh38", "GRCh38")
    sample_name = sample_name.replace("CHM13.0", "CHM13")
    return sample_name


def find_fasta_files(assemblies_dir: Path) -> list[Path]:
    """
    Return sorted FASTA files from the given assemblies directory.
    """
    fasta_files: list[Path] = []
    for path in sorted(assemblies_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        stem = path.stem.lower()
        if stem in IGNORED_STEMS:
            continue
        if stem.endswith(IGNORED_STEM_SUFFIXES):
            continue
        if path.suffix.lower() in VALID_FASTA_SUFFIXES:
            fasta_files.append(path)
    return fasta_files


def resolve_assemblies_dir(repo_root: Path, dataset_name: str) -> Path:
    """
    Prefer ASSEMBLIES when it contains a usable set of FASTA files, otherwise
    fall back to ASSEMBLIES_CACTUS_SANITIZED.
    """
    assemblies_dir = repo_root / "input_data" / dataset_name / "ASSEMBLIES"
    if not assemblies_dir.is_dir():
        raise FileNotFoundError(f"assemblies directory not found: {assemblies_dir}")

    fasta_files = find_fasta_files(assemblies_dir)
    if len(fasta_files) >= 2:
        return assemblies_dir

    sanitized_dir = repo_root / "input_data" / dataset_name / SANITIZED_DIRNAME
    if sanitized_dir.is_dir() and len(find_fasta_files(sanitized_dir)) >= 2:
        return sanitized_dir

    return assemblies_dir


def to_container_path(repo_root: Path, host_path: Path) -> str:
    """
    Convert one host path under input_data/ to the path visible in containers.
    """
    input_root = repo_root / "input_data"
    relative_path = host_path.relative_to(input_root)
    return f"/input_data/{relative_path.as_posix()}"


def build_seqfile_lines(repo_root: Path, dataset_name: str) -> list[str]:
    """
    Build seqfile lines for one dataset.
    """
    assemblies_dir = resolve_assemblies_dir(repo_root, dataset_name)
    fasta_files = find_fasta_files(assemblies_dir)
    if not fasta_files:
        raise FileNotFoundError(f"no FASTA files found in {assemblies_dir}")

    seen_names: set[str] = set()
    lines: list[str] = []

    for fasta_path in fasta_files:
        sample_name = normalize_sample_name(fasta_path)
        if sample_name in seen_names:
            raise RuntimeError(f"duplicate sample name after normalization: {sample_name}")
        seen_names.add(sample_name)
        lines.append(f"{sample_name}\t{to_container_path(repo_root, fasta_path)}")

    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Minigraph-Cactus seqfile for one dataset."
    )
    parser.add_argument("dataset_name", help="Dataset name under input_data/")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root containing input_data/ (default: inferred from this script)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output seqfile path "
            "(default: results/<dataset>/MinigraphCactus/outputs/<dataset>_seqfile.txt)"
        ),
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    dataset_name = args.dataset_name

    output_path = args.output
    if output_path is None:
        output_path = (
            repo_root
            / "results"
            / dataset_name
            / "MinigraphCactus"
            / "outputs"
            / f"{dataset_name.lower()}_seqfile.txt"
        )

    lines = build_seqfile_lines(repo_root, dataset_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Seqfile: {output_path}")
    print(f"Samples: {len(lines)}")


if __name__ == "__main__":
    main()
