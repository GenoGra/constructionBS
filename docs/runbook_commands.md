# Runbook Commands

Last validated: 2026-04-27

This file collects copy-paste commands used to run graph-construction tools in this repository.

Conventions:
- Run from repo root: `/home/azureuser/constructionBS`
- Standard flow: `clean -> run -> chown -> organize`
- `execution.log` and `timing.log` are always written under `results/<DATASET>/<TOOL>/logs`

## Common Setup

```bash
cd /home/azureuser/constructionBS
```

## Minigraph

### C4_TEST

```bash
./utils/clean_outputs.sh C4_TEST Minigraph
/usr/bin/time -v -o results/C4_TEST/Minigraph/logs/timing.log docker compose run --rm minigraph bash -lc "cd /minigraph && ./minigraph -cxggs /input_data/C4_TEST/ASSEMBLIES/C4-*.fa > /results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa" > results/C4_TEST/Minigraph/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/Minigraph
```

### MHC_TEST

```bash
./utils/clean_outputs.sh MHC_TEST Minigraph
/usr/bin/time -v -o results/MHC_TEST/Minigraph/logs/timing.log docker compose run --rm minigraph bash -lc "cd /minigraph && ./minigraph -cxggs /input_data/MHC_TEST/ASSEMBLIES/MHC-*.fa > /results/MHC_TEST/Minigraph/outputs/minigraph_MHC.gfa" > results/MHC_TEST/Minigraph/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/MHC_TEST/Minigraph
```

Canonical output:
- `results/<DATASET>/Minigraph/outputs/minigraph_<DATASET_SHORT>.gfa`

## PGGB

### C4_TEST

```bash
./utils/clean_outputs.sh C4_TEST PGGB
cat input_data/C4_TEST/ASSEMBLIES/C4-*.fa > input_data/C4_TEST/ASSEMBLIES/c4_total.fa
docker compose run --rm pggb bash -lc "samtools faidx /input_data/C4_TEST/ASSEMBLIES/c4_total.fa"
/usr/bin/time -v -o results/C4_TEST/PGGB/logs/timing.log docker compose run --rm pggb bash -lc "pggb -i /input_data/C4_TEST/ASSEMBLIES/c4_total.fa -n 96 -o /results/C4_TEST/PGGB/outputs" > results/C4_TEST/PGGB/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/PGGB
python utils/organize_outputs.py PGGB results/C4_TEST/PGGB/outputs
```

### MHC_TEST

```bash
./utils/clean_outputs.sh MHC_TEST PGGB
cat input_data/MHC_TEST/ASSEMBLIES/MHC-*.fa > input_data/MHC_TEST/ASSEMBLIES/mhc_total.fa
docker compose run --rm pggb bash -lc "samtools faidx /input_data/MHC_TEST/ASSEMBLIES/mhc_total.fa"
/usr/bin/time -v -o results/MHC_TEST/PGGB/logs/timing.log docker compose run --rm pggb bash -lc "pggb -i /input_data/MHC_TEST/ASSEMBLIES/mhc_total.fa -n 61 -o /results/MHC_TEST/PGGB/outputs" > results/MHC_TEST/PGGB/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/MHC_TEST/PGGB
python utils/organize_outputs.py PGGB results/MHC_TEST/PGGB/outputs
```

Canonical output:
- `results/<DATASET>/PGGB/outputs/pggb_graph.gfa`

## MinigraphCactus

### C4_TEST

```bash
./utils/clean_outputs.sh C4_TEST MinigraphCactus
python utils/make_minigraphcactus_seqfile.py C4_TEST
/usr/bin/time -v -o results/C4_TEST/MinigraphCactus/logs/timing.log docker compose run --rm minigraphcactus bash -lc "cactus-pangenome /results/C4_TEST/MinigraphCactus/outputs/jobstore /results/C4_TEST/MinigraphCactus/outputs/c4_test_seqfile.txt --outDir /results/C4_TEST/MinigraphCactus/outputs --outName minigraphcactus_C4 --reference C4-GRCh38 --gfa clip --batchSystem single_machine --maxCores 32" > results/C4_TEST/MinigraphCactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/MinigraphCactus
python utils/organize_outputs.py MinigraphCactus results/C4_TEST/MinigraphCactus/outputs
```

