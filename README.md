# constructionBS

constructionBS is a toolkit for setting up and running bioinformatics pipelines for pangenome graph construction using containerized tools. It provides utilities to prepare datasets, generate Docker configurations, and manage execution environments for various graph construction tools.

## Overview

This repository contains Python scripts and configuration files to automate the setup of bioinformatics workflows for pangenome analysis. It supports multiple tools including Cactus, Minigraph, PGGB, and ProgressiveCactus, providing a standardized way to:

- Validate dataset structures and requirements
- Generate Dockerfiles for each tool
- Create docker-compose configurations for execution
- Manage results and logging directories

## Features

- **Dataset Validation**: Check if datasets are properly structured and contain required files
- **Automated Docker Setup**: Generate Dockerfiles and docker-compose files for supported tools
- **Results Management**: Create standardized directory structures for outputs and logs
- **Tool Compatibility**: Support for multiple pangenome graph construction tools
- **Configuration-Driven**: Easy to add new tools or modify existing configurations

## Supported Tools

- **Cactus**: Progressive alignment workflow (`HAL`-first, distinct from `cactus-pangenome`)
- **Minigraph**: Fast graph construction from assemblies
- **MinigraphCactus**: Hybrid approach combining Minigraph and Cactus
- **PGGB**: Pangenome Graph Builder
- **ProgressiveCactus**: Progressive alignment using Cactus

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Git

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd constructionBS
   ```

2. Install Python dependencies:
   ```bash
   pip install pyyaml
   ```

## Dataset Structure

Datasets should follow this directory structure:

```
dataset_name/
├── ASSEMBLIES/     # Assembly files (.fa, .fasta, .fna)
├── GRAPH/          # Graph files (.gfa, .rgfa)
├── META/           # Metadata files
│   └── dataset_info.yml
├── READS/          # Read files (.fa, .fasta, .fq, .fastq)
└── TREE/           # Tree files (.nwk, .newick)
```

### Metadata File (META/dataset_info.yml)

```yaml
status: "ready"  # or "placeholder"
description: "Dataset description"
expected_inputs:
  assemblies: true
  graph: true
  reads: false
  tree: false
supported_workflows:
  cactus: true
  minigraph: true
  minigraphcactus: true
  pggb: true
  lcpan: true
  progressivecactus: true
```

## Usage

### 1. Prepare Datasets

Place your datasets in the `input_data/` directory following the required structure.

### 2. Check Dataset Readiness

Use the `utils/check_inputs.py` script to validate your datasets:

```bash
python -m utils.check_inputs --dataset dataset_name
# or inspect everything under the default input_data/ directory
python -m utils.check_inputs
# or point to a custom datasets root
python -m utils.check_inputs --input-data /path/to/input_data --dataset dataset_name
```

This will provide a detailed report on:
- Directory structure validity
- File type checking
- Tool runnability status
- Input resolution status

For `Minigraph` graph construction, the dataset should provide at least two FASTA
files in `ASSEMBLIES/`: the first is used as the reference backbone and the
others are incrementally added to the graph. The expected output is a graph
file (`.gfa`/rGFA), not a mapping file (`.gaf`).

Validated example datasets currently used in this repository are:
- `input_data/MHC_TEST`
- `input_data/C4_TEST`

Both are suitable for running `Minigraph` as separate experiments, and both now
include validated `GRAPH/` artifacts used by the `LCPan` workflow.

For `PGGB`, the same datasets are used as separate experiments, but the input
must first be concatenated into a single FASTA per dataset.

For `LCPan`, the dataset must also provide one VCF in `GRAPH/` plus a
single-reference FASTA whose header exactly matches the VCF `CHROM` field. In
the validated `C4_TEST` and `MHC_TEST` workflows, both files are derived from a
temporary PanSN-normalized `PGGB` input.

For `MinigraphCactus`, the same assembly-per-sample datasets can be reused,
but the workflow needs a seqfile that maps sample names to FASTA paths.

### 3. Generate Dockerfiles

Generate Dockerfiles for all configured tools:

```bash
python make_dockerfiles.py
```

This creates Dockerfiles in the `Dockerfiles/` directory based on `tools_config.yml`.

### 4. Generate Docker Compose Configuration

Create a docker-compose.yml file for running the tools:

```bash
python make_dockercompose.py
```

This generates a compose file with services for each tool, mounting the `input_data/` and `results/` directories.

### 5. Run Tools

Start the desired tool service:

```bash
docker-compose run cactus
# or
docker-compose run minigraph
# etc.
```

For real `Minigraph` graph construction runs, use the dataset-specific command
inside the container and wrap it with `/usr/bin/time` so that both
`execution.log` and `timing.log` are populated. Example for `MHC_TEST`:

```bash
mkdir -p results/MHC_TEST/Minigraph/outputs results/MHC_TEST/Minigraph/logs
/usr/bin/time -v -o results/MHC_TEST/Minigraph/logs/timing.log -- \
docker compose run --rm minigraph bash -lc "cd /minigraph && ./minigraph -cxggs /input_data/MHC_TEST/ASSEMBLIES/MHC-*.fa > /results/MHC_TEST/Minigraph/outputs/minigraph_MHC.gfa" \
> results/MHC_TEST/Minigraph/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/MHC_TEST/Minigraph
python utils/organize_outputs.py Minigraph results/MHC_TEST/Minigraph/outputs

