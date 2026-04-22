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
python check_inputs.py input_data/dataset_name
```

This will provide a detailed report on:
- Directory structure validity
- File type checking
- Tool runnability status
- Input resolution status

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
