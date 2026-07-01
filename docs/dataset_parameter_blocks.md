# Dataset Parameter Blocks

Reference sheet extracted from [docs/runbook_commands.md](/home/azureuser/constructionBS/docs/runbook_commands.md:1).

Use these blocks to fill the editable variables at the top of each runbook section.
This file is intentionally dataset-centric, so you can copy the right parameter block
without scanning the full runbook.

Notes:
- Paths and names mirror the current repository layout.
- When a block is marked `N/A`, the corresponding validated input files are not present
  in the repository today, so the runbook section is not currently plug-and-play for
  that dataset.
- `PGGB_N` is the number of PanSN sequences expected by `pggb` for the aggregated
  dataset input.
- `REFERENCE_PAN_NAME` is the exact path name to preserve when deriving the reference
  `P`-line view from the canonical PGGB graph.

## C4_TEST

### Minigraph
```bash
DATASET="C4_TEST"
DATASET_SHORT="C4"
TOOL="Minigraph"
ASSEMBLY_GLOB="/input_data/${DATASET}/ASSEMBLIES/${DATASET_SHORT}-*.fa"
```

### LCPan PGGB vg/vgx
```bash
DATASET="C4_TEST"
DATASET_SHORT="C4"
THREADS="32"
VARIANT="pggb_vg"   # or pggb_vgx
MODE_FLAG="-vg"     # or -vgx
REFERENCE_FASTA="/input_data/${DATASET}/GRAPH/c4_reference_pansn.fa"
INPUT_VCF="/input_data/${DATASET}/GRAPH/lcpan_C4.vcf"
```

### PGGB
```bash
DATASET="C4_TEST"
DATASET_SHORT="C4"
THREADS="${THREADS:-16}"
PGGB_N="96"
REFERENCE_PAN_NAME="GRCh38#0#C4"
```

### POASTA
```bash
DATASET="C4_TEST"
DATASET_SHORT="C4"
PAN_INPUT="input_data/${DATASET}/AUXILIARY_INPUTS/c4_total_pansn.fa"
```

### MinigraphCactus
```bash
DATASET="C4_TEST"
DATASET_SHORT="C4"
REFERENCE_NAME="C4-GRCh38"
MAX_CORES="32"
```

### MC_vg
```bash
DATASET="C4_TEST"
TOOL_NAME="MC_vg"
SEQFILE_NAME="c4_test_seqfile.txt"
REFERENCE_NAME="C4-GRCh38"
REFERENCE_FASTA="input_data/C4_TEST/ASSEMBLIES_CACTUS_SANITIZED/C4-00GRCh38.fa"
OUT_NAME="result_cactus_new"
AUTOINDEX_PREFIX="result_autoindex"
MAX_CORES="16"
```

### Cactus
```bash
DATASET="C4_TEST"
DATASET_SHORT="C4"
REFERENCE_NAME="C4-GRCh38"
MAX_CORES="32"
```

### ProgressiveCactus
```bash
DATASET="C4_TEST"
DATASET_SHORT="C4"
REFERENCE_NAME="C4-GRCh38"
MAX_CORES="32"
```

### LCPan MC vg/vgx
```bash
DATASET="C4_TEST"
DATASET_SHORT="C4"
REFERENCE_FASTA_SOURCE="input_data/${DATASET}/ASSEMBLIES/C4-00GRCh38.fa"
CACTUS_VCF_GZ="results/${DATASET}/MC_vg/outputs/result_cactus_new.vcf.gz"
THREADS="32"
```

## KIR_TEST

### Minigraph
```bash
DATASET="KIR_TEST"
DATASET_SHORT="KIR"
TOOL="Minigraph"
ASSEMBLY_GLOB="/input_data/${DATASET}/ASSEMBLIES/${DATASET_SHORT}-*.fa"
```

### LCPan PGGB vg/vgx
```bash
DATASET="KIR_TEST"
DATASET_SHORT="KIR"
THREADS="32"
VARIANT="pggb_vg"   # or pggb_vgx
MODE_FLAG="-vg"     # or -vgx
REFERENCE_FASTA="/input_data/${DATASET}/GRAPH/kir_reference_pansn.fa"
INPUT_VCF="/input_data/${DATASET}/GRAPH/lcpan_KIR.vcf"
```

### PGGB
```bash
DATASET="KIR_TEST"
DATASET_SHORT="KIR"
THREADS="${THREADS:-16}"
PGGB_N="7"
REFERENCE_PAN_NAME="GRCh38#0#KIR"
```

