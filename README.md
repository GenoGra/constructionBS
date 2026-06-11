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
- **LCPan**: VCF-driven pangenome graph builder from a single-reference FASTA + VCF (`-vg` and `-vgx` modes)

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
- `input_data/KIR_TEST`

Input layout convention for assembly datasets:
- `ASSEMBLIES/` must contain only the primary per-sample FASTA inputs used by
  graph-construction workflows.
- `ASSEMBLIES_CACTUS_SANITIZED/` must contain only sanitized copies of those
  same primary assemblies for Cactus-family workflows.
- `AUXILIARY_INPUTS/` should store helper FASTA files that must not be treated
  as primary assemblies, including concatenated inputs such as `*_total.fa`,
  helper references such as `*_reference.fa`, helper query files such as
  `*_queries.fa`, and original multi-FASTA aggregates.
- The seqfile generators intentionally ignore those helper inputs so they are
  not accidentally pulled into new runs.

For `PGGB`, the same datasets are used as separate experiments, but the input
must first be concatenated into a single FASTA per dataset.

For `LCPan`, the dataset must also provide one VCF in `GRAPH/` plus a
single-reference FASTA whose header exactly matches the VCF `CHROM` field.

For `MinigraphCactus`, the same assembly-per-sample datasets can be reused,
but the workflow needs a seqfile that maps sample names to FASTA paths.

Graph-visualization normalization convention:
- Keep the canonical graph output from each tool unchanged.
- If a viewer requires the reference to appear as a `P`-line instead of a
  `W`-line, write a derived visualization-only GFA rather than modifying the
  canonical file.
- For `Cactus`, `ProgressiveCactus`, and `MinigraphCactus`, only the
  reference `W` should be replaced with a `P`; all other sample `W`-lines stay
  unchanged.
- For `Minigraph`, the canonical output is an rGFA without native `P`/`W`
  records; only the reference backbone can be derived later from the rGFA
  tags, not the sample paths.
- For `LCPan`, the current outputs preserve only the reference `P`; sample
  `W`-lines and sample `P`-lines are not recoverable from the current GFA
  outputs.

For `LCPan`, Docker image generation is fully integrated in `tools_config.yml`
and `make_dockerfiles.py`; set the desired `ref` for the `lcpan` tool to pin
the exact upstream revision used in runs.

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

For real graph construction runs, use the dataset-specific command
inside the container and wrap it with `/usr/bin/time` so that both
`execution.log` and `timing.log` are populated. 

To build compact Markdown summaries for one dataset after runs complete, use:

```bash
cd /home/azureuser/constructionBS
python utils/summarize_timing_logs.py <TEST_NAME>
python utils/summarize_output_graphs.py <TEST_NAME>
```

This writes:
- `results/<DATASET>/timing_summary.md`
- `results/<DATASET>/output_summary.md`

Canonical naming note:
- `python utils/organize_outputs.py ...` and `python utils/summarize_output_graphs.py <DATASET>`
  now both prefer the optional metadata field `dataset_short` when present
- if `dataset_short` is absent, both commands keep the legacy behavior and
  derive the short token by stripping a trailing `_TEST`

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
`ProgressiveCactus`, `MinigraphCactus`, and normalized `LCPan` outputs), keep an explicit `W`-line copy and
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

To inspect a large `GFA` without opening the full file in the editor, create a
lightweight preview containing only the header plus `W`/`P` records. Example:

```bash
cd /home/azureuser/constructionBS
grep -nE '^[HWP]	' results/C4_TEST/Cactus/outputs/cactus_C4.gfa \
  > results/C4_TEST/Cactus/outputs/cactus_C4.preview.txt
```

For `PGGB`, use the official container image and prepare one aggregated FASTA
per dataset. The input FASTA must also be indexed with `samtools faidx`. In
practice, the most robust setup is to build a PanSN FASTA with canonical
headers of the form `sample#hap#contig_or_region`; this avoids ambiguous prefix
grouping during PGGB's prefix-based mapping stage and makes the final GFA
consistent with downstream tooling.

Example for `C4_TEST`:

```bash
cat input_data/C4_TEST/ASSEMBLIES/C4-*.fa > input_data/C4_TEST/AUXILIARY_INPUTS/c4_total.fa

awk '
/^>/ {
  h = substr($0, 2)
  if (match(h, /^(.*)_([0-9]+)$/, a)) {
    print ">" a[1] "#" a[2] "#C4"
  } else {
    print "ERROR: unrecognized header -> " h > "/dev/stderr"
    exit 1
  }
  next
}
{ print }
' input_data/C4_TEST/AUXILIARY_INPUTS/c4_total.fa > input_data/C4_TEST/AUXILIARY_INPUTS/c4_total_pansn.fa

docker compose run --rm pggb bash -lc 'samtools faidx /input_data/C4_TEST/AUXILIARY_INPUTS/c4_total_pansn.fa'
mkdir -p results/C4_TEST/PGGB/outputs results/C4_TEST/PGGB/logs
/usr/bin/time -p -o results/C4_TEST/PGGB/logs/timing.log docker compose run --rm pggb bash -lc "pggb -i /input_data/C4_TEST/AUXILIARY_INPUTS/c4_total_pansn.fa -n 96 -o /results/C4_TEST/PGGB/outputs" > results/C4_TEST/PGGB/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/PGGB
python utils/organize_outputs.py PGGB results/C4_TEST/PGGB/outputs
```

