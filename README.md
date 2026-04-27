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

- **Cactus**: Progressive alignment and graph construction
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
  graph: false
  reads: false
  tree: true
supported_workflows:
  - Cactus
  - ProgressiveCactus
```

## Usage

### 1. Prepare Datasets

Place your datasets in the `input_data/` directory following the required structure.

### 2. Check Dataset Readiness

Use the `check_inputs.py` script to validate your datasets:

```bash
python check_inputs.py --dataset dataset_name
# or inspect everything under the default input_data/ directory
python check_inputs.py
# or point to a custom datasets root
python check_inputs.py --input-data /path/to/input_data --dataset dataset_name
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

Both contain only assembly FASTA files in `ASSEMBLIES/` and are suitable for
running `Minigraph` as separate experiments.

For `PGGB`, the same datasets are used as separate experiments, but the input
must first be concatenated into a single FASTA per dataset.

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
docker compose run --rm minigraph bash -lc "/usr/bin/time -v -o /results/MHC_TEST/Minigraph/logs/timing.log bash -lc 'cd /minigraph && ./minigraph -cxggs /input_data/MHC_TEST/ASSEMBLIES/MHC-*.fa > /results/MHC_TEST/Minigraph/outputs/minigraph_graph.gfa' > /results/MHC_TEST/Minigraph/logs/execution.log 2>&1"
```

This produces:
- `results/MHC_TEST/Minigraph/outputs/minigraph_graph.gfa`
- `results/MHC_TEST/Minigraph/logs/execution.log`
- `results/MHC_TEST/Minigraph/logs/timing.log`

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
- `results/C4_TEST/PGGB/outputs/pggb_graph.gfa`
- `results/C4_TEST/PGGB/outputs/artifacts/`
- `results/C4_TEST/PGGB/logs/execution.log`
- `results/C4_TEST/PGGB/logs/timing.log`

Notes from the validated runs:
- `PGGB` writes many intermediate and auxiliary files in its output directory
- the final graph to keep is `*.smooth.final.gfa`
- `utils/organize_outputs.py PGGB ...` copies that file to `pggb_graph.gfa` and moves the remaining artifacts into `outputs/artifacts/`
- the run can still produce a final graph even if `multiqc` is missing from the image; in that case the warning remains in `execution.log`

To keep a stable layout after a run, you can normalize the directory with:

```bash
python utils/organize_outputs.py PGGB results/C4_TEST/PGGB/outputs
```

This keeps:
- `results/C4_TEST/PGGB/outputs/pggb_graph.gfa`

and moves the original PGGB-generated files into:
- `results/C4_TEST/PGGB/outputs/artifacts/`

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
- `results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_graph.gfa`
- `results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_graph.gfa.gz`
- `results/C4_TEST/MinigraphCactus/outputs/artifacts/`
- `results/C4_TEST/MinigraphCactus/logs/execution.log`
- `results/C4_TEST/MinigraphCactus/logs/timing.log`

Notes from the validated runs:
- `MinigraphCactus` writes many intermediate files and directories, including `HAL`, `PAF/GAF`, stats, and chromosomal subproblems
- the final graph to keep is the top-level `*.gfa.gz` output produced by `cactus-pangenome`
- `utils/organize_outputs.py MinigraphCactus ...` keeps both a canonical compressed graph and an uncompressed `GFA` copy for inspection
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

- `check_inputs.py`: Dataset validation and inspection tool
- `dataset_utils.py`: Utility functions for dataset handling
- `make_dockerfiles.py`: Dockerfile generation script
- `make_dockercompose.py`: Docker Compose configuration generator
- `run_config.py`: Configuration constants
- `utils/clean_outputs.sh`: Reset one dataset/tool results directory before reruns
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
