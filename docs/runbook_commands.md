# Runbook Commands

Last validated: 2026-04-30

This file collects copy-paste commands used to run graph-construction tools in this repository.

Conventions:
- Run from repo root: `/home/azureuser/constructionBS`
- Standard flow: `clean -> run -> chown -> organize`
- `execution.log` and `timing.log` are always written under `results/<DATASET>/<TOOL>/logs`

Path and logging policy (always apply):
- Launch every `docker compose` command from repo root: `/home/azureuser/constructionBS`
- Inside containers, use only absolute mounted paths (`/results/...`, `/input_data/...`)
- Never use relative container paths for graph files (for example `minigraphcactus_C4.gfa`)
- Use `/usr/bin/time -v -o ... -- docker compose ...` for all tools to keep `timing.log` format uniform

## Common Setup

```bash
cd /home/azureuser/constructionBS
```

## Result Summaries

After one dataset run is complete, generate compact Markdown summaries with:

```bash
python utils/summarize_timing_logs.py C4_TEST
python utils/summarize_output_graphs.py C4_TEST
```

This writes:
- `results/<DATASET>/timing_summary.md`
- `results/<DATASET>/output_summary.md`

## C4 End-to-End Commands By Tool

This section is intentionally redundant and operational: each tool has one
complete C4 command block (`clean -> run -> chown -> organize -> optional
line-encoding conversions -> checks`).

### Minigraph (C4_TEST)

```bash
cd /home/azureuser/constructionBS
./utils/clean_outputs.sh C4_TEST Minigraph
/usr/bin/time -v -o results/C4_TEST/Minigraph/logs/timing.log -- \
docker compose run --rm minigraph bash -lc "cd /minigraph && ./minigraph -cxggs /input_data/C4_TEST/ASSEMBLIES/C4-*.fa > /results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa" \
> results/C4_TEST/Minigraph/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/Minigraph
python utils/organize_outputs.py Minigraph results/C4_TEST/Minigraph/outputs
# Canonical output: results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa

# Optional: reference-only derived encodings from Minigraph canonical GFA
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f /results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa > /results/C4_TEST/Minigraph/outputs/minigraph_C4_with_wlines.gfa"
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f -W /results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa > /results/C4_TEST/Minigraph/outputs/minigraph_C4_with_plines.gfa"
sudo chown $USER:$USER \
  results/C4_TEST/Minigraph/outputs/minigraph_C4_with_wlines.gfa \
  results/C4_TEST/Minigraph/outputs/minigraph_C4_with_plines.gfa

# Checks
grep -E 'Elapsed|Maximum resident|User time|System time' results/C4_TEST/Minigraph/logs/timing.log
```

### LCPan (C4_TEST)