### MHC_TEST

```bash
./utils/clean_outputs.sh MHC_TEST MinigraphCactus
python utils/make_minigraphcactus_seqfile.py MHC_TEST
/usr/bin/time -v -o results/MHC_TEST/MinigraphCactus/logs/timing.log docker compose run --rm minigraphcactus bash -lc "cactus-pangenome /results/MHC_TEST/MinigraphCactus/outputs/jobstore /results/MHC_TEST/MinigraphCactus/outputs/mhc_test_seqfile.txt --outDir /results/MHC_TEST/MinigraphCactus/outputs --outName minigraphcactus_MHC --reference MHC-GRCh38 --gfa clip --batchSystem single_machine --maxCores 32" > results/MHC_TEST/MinigraphCactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/MHC_TEST/MinigraphCactus
python utils/organize_outputs.py MinigraphCactus results/MHC_TEST/MinigraphCactus/outputs
```

Canonical outputs:
- `results/<DATASET>/MinigraphCactus/outputs/minigraphcactus_graph.gfa`
- `results/<DATASET>/MinigraphCactus/outputs/minigraphcactus_graph.gfa.gz`

## Cactus

`make_cactus_seqfile.py` now creates sanitized FASTAs in:
- `input_data/<DATASET>/ASSEMBLIES_CACTUS_SANITIZED`

The generated seqfile points to sanitized inputs automatically.

### C4_TEST

```bash
./utils/clean_outputs.sh C4_TEST Cactus
python utils/make_cactus_seqfile.py C4_TEST
/usr/bin/time -v -o results/C4_TEST/Cactus/logs/timing.log docker compose run --rm cactus bash -lc "cactus /results/C4_TEST/Cactus/outputs/jobstore /results/C4_TEST/Cactus/outputs/c4_test_seqfile.txt /results/C4_TEST/Cactus/outputs/cactus_C4.hal --batchSystem single_machine --maxCores 32" > results/C4_TEST/Cactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/Cactus
python utils/organize_outputs.py Cactus results/C4_TEST/Cactus/outputs
```

### MHC_TEST

```bash
./utils/clean_outputs.sh MHC_TEST Cactus
python utils/make_cactus_seqfile.py MHC_TEST
/usr/bin/time -v -o results/MHC_TEST/Cactus/logs/timing.log docker compose run --rm cactus bash -lc "cactus /results/MHC_TEST/Cactus/outputs/jobstore /results/MHC_TEST/Cactus/outputs/mhc_test_seqfile.txt /results/MHC_TEST/Cactus/outputs/cactus_MHC.hal --batchSystem single_machine --maxCores 32" > results/MHC_TEST/Cactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/MHC_TEST/Cactus
python utils/organize_outputs.py Cactus results/MHC_TEST/Cactus/outputs
```

Optional graph export from HAL:

```bash
docker compose run --rm cactus bash -lc "hal2vg /results/MHC_TEST/Cactus/outputs/cactus_alignment.hal > /results/MHC_TEST/Cactus/outputs/cactus_alignment.vg"
docker compose run --rm cactus bash -lc "vg view -g /results/MHC_TEST/Cactus/outputs/cactus_alignment.vg > /results/MHC_TEST/Cactus/outputs/cactus_alignment.gfa"
sudo chown -R $USER:$USER results/MHC_TEST/Cactus
```

Canonical output:
- `results/<DATASET>/Cactus/outputs/cactus_alignment.hal`

## Quick Troubleshooting

- `FileNotFoundError: no final output matching '*.hal'`:
  run failed before HAL creation; inspect `results/<DATASET>/Cactus/logs/execution.log`.

- Cactus header errors (`invalid character in fasta header`):
  regenerate seqfile with:
  ```bash
  python utils/make_cactus_seqfile.py <DATASET>
  ```
  it rebuilds `ASSEMBLIES_CACTUS_SANITIZED`.

- Permission issues after container runs:
  ```bash
  sudo chown -R $USER:$USER results/<DATASET>/<TOOL>
  ```