### POASTA
```bash
DATASET="KIR_TEST"
DATASET_SHORT="KIR"
PAN_INPUT="input_data/${DATASET}/AUXILIARY_INPUTS/kir_total_pansn.fa"
```

### MinigraphCactus
```bash
DATASET="KIR_TEST"
DATASET_SHORT="KIR"
REFERENCE_NAME="KIR-GRCh38"
MAX_CORES="32"
```

### MC_vg
```bash
DATASET="KIR_TEST"
TOOL_NAME="MC_vg"
SEQFILE_NAME="kir_test_seqfile.txt"
REFERENCE_NAME="KIR-GRCh38"
REFERENCE_FASTA="input_data/KIR_TEST/ASSEMBLIES/KIR-00GRCh38.fa"
OUT_NAME="result_cactus_new"
AUTOINDEX_PREFIX="result_autoindex"
MAX_CORES="16"
```

### Cactus
```bash
DATASET="KIR_TEST"
DATASET_SHORT="KIR"
REFERENCE_NAME="KIR-GRCh38"
MAX_CORES="32"
```

### ProgressiveCactus
```bash
DATASET="KIR_TEST"
DATASET_SHORT="KIR"
REFERENCE_NAME="KIR-GRCh38"
MAX_CORES="32"
```

### LCPan MC vg/vgx
```bash
DATASET="KIR_TEST"
DATASET_SHORT="KIR"
REFERENCE_FASTA_SOURCE="input_data/${DATASET}/ASSEMBLIES/KIR-00GRCh38.fa"
CACTUS_VCF_GZ="results/${DATASET}/MC_vg/outputs/result_cactus_new.vcf.gz"
THREADS="32"
```

## MHC_TEST

### Minigraph
```bash
DATASET="MHC_TEST"
DATASET_SHORT="MHC"
TOOL="Minigraph"
ASSEMBLY_GLOB="/input_data/${DATASET}/ASSEMBLIES/${DATASET_SHORT}-*.fa"
```

### LCPan PGGB vg/vgx
```bash
DATASET="MHC_TEST"
DATASET_SHORT="MHC"
THREADS="32"
VARIANT="pggb_vg"   # or pggb_vgx
MODE_FLAG="-vg"     # or -vgx
REFERENCE_FASTA="/input_data/${DATASET}/GRAPH/mhc_reference_pansn.fa"
INPUT_VCF="/input_data/${DATASET}/GRAPH/lcpan_MHC.vcf"
```

### PGGB
```bash
DATASET="MHC_TEST"
DATASET_SHORT="MHC"
THREADS="${THREADS:-16}"
PGGB_N="61"
REFERENCE_PAN_NAME="GRCh38#0#MHC"
```

### POASTA
```bash
DATASET="MHC_TEST"
DATASET_SHORT="MHC"
PAN_INPUT="input_data/${DATASET}/AUXILIARY_INPUTS/mhc_total_pansn.fa"
```

### MinigraphCactus
```bash
DATASET="MHC_TEST"
DATASET_SHORT="MHC"
REFERENCE_NAME="MHC-GRCh38"
MAX_CORES="32"
```

### MC_vg
```bash
DATASET="MHC_TEST"
TOOL_NAME="MC_vg"
SEQFILE_NAME="mhc_test_seqfile.txt"
REFERENCE_NAME="MHC-GRCh38"
REFERENCE_FASTA="input_data/MHC_TEST/ASSEMBLIES/MHC-00GRCh38.fa"
OUT_NAME="result_cactus_new"
AUTOINDEX_PREFIX="result_autoindex"
MAX_CORES="16"
```

### Cactus
```bash
DATASET="MHC_TEST"
DATASET_SHORT="MHC"
REFERENCE_NAME="MHC-GRCh38"
MAX_CORES="32"
```

### ProgressiveCactus
```bash
DATASET="MHC_TEST"
DATASET_SHORT="MHC"
REFERENCE_NAME="MHC-GRCh38"
MAX_CORES="32"
```

### LCPan MC vg/vgx
```bash
DATASET="MHC_TEST"
DATASET_SHORT="MHC"
REFERENCE_FASTA_SOURCE="input_data/${DATASET}/ASSEMBLIES/MHC-00GRCh38.fa"
CACTUS_VCF_GZ="results/${DATASET}/MC_vg/outputs/result_cactus_new.vcf.gz"
THREADS="32"
```