```bash
cd /home/azureuser/constructionBS
./utils/clean_outputs.sh C4_TEST LCPan

# LCPan requires a single-reference FASTA whose header matches the CHROM field of
# the input VCF. For C4_TEST we derive a PanSN-compatible FASTA/VCF pair from PGGB.
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

docker compose run --rm pggb bash -lc \
"samtools faidx /input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa"

/usr/bin/time -v -o input_data/C4_TEST/GRAPH/tmp/pggb_vcf/timing.log -- \
docker compose run --rm pggb bash -lc \
"pggb -i /input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa -n 96 -o /input_data/C4_TEST/GRAPH/tmp/pggb_vcf -V 'GRCh38#0#C4:1000'" \
> input_data/C4_TEST/GRAPH/tmp/pggb_vcf/execution.log 2>&1

cp input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa.*.smooth.final.GRCh38#0#C4.vcf \
  input_data/C4_TEST/GRAPH/lcpan_C4.vcf

docker compose run --rm pggb bash -lc \
"samtools faidx /input_data/C4_TEST/GRAPH/tmp/pggb_vcf/c4_total_pansn.fa 'GRCh38#0#C4' > /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa"

docker compose run --rm pggb bash -lc \
"samtools faidx /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa"

# Required inputs for the actual LCPan run:
test -f input_data/C4_TEST/GRAPH/c4_reference_pansn.fa
test -f input_data/C4_TEST/GRAPH/c4_reference_pansn.fa.fai
test -f input_data/C4_TEST/GRAPH/lcpan_C4.vcf

/usr/bin/time -v -o results/C4_TEST/LCPan/logs/timing.log -- \
docker compose run --rm lcpan bash -lc "/lcpan/bin/lcpan -vg --gfa -t 32 -r /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa -v /input_data/C4_TEST/GRAPH/lcpan_C4.vcf -p /results/C4_TEST/LCPan/outputs/lcpan_C4 && /lcpan/lcpan-merge.sh /results/C4_TEST/LCPan/outputs/lcpan_C4.log" \
> results/C4_TEST/LCPan/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/LCPan
python utils/organize_outputs.py LCPan results/C4_TEST/LCPan/outputs
# Canonical output: results/C4_TEST/LCPan/outputs/lcpan_C4.gfa

# Optional normalization before vg convert:
# LCPan can emit orphan L-lines (for example a single `L 0 ...` link in C4_TEST)
# that `vg convert` rejects. This filter keeps all S/P/W records and only drops
# links whose endpoints are not present as S-segment IDs.
mkdir -p results/C4_TEST/LCPan/outputs/artifacts
awk '
/^S\t/ { ids[$2] = 1; lines[++n] = $0; next }
/^L\t/ { lines[++n] = $0; next }
{ lines[++n] = $0 }
END {
  for (i = 1; i <= n; i++) {
    split(lines[i], f, "\t")
    if (f[1] == "L" && (!(f[2] in ids) || !(f[4] in ids))) continue
    print lines[i]
  }
}
' results/C4_TEST/LCPan/outputs/lcpan_C4.gfa \
> results/C4_TEST/LCPan/outputs/artifacts/lcpan_C4_vg_ready.gfa

# P-lines export from the normalized GFA.
# Write to a temporary file first so failures do not leave a misleading empty
# final output behind.
docker compose run --rm progressivecactus bash -lc \
"vg convert -g -f -W /results/C4_TEST/LCPan/outputs/artifacts/lcpan_C4_vg_ready.gfa > /results/C4_TEST/LCPan/outputs/lcpan_C4_with_plines.gfa.tmp" && \
mv results/C4_TEST/LCPan/outputs/lcpan_C4_with_plines.gfa.tmp \
  results/C4_TEST/LCPan/outputs/lcpan_C4_with_plines.gfa

# W-lines export: keep the original LCPan GFA as the W-lines version because
# `vg convert` is only needed for the P-lines rewrite.
cp results/C4_TEST/LCPan/outputs/lcpan_C4.gfa \
  results/C4_TEST/LCPan/outputs/lcpan_C4_with_wlines.gfa

# Checks
grep -m 5 -v '^#' input_data/C4_TEST/GRAPH/lcpan_C4.vcf
grep -E 'Elapsed|Maximum resident|User time|System time' results/C4_TEST/LCPan/logs/timing.log
ls -lh results/C4_TEST/LCPan/outputs/lcpan_C4_with_wlines.gfa \
  results/C4_TEST/LCPan/outputs/lcpan_C4_with_plines.gfa
```

### PGGB (C4_TEST)