# Optional: reference-only derived encodings from the canonical GFA
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f /results/MHC_TEST/Minigraph/outputs/minigraph_MHC.gfa > /results/MHC_TEST/Minigraph/outputs/minigraph_MHC_with_wlines.gfa"
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f -W /results/MHC_TEST/Minigraph/outputs/minigraph_MHC.gfa > /results/MHC_TEST/Minigraph/outputs/minigraph_MHC_with_plines.gfa"
sudo chown $USER:$USER \
  results/MHC_TEST/Minigraph/outputs/minigraph_MHC_with_wlines.gfa \
  results/MHC_TEST/Minigraph/outputs/minigraph_MHC_with_plines.gfa
```

This produces:
- `results/MHC_TEST/Minigraph/outputs/minigraph_MHC.gfa`
- optional `results/MHC_TEST/Minigraph/outputs/minigraph_MHC_with_wlines.gfa`
- optional `results/MHC_TEST/Minigraph/outputs/minigraph_MHC_with_plines.gfa`
- `results/MHC_TEST/Minigraph/logs/execution.log`
- `results/MHC_TEST/Minigraph/logs/timing.log`

To build compact Markdown summaries for one dataset after runs complete, use:

```bash
cd /home/azureuser/constructionBS
python utils/summarize_timing_logs.py C4_TEST
python utils/summarize_output_graphs.py C4_TEST
```

This writes:
- `results/<DATASET>/timing_summary.md`
- `results/<DATASET>/output_summary.md`

## Common GFA Line Encodings

Some workflows already write path information as `W`-lines or `P`-lines, while
others need a post-processing step. To avoid repeating the same conversion
commands in every tool section, use the patterns below after the canonical GFA
has been produced.

Current canonical encodings in this repository:
- `PGGB`: canonical graph already uses `P`-lines
- `Cactus`: exported `GFA` already uses `W`-lines
- `ProgressiveCactus`: exported `GFA` already uses `W`-lines
- `MinigraphCactus`: canonical graph already uses `W`-lines
- `Minigraph`: canonical graph has no `P` or `W` records; only the reference
  path embedded in the rGFA tags can be materialized from the current files

For tools whose canonical `GFA` already uses `W`-lines (`Cactus`,
`ProgressiveCactus`, `MinigraphCactus`), keep an explicit `W`-line copy and
derive the `P`-line version with:

```bash
cp <canonical_graph.gfa> <graph_with_wlines.gfa>
docker compose run --rm progressivecactus bash -lc "vg convert -g -f -W <container_canonical_graph.gfa> > <container_graph_with_plines.gfa>"
sudo chown $USER:$USER <graph_with_wlines.gfa> <graph_with_plines.gfa>
```

For tools whose canonical `GFA` already uses `P`-lines (`PGGB`), keep an
explicit `P`-line copy and derive the `W`-line version with:

```bash
cp <canonical_graph.gfa> <graph_with_plines.gfa>
docker compose run --rm progressivecactus bash -lc "vg convert -g -f <container_canonical_graph.gfa> > <container_graph_with_wlines.gfa>"
sudo chown $USER:$USER <graph_with_wlines.gfa> <graph_with_plines.gfa>
```

For `Minigraph`, the current files can only reconstruct the rank-0 reference
path from the rGFA tags, not full per-sample walks. Use:

```bash
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f <container_canonical_graph.gfa> > <container_graph_with_wlines.gfa>"
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f -W <container_canonical_graph.gfa> > <container_graph_with_plines.gfa>"
sudo chown $USER:$USER <graph_with_wlines.gfa> <graph_with_plines.gfa>
```

Tool-specific file targets used in this repository:
- `PGGB`: `pggb_<DATASET_SHORT>.gfa`, `pggb_<DATASET_SHORT>_with_wlines.gfa`,
  `pggb_<DATASET_SHORT>_with_plines.gfa`
- `Minigraph`: `minigraph_<DATASET_SHORT>.gfa`,
  `minigraph_<DATASET_SHORT>_with_wlines.gfa`,
  `minigraph_<DATASET_SHORT>_with_plines.gfa`
- `MinigraphCactus`: `minigraphcactus_<DATASET_SHORT>.gfa`,
  `minigraphcactus_<DATASET_SHORT>_with_wlines.gfa`,
  `minigraphcactus_<DATASET_SHORT>_with_plines.gfa`
- `Cactus`: `cactus_<DATASET_SHORT>.gfa`, `cactus_<DATASET_SHORT>_with_wlines.gfa`,
  `cactus_<DATASET_SHORT>_with_plines.gfa`
- `ProgressiveCactus`: `progressivecactus_<DATASET_SHORT>.gfa`,
  `progressivecactus_<DATASET_SHORT>_with_wlines.gfa`,
  `progressivecactus_<DATASET_SHORT>_with_plines.gfa`

To inspect a large `GFA` without opening the full file in the editor, create a
lightweight preview containing only the header plus `W`/`P` records. Example:

```bash
cd /home/azureuser/constructionBS
grep -nE '^[HWP]	' results/C4_TEST/Cactus/outputs/cactus_C4.gfa \
  > results/C4_TEST/Cactus/outputs/cactus_C4.preview.txt