This produces:
- `results/C4_TEST/PGGB/outputs/pggb_C4.gfa`
- `results/C4_TEST/PGGB/outputs/artifacts/`
- `results/C4_TEST/PGGB/logs/execution.log`
- `results/C4_TEST/PGGB/logs/timing.log`

To keep a stable layout after a run, you can normalize the directory with:

```bash
python utils/organize_outputs.py PGGB results/C4_TEST/PGGB/outputs
```

This keeps:
- `results/C4_TEST/PGGB/outputs/pggb_C4.gfa`

and moves the original PGGB-generated files into:
- `results/C4_TEST/PGGB/outputs/artifacts/`

For cross-tool comparisons on `C4_TEST`, the raw PGGB GFA may need one final
normalization step. PGGB emits `P` lines for every sample, while the rest of
this study uses one reference `P` plus sample `W` lines. The validated
convention is:
- keep `GRCh38#0#C4` as the only `P`
- convert every non-reference sample path to a `W`
- preserve segments and links unchanged

Example normalization:

```bash
awk '
BEGIN {
  FS = OFS = "	"
  ref = "GRCh38#0#C4"
}
$1 == "S" {
  seglen[$2] = length($3)
  print
  next
}
$1 != "P" {
  print
  next
}
{
  name = $2
  path = $3

  if (name == ref) {
    print
    next
  }

  if (match(name, /^([^#]+)#([^#]+)#(.+)$/, a) == 0) {
    print "ERROR: non-canonical PanSN name -> " name > "/dev/stderr"
    exit 1
  }

  sample = a[1]
  hap = a[2]
  seqid = a[3]

  n = split(path, steps, ",")
  walk = ""
  endpos = 0

  for (i = 1; i <= n; i++) {
    step = steps[i]
    orient = substr(step, length(step), 1)
    node = substr(step, 1, length(step) - 1)

    if (!(node in seglen)) {
      print "ERROR: missing segment -> " node > "/dev/stderr"
      exit 1
    }

    if (orient == "+") {
      walk = walk ">" node
    } else if (orient == "-") {
      walk = walk "<" node
    } else {
      print "ERROR: invalid orientation -> " step > "/dev/stderr"
      exit 1
    }

    endpos += seglen[node]
  }

  print "W", sample, hap, seqid, 0, endpos - 1, walk
}
' results/C4_TEST/PGGB/outputs/pggb_C4.gfa > results/C4_TEST/PGGB/outputs/pggb_C4_refP_sampleW.gfa
```

For `LCPan`, use a PGGB-derived VCF plus a single-reference FASTA with an
exactly matching sequence name. `LCPan` itself expects `ref.fa`, `ref.fa.fai`,
and a plain-text `.vcf`; for the validated `C4_TEST` run the working reference
was `GRCh38#0#C4` extracted from a temporary PanSN FASTA built from
`AUXILIARY_INPUTS/c4_total.fa`.

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
' input_data/C4_TEST/AUXILIARY_INPUTS/c4_total.fa \
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
/usr/bin/time -v -o results/C4_TEST/LCPan/pggb_vg/logs/timing.log docker compose run --rm lcpan bash -lc "/lcpan/bin/lcpan -vg --gfa -t 32 -r /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa -v /input_data/C4_TEST/GRAPH/lcpan_C4.vcf -p /results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4 && /lcpan/lcpan-merge.sh /results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4.log" > results/C4_TEST/LCPan/pggb_vg/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/LCPan
python utils/organize_outputs.py LCPan results/C4_TEST/LCPan/pggb_vg/outputs
```

This produces:
- `results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4.gfa`
- optional `results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4_with_wlines.gfa`
- optional `results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4_with_plines.gfa`
- `results/C4_TEST/LCPan/pggb_vg/outputs/artifacts/`
- `results/C4_TEST/LCPan/pggb_vg/logs/execution.log`
- `results/C4_TEST/LCPan/pggb_vg/logs/timing.log`

Notes:
- `pggb_vg` is the standard top-level LCPan branch; `pggb_vgx` is its expanded-graph sibling branch
- `from_MC_vg` and `from_MC_vgx` are downstream LCPan branches built from `MC_vg` outputs (`results/<DATASET>/LCPan/mc_vg` and `results/<DATASET>/LCPan/mc_vgx`)
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

LCPan:
  version: v1.1

```

### Tool Requirements and Input Specifications

Tool requirements, service metadata, and input mappings are centralized in
`tool_registry.py`. The compatibility module `run_config.py` re-exports the
tool requirements and input specifications consumed by the dataset utilities.

- `TOOL_REGISTRY`: Central per-tool registry for source type, compose service
  metadata, required directories, and input-resolution rules
- `TOOL_REQUIREMENTS`: Specifies required directories for each tool
- `EXPECTED_FILE_TYPES`: Maps directories to expected file extensions
- `TOOL_INPUT_SPECS`: Defines how tool inputs are resolved from dataset files

## Scripts

- `utils/check_inputs.py`: Dataset validation and inspection tool
- `tool_registry.py`: Central tool metadata registry used by Docker and dataset helpers
- `utils/dataset_utils.py`: Compatibility facade that re-exports dataset helper functions
- `make_dockerfiles.py`: Dockerfile generation script
- `make_dockercompose.py`: Docker Compose configuration generator
- `run_config.py`: Compatibility configuration exports for file types and tool input requirements
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
2. Add the tool entry to `tool_registry.py` with source type, compose service metadata, requirements, and input specs
3. Add the Dockerfile template to `make_dockerfiles.py`
4. Update any workflow-specific helpers only if the new tool needs custom handling beyond the shared registry