```bash
cd /home/azureuser/constructionBS
./utils/clean_outputs.sh C4_TEST PGGB
cat input_data/C4_TEST/ASSEMBLIES/C4-*.fa > input_data/C4_TEST/ASSEMBLIES/c4_total.fa
docker compose run --rm pggb bash -lc "samtools faidx /input_data/C4_TEST/ASSEMBLIES/c4_total.fa"
/usr/bin/time -v -o results/C4_TEST/PGGB/logs/timing.log -- \
docker compose run --rm pggb bash -lc "pggb -i /input_data/C4_TEST/ASSEMBLIES/c4_total.fa -n 96 -o /results/C4_TEST/PGGB/outputs" \
> results/C4_TEST/PGGB/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/PGGB
python utils/organize_outputs.py PGGB results/C4_TEST/PGGB/outputs
# Canonical output: results/C4_TEST/PGGB/outputs/pggb_C4.gfa

# Derived encodings from PGGB canonical GFA (canonical already uses P-lines)
cp results/C4_TEST/PGGB/outputs/pggb_C4.gfa \
  results/C4_TEST/PGGB/outputs/pggb_C4_with_plines.gfa
docker compose run --rm progressivecactus bash -lc "vg convert -g -f /results/C4_TEST/PGGB/outputs/pggb_C4.gfa > /results/C4_TEST/PGGB/outputs/pggb_C4_with_wlines.gfa"
sudo chown $USER:$USER \
  results/C4_TEST/PGGB/outputs/pggb_C4.gfa \
  results/C4_TEST/PGGB/outputs/pggb_C4_with_wlines.gfa \
  results/C4_TEST/PGGB/outputs/pggb_C4_with_plines.gfa

# Checks
grep -E 'Elapsed|Maximum resident|User time|System time' results/C4_TEST/PGGB/logs/timing.log
```

### MinigraphCactus (C4_TEST)

```bash
cd /home/azureuser/constructionBS
./utils/clean_outputs.sh C4_TEST MinigraphCactus
python utils/make_minigraphcactus_seqfile.py C4_TEST
/usr/bin/time -v -o results/C4_TEST/MinigraphCactus/logs/timing.log -- \
docker compose run --rm minigraphcactus bash -lc "cactus-pangenome /results/C4_TEST/MinigraphCactus/outputs/jobstore /results/C4_TEST/MinigraphCactus/outputs/c4_test_seqfile.txt --outDir /results/C4_TEST/MinigraphCactus/outputs --outName minigraphcactus_C4 --reference C4-GRCh38 --gfa clip --batchSystem single_machine --maxCores 32" \
> results/C4_TEST/MinigraphCactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/MinigraphCactus
python utils/organize_outputs.py MinigraphCactus results/C4_TEST/MinigraphCactus/outputs
# Canonical outputs:
# - results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa.gz
# - results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa

# Derived encodings from MinigraphCactus canonical GFA (canonical already uses W-lines)
cp results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa \
  results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_with_wlines.gfa
docker compose run --rm minigraphcactus bash -lc "vg convert -g -f -W /results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa > /results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_with_plines.gfa"
sudo chown $USER:$USER \
  results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa \
  results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_with_wlines.gfa \
  results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_with_plines.gfa

# Checks
grep -E 'Elapsed|Maximum resident|User time|System time' results/C4_TEST/MinigraphCactus/logs/timing.log
```

### Cactus (C4_TEST)