## SALMONELLA_TEST

### Minigraph
```bash
DATASET="SALMONELLA_TEST"
DATASET_SHORT="SALMONELLA"
TOOL="Minigraph"
# SALMONELLA_TEST mixes .fa, .fasta, and .fna inputs, so do not use the generic
# -*.fa glob from the other datasets here.
ASSEMBLY_GLOB="/input_data/${DATASET}/ASSEMBLIES/*"
```

### LCPan PGGB vg/vgx
```bash
# Run this only after preparing the SALMONELLA GRAPH inputs. These files are not
# shipped prebuilt in the current repository state.
DATASET="SALMONELLA_TEST"
DATASET_SHORT="SALMONELLA"
THREADS="32"
VARIANT="pggb_vg"   # or pggb_vgx
MODE_FLAG="-vg"     # or -vgx
REFERENCE_FASTA="/input_data/${DATASET}/GRAPH/salmonella_reference_pansn.fa"
INPUT_VCF="/input_data/${DATASET}/GRAPH/lcpan_SALMONELLA.vcf"
```

### PGGB
```bash
DATASET="SALMONELLA_TEST"
DATASET_SHORT="SALMONELLA"
THREADS="${THREADS:-16}"
PGGB_N="127"
REFERENCE_PAN_NAME="FQ312003#0#SALMONELLA"
```

### POASTA
```bash
DATASET="SALMONELLA_TEST"
DATASET_SHORT="SALMONELLA"
PAN_INPUT="input_data/${DATASET}/AUXILIARY_INPUTS/salmonella_total_pansn.fa"
```

### MinigraphCactus
```bash
DATASET="SALMONELLA_TEST"
DATASET_SHORT="SALMONELLA"
REFERENCE_NAME="FQ312003"
MAX_CORES="32"
```

### MC_vg
```bash
DATASET="SALMONELLA_TEST"
TOOL_NAME="MC_vg"
SEQFILE_NAME="salmonella_test_seqfile.txt"
REFERENCE_NAME="FQ312003"
REFERENCE_FASTA="input_data/SALMONELLA_TEST/ASSEMBLIES/FQ312003.fa"
OUT_NAME="result_cactus_new"
AUTOINDEX_PREFIX="result_autoindex"
MAX_CORES="16"
```

### Cactus
```bash
DATASET="SALMONELLA_TEST"
DATASET_SHORT="SALMONELLA"
REFERENCE_NAME="FQ312003"
MAX_CORES="32"
```

### ProgressiveCactus
```bash
DATASET="SALMONELLA_TEST"
DATASET_SHORT="SALMONELLA"
REFERENCE_NAME="FQ312003"
MAX_CORES="32"
```

### LCPan MC vg/vgx
```bash
DATASET="SALMONELLA_TEST"
DATASET_SHORT="SALMONELLA"
REFERENCE_FASTA_SOURCE="input_data/${DATASET}/ASSEMBLIES/FQ312003.fa"
CACTUS_VCF_GZ="results/${DATASET}/MC_vg/outputs/result_cactus_new.vcf.gz"
THREADS="32"
```

## MONKEY_TEST

### Minigraph
`N/A` for the current reference-free setup.

### LCPan PGGB vg/vgx
`N/A` for the current reference-free setup.

### PGGB
```bash
DATASET="MONKEY_TEST"
DATASET_SHORT="MONKEY"
THREADS="${THREADS:-16}"
PGGB_N="100"
PAN_INPUT="input_data/${DATASET}/AUXILIARY_INPUTS/monkey_total_pansn.fa"
```

### POASTA
```bash
DATASET="MONKEY_TEST"
DATASET_SHORT="MONKEY"
PAN_INPUT="input_data/${DATASET}/AUXILIARY_INPUTS/monkey_total_pansn.fa"
```

### MinigraphCactus
`N/A` for the current reference-free setup.

### MC_vg
`N/A` for the current reference-free setup.

### Cactus
`N/A` for the current reference-free setup.

### ProgressiveCactus
`N/A` for the current reference-free setup.

### LCPan MC vg/vgx
`N/A` for the current reference-free setup.

### Theseus
```bash
DATASET="MONKEY_TEST"
DATASET_SHORT="MONKEY"
PAN_INPUT="input_data/${DATASET}/AUXILIARY_INPUTS/monkey_total.fa"
```