```

For `PGGB`, use the official container image and prepare one aggregated FASTA
per dataset. The input FASTA must also be indexed with `samtools faidx`, and if
the sequence names do not respect PanSN naming you must provide the haplotype
count explicitly with `-n`.

Example for `C4_TEST`:

```bash
cat input_data/C4_TEST/ASSEMBLIES/C4-*.fa > input_data/C4_TEST/ASSEMBLIES/c4_total.fa
docker compose run --rm pggb bash -lc 'samtools faidx /input_data/C4_TEST/ASSEMBLIES/c4_total.fa'
mkdir -p results/C4_TEST/PGGB/outputs results/C4_TEST/PGGB/logs
/usr/bin/time -p -o results/C4_TEST/PGGB/logs/timing.log docker compose run --rm pggb bash -lc "pggb -i /input_data/C4_TEST/ASSEMBLIES/c4_total.fa -n 96 -o /results/C4_TEST/PGGB/outputs" > results/C4_TEST/PGGB/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/PGGB
python utils/organize_outputs.py PGGB results/C4_TEST/PGGB/outputs
```

This produces:
- `results/C4_TEST/PGGB/outputs/pggb_C4.gfa`
- `results/C4_TEST/PGGB/outputs/artifacts/`
- `results/C4_TEST/PGGB/logs/execution.log`
- `results/C4_TEST/PGGB/logs/timing.log`

Notes from the validated runs:
- `PGGB` writes many intermediate and auxiliary files in its output directory
- the final graph to keep is `*.smooth.final.gfa`
- `utils/organize_outputs.py PGGB ...` copies that file to `pggb_<DATASET_SHORT>.gfa` and moves the remaining artifacts into `outputs/artifacts/`
- if dataset-specific `*_with_wlines.gfa` or `*_with_plines.gfa` files are already present at the top level, rerunning `organize_outputs.py` keeps publishing them with the same canonical dataset-specific names
- `pggb_<DATASET_SHORT>.gfa` is the canonical output kept by this workflow
- if you also want explicit `W`/`P` variants, use the shared conversion patterns
  from `Common GFA Line Encodings`
- the run can still produce a final graph even if `multiqc` is missing from the image; in that case the warning remains in `execution.log`

To keep a stable layout after a run, you can normalize the directory with:

```bash
python utils/organize_outputs.py PGGB results/C4_TEST/PGGB/outputs
```

This keeps:
- `results/C4_TEST/PGGB/outputs/pggb_C4.gfa`

and moves the original PGGB-generated files into:
- `results/C4_TEST/PGGB/outputs/artifacts/`

For `LCPan`, use a PGGB-derived VCF plus a single-reference FASTA with an
exactly matching sequence name. `LCPan` itself expects `ref.fa`, `ref.fa.fai`,
and a plain-text `.vcf`; for the validated `C4_TEST` run the working reference
was `GRCh38#0#C4` extracted from a temporary PanSN FASTA built from
`c4_total.fa`.