```bash
cd /home/azureuser/constructionBS
./utils/clean_outputs.sh C4_TEST Cactus
python utils/make_cactus_seqfile.py C4_TEST
/usr/bin/time -v -o results/C4_TEST/Cactus/logs/timing.log -- \
docker compose run --rm cactus bash -lc "cactus /results/C4_TEST/Cactus/outputs/jobstore /results/C4_TEST/Cactus/outputs/c4_test_seqfile.txt /results/C4_TEST/Cactus/outputs/cactus_C4.hal --batchSystem single_machine --maxCores 32" \
> results/C4_TEST/Cactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/Cactus
python utils/organize_outputs.py Cactus results/C4_TEST/Cactus/outputs

# Export to VG/GFA from the HAL output.
# organize_outputs.py normalizes and preserves these files if they already
# exist, but it does not perform the HAL -> VG/GFA conversion itself.
docker compose run --rm cactus bash -lc "hal2vg /results/C4_TEST/Cactus/outputs/cactus_C4.hal > /results/C4_TEST/Cactus/outputs/cactus_C4.vg"
docker compose run --rm cactus bash -lc "vg view -g /results/C4_TEST/Cactus/outputs/cactus_C4.vg > /results/C4_TEST/Cactus/outputs/cactus_C4.gfa"
# Canonical output: results/C4_TEST/Cactus/outputs/cactus_C4.gfa

# Derived encodings from Cactus canonical GFA (canonical already uses W-lines)
cp results/C4_TEST/Cactus/outputs/cactus_C4.gfa \
  results/C4_TEST/Cactus/outputs/cactus_C4_with_wlines.gfa
docker compose run --rm progressivecactus bash -lc "vg convert -g -f -W /results/C4_TEST/Cactus/outputs/cactus_C4.gfa > /results/C4_TEST/Cactus/outputs/cactus_C4_with_plines.gfa"
sudo chown -R $USER:$USER results/C4_TEST/Cactus

# Checks
grep -E 'Elapsed|Maximum resident|User time|System time' results/C4_TEST/Cactus/logs/timing.log
```

### ProgressiveCactus (C4_TEST)

```bash
cd /home/azureuser/constructionBS
./utils/clean_outputs.sh C4_TEST ProgressiveCactus
python utils/make_cactus_seqfile.py C4_TEST --output results/C4_TEST/ProgressiveCactus/outputs/c4_test_seqfile.txt
/usr/bin/time -v -o results/C4_TEST/ProgressiveCactus/logs/timing.log -- \
docker compose run --rm progressivecactus bash -lc "cactus /results/C4_TEST/ProgressiveCactus/outputs/jobstore /results/C4_TEST/ProgressiveCactus/outputs/c4_test_seqfile.txt /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.hal --batchSystem single_machine --maxCores 32" \
> results/C4_TEST/ProgressiveCactus/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/ProgressiveCactus
python utils/organize_outputs.py ProgressiveCactus results/C4_TEST/ProgressiveCactus/outputs

# Export to VG/GFA from the HAL output.
# organize_outputs.py normalizes and preserves these files if they already
# exist, but it does not perform the HAL -> VG/GFA conversion itself.
docker compose run --rm progressivecactus bash -lc "hal2vg /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.hal > /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.vg"
docker compose run --rm progressivecactus bash -lc "vg view -g /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.vg > /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.gfa"
# Canonical output: results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.gfa

# Derived encodings from ProgressiveCactus canonical GFA (canonical already uses W-lines)
cp results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.gfa results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4_with_wlines.gfa
docker compose run --rm progressivecactus bash -lc "vg convert -g -f -W /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.gfa > /results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4_with_plines.gfa"
sudo chown -R $USER:$USER results/C4_TEST/ProgressiveCactus

# Checks
grep -E 'Elapsed|Maximum resident|User time|System time' results/C4_TEST/ProgressiveCactus/logs/timing.log
```

## Stable Docker Paths (Required)

When running conversion or post-processing commands, always target files via
container-absolute paths under `/results`.

Template:

```bash
docker compose run --rm <service> bash -lc \
'<command> /results/<DATASET>/<TOOL>/outputs/<input.gfa> > /results/<DATASET>/<TOOL>/outputs/<output.gfa>'
```

Example (`MinigraphCactus`, C4):

```bash
docker compose run --rm minigraphcactus bash -lc \
'vg convert -g -f -W /results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa > /results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_with_plines.gfa'
```

## Quick Troubleshooting

- `FileNotFoundError: no final output matching '*.hal'`:
  run failed before HAL creation; inspect `results/<DATASET>/Cactus/logs/execution.log`.

- `ProgressiveCactus` rerun fails with `Permission denied`:
  fix ownership or remove `results/<DATASET>/ProgressiveCactus/outputs/jobstore`
  before retrying.

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
