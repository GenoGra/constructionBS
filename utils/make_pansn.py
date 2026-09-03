"""
Build a PanSN-headered concatenated FASTA from one dataset's assemblies.

PanSN names each sequence ``SAMPLE#HAPLOTYPE#CONTIG``:
  - SAMPLE  : derived from the FASTA *filename* via the same
              ``normalize_sample_name`` used by the seqfile generators, so a
              given assembly gets the SAME sample name across all tools
              (Cactus, PGGB, POASTA, ...). It reuses ``seqfile.sample_name_rewrites``
              from META/dataset_info.yml, so no per-tool config drift.
  - HAPLOTYPE: 0 by default. Only when the dataset sets
              ``pansn.haplotype_from_suffix: true`` is a trailing ``.N`` split
              off the sample name and used as the haplotype. This is opt-in
              because a trailing ``.N`` is ambiguous (HG002.1 = haplotype, but
              GL000209.2 = accession version), so it must never be guessed.
  - CONTIG  : the ORIGINAL FASTA header token, unchanged. This keeps the tool
              agnostic to header format (NCBI, SPAdes NODE_..., plain) and
              handles multi-contig assemblies (one PanSN record per contig).

Deriving SAMPLE from the filename (not the header) is what makes this work on
non-human, multi-contig assemblies (e.g. a Salmonella genome with hundreds of
NODE_* contigs becomes ERS007564#0#NODE_1..., ERS007564#0#NODE_2..., all under
the one sample ERS007564), where header-based rules produce wrong or collapsed
sample names.

Runs on the HOST (plain Python): no awk, so no mawk-vs-gawk portability trap.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import re
import sys

try:
    from utils.dataset_common import find_fasta_files, get_sample_name_rewrites, normalize_sample_name
    from utils.dataset_metadata import get_metadata_value, load_dataset_metadata_dict
except ModuleNotFoundError:
    from dataset_common import find_fasta_files, get_sample_name_rewrites, normalize_sample_name
    from dataset_metadata import get_metadata_value, load_dataset_metadata_dict


_TRAILING_HAP = re.compile(r"^(.*)\.([0-9]+)$")


def split_haplotype(sample_name: str, enabled: bool) -> tuple[str, str]:
    """
    Split a trailing ``.N`` into (sample, haplotype) when ``enabled``.

    When disabled (the default), returns (sample_name, "0"): the whole name is
    the sample and the haplotype is 0. This is deliberately opt-in — a trailing
    ``.N`` cannot be safely assumed to be a haplotype.
    """
    if enabled:
        match = _TRAILING_HAP.match(sample_name)
        if match:
            return match.group(1), match.group(2)
    return sample_name, "0"


def first_header_token(header_line: str) -> str:
    """
    Return the first whitespace-delimited token of a FASTA header (no '>').
    """
    return header_line[1:].strip().split()[0] if header_line[1:].strip() else ""


def build_pansn(repo_root: Path, dataset_name: str, output_path: Path) -> tuple[int, int]:
    """
    Write the PanSN-headered concatenation. Returns (n_samples, n_sequences).
    """
    assemblies_dir = repo_root / "input_data" / dataset_name / "ASSEMBLIES"
    if not assemblies_dir.is_dir():
        raise FileNotFoundError(f"assemblies directory not found: {assemblies_dir}")

    fasta_files = find_fasta_files(assemblies_dir)
    if not fasta_files:
        raise FileNotFoundError(f"no FASTA files found in {assemblies_dir}")

    rewrites = get_sample_name_rewrites(repo_root, dataset_name)
    metadata = load_dataset_metadata_dict(repo_root / "input_data" / dataset_name)
    hap_from_suffix = bool(get_metadata_value(metadata, "pansn.haplotype_from_suffix"))

    n_samples = 0
    n_sequences = 0
    seen_pansn: set[str] = set()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out:
        for fasta_path in fasta_files:
            raw_sample = normalize_sample_name(fasta_path, rewrites)
            sample, haplotype = split_haplotype(raw_sample, hap_from_suffix)
            n_samples += 1

            with fasta_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith(">"):
                        contig = first_header_token(line)
                        if not contig:
                            raise RuntimeError(f"empty FASTA header in {fasta_path}")
                        pansn = f"{sample}#{haplotype}#{contig}"
                        if pansn in seen_pansn:
                            raise RuntimeError(f"duplicate PanSN name: {pansn}")
                        seen_pansn.add(pansn)
                        n_sequences += 1
                        out.write(f">{pansn}\n")
                    else:
                        out.write(line)

    return n_samples, n_sequences


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a PanSN-headered concatenated FASTA for one dataset."
    )
    parser.add_argument("dataset_name", help="Dataset name under input_data/")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root containing input_data/ (default: inferred).",
    )
    parser.add_argument("--output", type=Path, required=True, help="Output PanSN FASTA path.")
    args = parser.parse_args()

    n_samples, n_sequences = build_pansn(
        args.repo_root.resolve(), args.dataset_name, args.output
    )
    print(f"PanSN: {args.output}")
    print(f"Samples: {n_samples}")
    print(f"Sequences: {n_sequences}")


if __name__ == "__main__":
    main()