Example for `C4_TEST`:

```bash
mkdir -p input_data/C4_TEST/GRAPH/tmp/pggb_vcf

awk '
/^>/ {
  sub(/^>/, "", $0)
  print ">" $0 "#C4"
  next
}
{ print }
' input_data/C4_TEST/ASSEMBLIES/c4_total.fa \
> input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa

docker compose run --rm pggb bash -lc "samtools faidx /input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa"

/usr/bin/time -v -o input_data/C4_TEST/GRAPH/tmp/pggb_vcf/timing.log \
docker compose run --rm pggb bash -lc "pggb -i /input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa -n 96 -o /input_data/C4_TEST/GRAPH/tmp/pggb_vcf -V 'GRCh38#0#C4:1000'" \
> input_data/C4_TEST/GRAPH/tmp/pggb_vcf/execution.log 2>&1

cp input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa.*.smooth.final.GRCh38#0#C4.vcf \
  input_data/C4_TEST/GRAPH/lcpan_C4.vcf

docker compose run --rm pggb bash -lc "samtools faidx /input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa 'GRCh38#0#C4' > /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa"
docker compose run --rm pggb bash -lc "samtools faidx /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa"

./utils/clean_outputs.sh C4_TEST LCPan
/usr/bin/time -v -o results/C4_TEST/LCPan/logs/timing.log docker compose run --rm lcpan bash -lc "/lcpan/bin/lcpan -vg --gfa -t 32 -r /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa -v /input_data/C4_TEST/GRAPH/lcpan_C4.vcf -p /results/C4_TEST/LCPan/outputs/lcpan_C4 && /lcpan/lcpan-merge.sh /results/C4_TEST/LCPan/outputs/lcpan_C4.log" > results/C4_TEST/LCPan/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/LCPan
python utils/organize_outputs.py LCPan results/C4_TEST/LCPan/outputs
```

This produces:
- `results/C4_TEST/LCPan/outputs/lcpan_C4.gfa`
- optional `results/C4_TEST/LCPan/outputs/lcpan_C4_with_wlines.gfa`
- optional `results/C4_TEST/LCPan/outputs/lcpan_C4_with_plines.gfa`
- `results/C4_TEST/LCPan/outputs/artifacts/`
- `results/C4_TEST/LCPan/logs/execution.log`
- `results/C4_TEST/LCPan/logs/timing.log`

Notes:
- helper files used only to make `vg convert` succeed, such as `lcpan_*_vg_ready.gfa` or `lcpan_*_vgfixed.gfa`, belong under `outputs/artifacts/` instead of the top level

For `MinigraphCactus`, use the Cactus container with a generated seqfile and
keep the run wrapped with `/usr/bin/time` so the logs match the other tools.

Example for `C4_TEST`:

```bash
./utils/clean_outputs.sh C4_TEST MinigraphCactus
python utils/make_minigraphcactus_seqfile.py C4_TEST
/usr/bin/time -v -o results/C4_TEST/MinigraphCactus/logs/timing.log docker compose run --rm minigraphcactus bash -lc "cactus-pangenome /results/C4_TEST/MinigraphCactus/outputs/jobstore /results/C4_TEST/MinigraphCactus/outputs/c4_test_seqfile.txt --outDir /results/C4_TEST/MinigraphCactus/outputs --outName minigraphcactus_C4 --reference C4-GRCh38 --gfa clip --batchSystem single_machine --maxCores 32" > results/C4_TEST/MinigraphCactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/MinigraphCactus
python utils/organize_outputs.py MinigraphCactus results/C4_TEST/MinigraphCactus/outputs
```

This produces:
- `results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa`
- `results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa.gz`
- `results/C4_TEST/MinigraphCactus/outputs/artifacts/`
- `results/C4_TEST/MinigraphCactus/logs/execution.log`
- `results/C4_TEST/MinigraphCactus/logs/timing.log`

