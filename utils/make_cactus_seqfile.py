"""
Generate a Cactus seqfile from one dataset assemblies directory.

The Cactus seqfile format is:
    1) a Newick tree on the first line
    2) one mapping per line: SAMPLE_NAME <tab> /input_data/.../assembly.fa

This helper builds a deterministic binary tree from all assemblies in the dataset.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import re


VALID_FASTA_SUFFIXES = {".fa", ".fasta", ".fna"}
IGNORED_SUFFIXES = {".fai"}
IGNORED_STEMS = {
    "c4_total",
    "mhc_total",
    "kir_total",
    "monkeypox_100_seq",
    "salmonella_total",
    "salmonella_total_pansn",
}
IGNORED_STEM_SUFFIXES = ("_total", "_total_pansn", "_queries", "_reference")
SANITIZED_DIRNAME = "ASSEMBLIES_CACTUS_SANITIZED"


def normalize_sample_name(fasta_path: Path) -> str:
    """
    Convert one FASTA filename into a stable Cactus sample name.
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


def to_container_path(repo_root: Path, host_path: Path) -> str:
    """
    Convert one host path under input_data/ to the path visible in containers.
    """
    input_root = repo_root / "input_data"
    relative_path = host_path.relative_to(input_root)
    return f"/input_data/{relative_path.as_posix()}"


def sanitize_header_token(raw_token: str) -> str:
    """
    Convert one FASTA header token to a Cactus-compatible identifier.
    """
    token = raw_token
    if token.startswith("id=") and "|" in token:
        token = token.split("|", 1)[1]
    token = re.sub(r"[^A-Za-z0-9_.:-]", "_", token)
    return token


def sanitize_fasta_headers(source_fasta: Path, target_fasta: Path) -> None:
    """
    Rewrite FASTA headers to a Cactus-safe form.
    """
    seen_headers: set[str] = set()
    with source_fasta.open("r", encoding="utf-8") as src, target_fasta.open(
        "w", encoding="utf-8"
    ) as dst:
        for line in src:
            if not line.startswith(">"):
                dst.write(line)
                continue

            header = line[1:].strip()
            first_token = header.split()[0] if header else ""
            sanitized = sanitize_header_token(first_token)

            if not sanitized:
                raise RuntimeError(f"empty FASTA header after sanitization in {source_fasta}")
            if sanitized in seen_headers:
                raise RuntimeError(
                    f"duplicate sanitized FASTA header '{sanitized}' in {source_fasta}"
                )
            seen_headers.add(sanitized)
            dst.write(f">{sanitized}\n")


def prepare_sanitized_assemblies(
    repo_root: Path, dataset_name: str, fasta_files: list[Path]
) -> dict[Path, Path]:
    """
    Build/update ASSEMBLIES_CACTUS_SANITIZED and return source->sanitized paths.
    """
    sanitized_dir = repo_root / "input_data" / dataset_name / SANITIZED_DIRNAME
    sanitized_dir.mkdir(parents=True, exist_ok=True)

    path_map: dict[Path, Path] = {}
    for source_fasta in fasta_files:
        target_fasta = sanitized_dir / source_fasta.name
        sanitize_fasta_headers(source_fasta, target_fasta)
        path_map[source_fasta] = target_fasta

    return path_map


def _build_binary_subtree(sample_names: list[str], include_length: bool = True) -> str:
    """
    Recursively build a strictly binary Newick subtree.
    """
    if len(sample_names) == 1:
        return f"{sample_names[0]}:1.0"

    middle = len(sample_names) // 2
    left = _build_binary_subtree(sample_names[:middle], include_length=True)
    right = _build_binary_subtree(sample_names[middle:], include_length=True)
    subtree = f"({left},{right})"
    if include_length:
        return f"{subtree}:1.0"
    return subtree


def build_binary_tree(sample_names: list[str]) -> str:
    """
    Build a strictly binary Newick tree with uniform branch lengths.
    """
    # Leave the top-level root unlengthed to avoid an implicit extra root node.
    return f"{_build_binary_subtree(sample_names, include_length=False)};"


def build_seqfile_lines(repo_root: Path, dataset_name: str) -> list[str]:
    """
    Build Cactus seqfile lines for one dataset.
    """
    assemblies_dir = repo_root / "input_data" / dataset_name / "ASSEMBLIES"
    if not assemblies_dir.is_dir():
        raise FileNotFoundError(f"assemblies directory not found: {assemblies_dir}")

    fasta_files = find_fasta_files(assemblies_dir)
    if len(fasta_files) < 2:
        raise FileNotFoundError(
            f"at least two FASTA files are required in {assemblies_dir}, found {len(fasta_files)}"
        )

    sanitized_paths = prepare_sanitized_assemblies(repo_root, dataset_name, fasta_files)

    seen_names: set[str] = set()
    sample_names: list[str] = []
    lines: list[str] = []

    for fasta_path in fasta_files:
        sample_name = normalize_sample_name(fasta_path)
        if sample_name in seen_names:
            raise RuntimeError(f"duplicate sample name after normalization: {sample_name}")
        seen_names.add(sample_name)
        sample_names.append(sample_name)
        lines.append(f"{sample_name}\t{to_container_path(repo_root, sanitized_paths[fasta_path])}")

    tree_line = build_binary_tree(sample_names)
    return [tree_line, *lines]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Cactus seqfile for one dataset."
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
            "(default: results/<dataset>/Cactus/outputs/<dataset>_seqfile.txt)"
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
            / "Cactus"
            / "outputs"
            / f"{dataset_name.lower()}_seqfile.txt"
        )

    lines = build_seqfile_lines(repo_root, dataset_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except PermissionError as error:
        raise SystemExit(
            "Permission denied while writing seqfile. "
            "If this directory was written by Docker as root, run: "
            f"sudo chown -R $USER:$USER {output_path.parent}"
        ) from error

    print(f"Seqfile: {output_path}")
    print(f"Samples: {len(lines) - 1}")


if __name__ == "__main__":
    main()