Notes from the validated runs:
- `MinigraphCactus` writes many intermediate files and directories, including `HAL`, `PAF/GAF`, stats, and chromosomal subproblems
- the final graph to keep is the top-level `*.gfa.gz` output produced by `cactus-pangenome`
- `utils/organize_outputs.py MinigraphCactus ...` keeps both a canonical compressed graph and an uncompressed `GFA` copy for inspection
- if canonical `*_with_wlines.gfa` or `*_with_plines.gfa` files already exist, rerunning `organize_outputs.py` republishes them at the top level with dataset-specific names such as `minigraphcactus_C4_with_wlines.gfa`
- the canonical `GFA` already uses `W`-lines; derive the `P`-line version using
  the shared commands from `Common GFA Line Encodings`
- some output files may be owned by `root` after the container exits, so `chown` is part of the standard post-run cleanup

For `Cactus` (distinct from `MinigraphCactus`), use the `cactus` entrypoint
instead of `cactus-pangenome`. Generate a dedicated Cactus seqfile (with a
tree line) using:

```bash
python utils/make_cactus_seqfile.py C4_TEST
```

This writes `results/C4_TEST/Cactus/outputs/c4_test_seqfile.txt`, which can be
used with `cactus jobStore seqFile outputHal`.

After a Cactus run, normalize outputs with:

```bash
python utils/organize_outputs.py Cactus results/C4_TEST/Cactus/outputs
```

Canonical layout:
- `results/C4_TEST/Cactus/outputs/cactus_C4.hal`
- `results/C4_TEST/Cactus/outputs/artifacts/`

If you export `GFA` from the `HAL`, that `GFA` already uses `W`-lines; derive
the `P`-line version using the shared commands from `Common GFA Line Encodings`.
When those exported files are present, `organize_outputs.py` preserves the
dataset-specific top-level names `cactus_<DATASET_SHORT>.vg`,
`cactus_<DATASET_SHORT>.gfa`, `cactus_<DATASET_SHORT>_with_wlines.gfa`, and
`cactus_<DATASET_SHORT>_with_plines.gfa`.

For `ProgressiveCactus`, use the dedicated `progressivecactus` service. At the
moment the simplest workflow is to reuse `make_cactus_seqfile.py` and write the
seqfile directly into the `ProgressiveCactus` output directory.

Example for `C4_TEST`:

```bash
./utils/clean_outputs.sh C4_TEST ProgressiveCactus
python utils/make_cactus_seqfile.py C4_TEST --output results/C4_TEST/ProgressiveCactus/outputs/c4_test_seqfile.txt
/usr/bin/time -v -o results/C4_TEST/ProgressiveCactus/logs/timing.log docker compose run --rm progressivecactus bash -lc "cactus /results/C4_TEST/ProgressiveCactus/outputs/jobstore /results/C4_TEST/ProgressiveCactus/outputs/c4_test_seqfile.txt /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.hal --batchSystem single_machine --maxCores 32" > results/C4_TEST/ProgressiveCactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/ProgressiveCactus
python utils/organize_outputs.py ProgressiveCactus results/C4_TEST/ProgressiveCactus/outputs
```

Optional graph export from HAL:

```bash
docker compose run --rm progressivecactus bash -lc "hal2vg /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.hal > /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.vg"
docker compose run --rm progressivecactus bash -lc "vg view -g /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.vg > /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.gfa"
sudo chown -R $USER:$USER results/C4_TEST/ProgressiveCactus
```

Example for `MHC_TEST`:

```bash
./utils/clean_outputs.sh MHC_TEST ProgressiveCactus
python utils/make_cactus_seqfile.py MHC_TEST --output results/MHC_TEST/ProgressiveCactus/outputs/mhc_test_seqfile.txt
/usr/bin/time -v -o results/MHC_TEST/ProgressiveCactus/logs/timing.log docker compose run --rm progressivecactus bash -lc "cactus /results/MHC_TEST/ProgressiveCactus/outputs/jobstore /results/MHC_TEST/ProgressiveCactus/outputs/mhc_test_seqfile.txt /results/MHC_TEST/ProgressiveCactus/outputs/progressivecactus_MHC.hal --batchSystem single_machine --maxCores 32" > results/MHC_TEST/ProgressiveCactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/MHC_TEST/ProgressiveCactus
python utils/organize_outputs.py ProgressiveCactus results/MHC_TEST/ProgressiveCactus/outputs
```

Optional graph export from HAL:

```bash
docker compose run --rm progressivecactus bash -lc "hal2vg /results/MHC_TEST/ProgressiveCactus/outputs/progressivecactus_MHC.hal > /results/MHC_TEST/ProgressiveCactus/outputs/progressivecactus_MHC.vg"
docker compose run --rm progressivecactus bash -lc "vg view -g /results/MHC_TEST/ProgressiveCactus/outputs/progressivecactus_MHC.vg > /results/MHC_TEST/ProgressiveCactus/outputs/progressivecactus_MHC.gfa"
sudo chown -R $USER:$USER results/MHC_TEST/ProgressiveCactus
```

This produces:
- `results/<DATASET>/ProgressiveCactus/outputs/progressivecactus_<DATASET_SHORT>.hal`
- optional `results/<DATASET>/ProgressiveCactus/outputs/progressivecactus_<DATASET_SHORT>.vg`
- optional `results/<DATASET>/ProgressiveCactus/outputs/progressivecactus_<DATASET_SHORT>.gfa`
- optional `results/<DATASET>/ProgressiveCactus/outputs/progressivecactus_<DATASET_SHORT>_with_wlines.gfa`
- optional `results/<DATASET>/ProgressiveCactus/outputs/progressivecactus_<DATASET_SHORT>_with_plines.gfa`
- `results/<DATASET>/ProgressiveCactus/outputs/artifacts/`
- `results/<DATASET>/ProgressiveCactus/logs/execution.log`
- `results/<DATASET>/ProgressiveCactus/logs/timing.log`

Notes:
- `ProgressiveCactus` leaves a `jobstore/` under `outputs/`; if a rerun fails with `Permission denied`, fix ownership or remove the old jobstore before retrying
- once the `GFA` has been exported from `HAL`, it already uses `W`-lines;
  derive the `P`-line version using the shared commands from
  `Common GFA Line Encodings`
- preview and helper files such as the generated seqfile, `*.head.txt`,
  `*.preview.txt`, and `*.paths_preview.txt` should live under
  `outputs/artifacts/` rather than at the top level
- some output files may be owned by `root` after the container exits, so `chown` is part of the standard post-run cleanup

## Configuration

### tools_config.yml

This file specifies the versions of each tool:

```yaml
Cactus:
  version: v3.1.4

Minigraph:
  version: 7e3e65c

MinigraphCactus:
  version: v3.1.4

PGGB:
  version: e25486b

ProgressiveCactus:
  version: v3.1.4
```

### Tool Requirements and Input Specifications

Tool requirements and input mappings are defined in `run_config.py`:

- `TOOL_REQUIREMENTS`: Specifies required directories for each tool
- `EXPECTED_FILE_TYPES`: Maps directories to expected file extensions
- `TOOL_INPUT_SPECS`: Defines how tool inputs are resolved from dataset files

## Scripts

- `utils/check_inputs.py`: Dataset validation and inspection tool
- `utils/dataset_utils.py`: Utility functions for dataset handling
- `make_dockerfiles.py`: Dockerfile generation script
- `make_dockercompose.py`: Docker Compose configuration generator
- `run_config.py`: Configuration constants
- `utils/clean_outputs.sh`: Reset one dataset/tool results directory before reruns
- `utils/make_cactus_seqfile.py`: Generate Cactus seqfiles (tree + sample/path mappings) from assembly datasets
- `utils/make_minigraphcactus_seqfile.py`: Generate seqfiles for Minigraph-Cactus from assembly datasets
- `utils/organize_outputs.py`: Normalize supported tool outputs into canonical graph files plus artifacts

## Results Structure

Results are organized as:

```
results/
├── dataset_name/
│   ├── tool_name/
│   │   ├── outputs/
│   │   └── logs/
```

## Adding New Tools

1. Add tool configuration to `tools_config.yml`
2. Define requirements in `run_config.py` (TOOL_REQUIREMENTS, TOOL_INPUT_SPECS)
3. Add Dockerfile template to `make_dockerfiles.py`
4. Add service template to `make_dockercompose.py`

## Contributing

Contributions are welcome! Please ensure that:

- New tools follow the established patterns
- Configuration changes are tested
- Documentation is updated for new features

## License

[Specify license here]

## Contact

[Add contact information]
