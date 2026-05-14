# Runbook Commands

Last validated: 2026-04-30

This file collects copy-paste commands used to run graph-construction tools in this repository.

Conventions:
- Run from repo root: `/home/azureuser/constructionBS`
- Standard flow: `clean -> run -> chown -> organize`
- `execution.log` and `timing.log` are written either under `results/<DATASET>/<TOOL>/logs` or, for LCPan variants, under `results/<DATASET>/LCPan/<variant>/logs`
- LCPan variant runs use explicit subdirectories under `results/<DATASET>/LCPan/`: `pggb_vg`, `pggb_vgx`, `mc_vg`, `mc_vgx`
- In summaries and prose, use branch names `pggb_vg`, `pggb_vgx`, `from_MC_vg`, `from_MC_vgx` (where `from_MC_vg -> mc_vg` path and `from_MC_vgx -> mc_vgx` path)
- `MC_vg` is a standalone tool under `results/<DATASET>/MC_vg`
- `results/<DATASET>/LCPan/mc_vg` and `results/<DATASET>/LCPan/mc_vgx` are downstream LCPan variants built from `MC_vg` outputs, not aliases of the `MC_vg` tool itself
- In prose and summaries, prefer the clearer labels `from_MC_vg` and `from_MC_vgx` for those two branches.
- Within LCPan, `pggb_vg` is the standard top-level branch, `pggb_vgx` is its expanded-graph sibling branch, and `from_MC_vg` / `from_MC_vgx` are downstream LCPan branches built from `MC_vg` outputs

Path and logging policy (always apply):
- Launch every `docker compose` command from repo root: `/home/azureuser/constructionBS`
- Inside containers, use only absolute mounted paths (`/results/...`, `/input_data/...`)
- Never use relative container paths for graph files (for example `minigraphcactus_C4.gfa`)
- Use `/usr/bin/time -v -o ... -- docker compose ...` for all tools to keep `timing.log` format uniform

Optional metadata overrides (safe, opt-in only):
- Existing validated workflows do not need any metadata changes.
- For future datasets that should not depend on historical naming, `input_data/<DATASET>/META/dataset_info.yml` may define:
  - `dataset_short`
  - `lcpan.reference_fasta`
  - `lcpan.variants_vcf`
  - `reference_name`
- These keys only act as overrides when present; if absent, all current commands and fallbacks remain unchanged.
- Keep override targets inside `input_data/<DATASET>/...`; this preserves the current structure checks, mounted paths, and rerun behavior.

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
- `results/<DATASET>/pggb_timing_summary.md`
- `results/<DATASET>/minigraph_timing_summary.md`
- `results/<DATASET>/lcpan_timing_summary.md`

Canonical-output rule:
- The only canonical graph outputs for cross-tool comparisons and `output_summary.md` are the primary `.gfa` files produced by each validated run.
- Derived files such as `_with_plines.gfa`, `_with_wlines.gfa`, temporary files, normalization artifacts, and conversion byproducts are support artifacts only.
- Timing summaries may still mention repeated runs or variants, but that does not promote their derived files to canonical dataset outputs.
- For LCPan specifically, branch names such as `pggb_vg`, `pggb_vgx`, `from_MC_vg`, and `from_MC_vgx` identify variants of the same tool, not separate top-level tools.
- `organize_outputs.py` and `summarize_output_graphs.py` prefer `dataset_short` from metadata when available; otherwise they keep the legacy `_TEST -> short token` fallback.

The extra timing summaries are additive:
- `timing_summary.md` stays the dataset-wide cross-tool report
- `pggb_timing_summary.md`, `minigraph_timing_summary.md`, and `lcpan_timing_summary.md` are tool-specific reports for repeated runs, including multithread studies

## Multithread Study Layout

Use dedicated run folders under `threads/` so the canonical outputs of the validated commands stay untouched.

Recommended layout:
- `results/<DATASET>/PGGB/threads/t8/{logs,outputs}`
- `results/<DATASET>/Minigraph/threads/t8/{logs,outputs}`
- `results/<DATASET>/LCPan/pggb_vg/threads/t8/{logs,outputs}`
- `results/<DATASET>/LCPan/pggb_vgx/threads/t8/{logs,outputs}`

Suggested workflow:
1. Keep the standard commands below as the reference run.
2. For multithread experiments, write logs and outputs inside `threads/t<THREADS>/`.
3. Re-run `python utils/summarize_timing_logs.py <DATASET>` to refresh both the original dataset summary and the new per-tool summaries.

Current validation status (2026-05-12):
- `PGGB`: validated in practice; thread studies exist in `results/C4_TEST/PGGB/threads/`, `results/KIR_TEST/PGGB/threads/`, and `results/MHC_TEST/PGGB/threads/`.
- `Minigraph`: not yet validated as a multithread workflow; current `C4_TEST` thread runs exit with status `1` and `failed to load the graph from file '/input_data/C4_TEST/ASSEMBLIES/C4-00GRCh38.fa'`.
- `LCPan`: template prepared, but no validated `threads/` study is documented yet.

## Multithread Study Commands

### PGGB Multithread Template

```bash
cd /home/azureuser/constructionBS
DATASET="C4_TEST"
THREADS="32"
INPUT_FASTA="/input_data/${DATASET}/ASSEMBLIES/c4_total.fa"
RUN_DIR="results/${DATASET}/PGGB/threads/t${THREADS}"

mkdir -p "${RUN_DIR}/outputs" "${RUN_DIR}/logs"
sudo chown -R $USER:$USER "${RUN_DIR}"

/usr/bin/time -v -o "${RUN_DIR}/logs/timing.log" -- \
docker compose run --rm pggb bash -lc "pggb -i ${INPUT_FASTA} -n 96 -t ${THREADS} -o /${RUN_DIR}/outputs" \
> "${RUN_DIR}/logs/execution.log" 2>&1

sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/summarize_timing_logs.py "${DATASET}"
```

### Minigraph Multithread Template (Unvalidated)

```bash
cd /home/azureuser/constructionBS
DATASET="C4_TEST"
THREADS="32"
INPUT_GLOB="/input_data/${DATASET}/ASSEMBLIES/C4-*.fa"
OUTPUT_GRAPH="minigraph_C4.gfa"
RUN_DIR="results/${DATASET}/Minigraph/threads/t${THREADS}"

mkdir -p "${RUN_DIR}/outputs" "${RUN_DIR}/logs"
sudo chown -R $USER:$USER "${RUN_DIR}"

/usr/bin/time -v -o "${RUN_DIR}/logs/timing.log" -- \
docker compose run --rm minigraph bash -lc "cd /minigraph && ./minigraph -x ggs -c -t ${THREADS} ${INPUT_GLOB} > /${RUN_DIR}/outputs/${OUTPUT_GRAPH}" \
> "${RUN_DIR}/logs/execution.log" 2>&1

sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/summarize_timing_logs.py "${DATASET}"
```

### LCPan Multithread Template

```bash
cd /home/azureuser/constructionBS
DATASET="C4_TEST"
THREADS="32"
VARIANT="pggb_vg"  # or pggb_vgx
MODE_FLAG="-vg"    # or -vgx
REFERENCE_FASTA="/input_data/${DATASET}/GRAPH/c4_reference_pansn.fa"
INPUT_VCF="/input_data/${DATASET}/GRAPH/lcpan_C4.vcf"
OUTPUT_PREFIX="lcpan_C4"
RUN_DIR="results/${DATASET}/LCPan/${VARIANT}/threads/t${THREADS}"

mkdir -p "${RUN_DIR}/outputs" "${RUN_DIR}/logs"
sudo chown -R $USER:$USER "${RUN_DIR}"

/usr/bin/time -v -o "${RUN_DIR}/logs/timing.log" -- \
docker compose run --rm lcpan bash -lc "/lcpan/bin/lcpan ${MODE_FLAG} --gfa -t ${THREADS} -r ${REFERENCE_FASTA} -v ${INPUT_VCF} -p /${RUN_DIR}/outputs/${OUTPUT_PREFIX} && /lcpan/lcpan-merge.sh /${RUN_DIR}/outputs/${OUTPUT_PREFIX}.log" \
> "${RUN_DIR}/logs/execution.log" 2>&1

sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/summarize_timing_logs.py "${DATASET}"
```

## C4 End-to-End Commands By Tool

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
```

### LCPan PGGB vg (C4_TEST)

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

/usr/bin/time -v -o results/C4_TEST/LCPan/pggb_vg/logs/timing.log -- \
docker compose run --rm lcpan bash -lc "/lcpan/bin/lcpan -vg --gfa -t 32 -r /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa -v /input_data/C4_TEST/GRAPH/lcpan_C4.vcf -p /results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4 && /lcpan/lcpan-merge.sh /results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4.log" \
> results/C4_TEST/LCPan/pggb_vg/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/LCPan
python utils/organize_outputs.py LCPan results/C4_TEST/LCPan/pggb_vg/outputs
# Canonical output: results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4.gfa

# Optional normalization before vg convert:
# LCPan can emit orphan L-lines (for example a single `L 0 ...` link in C4_TEST)
# that `vg convert` rejects. This filter keeps all S/P/W records and only drops
# links whose endpoints are not present as S-segment IDs.
mkdir -p results/C4_TEST/LCPan/pggb_vg/outputs/artifacts
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
' results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4.gfa \
> results/C4_TEST/LCPan/pggb_vg/outputs/artifacts/lcpan_C4_vg_ready.gfa

docker compose run --rm progressivecactus bash -lc \
"vg convert -g -f -W /results/C4_TEST/LCPan/pggb_vg/outputs/artifacts/lcpan_C4_vg_ready.gfa > /results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4_with_plines.gfa.tmp" && \
mv results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4_with_plines.gfa.tmp \
  results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4_with_plines.gfa

cp results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4.gfa \
  results/C4_TEST/LCPan/pggb_vg/outputs/lcpan_C4_with_wlines.gfa
```

### LCPan PGGB vgx (C4_TEST)

```bash
cd /home/azureuser/constructionBS

# Keep the standard LCPan inputs and write the expanded-graph run
# to its dedicated `pggb_vgx` folder.
mkdir -p results/C4_TEST/LCPan/pggb_vgx/{outputs,logs}
sudo chown -R $USER:$USER results/C4_TEST/LCPan

/usr/bin/time -v -o results/C4_TEST/LCPan/pggb_vgx/logs/timing.log -- \
docker compose run --rm lcpan bash -lc "/lcpan/bin/lcpan -vgx --gfa -t 32 -r /input_data/C4_TEST/GRAPH/c4_reference_pansn.fa -v /input_data/C4_TEST/GRAPH/lcpan_C4.vcf -p /results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4 && /lcpan/lcpan-merge.sh /results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4.log" \
> results/C4_TEST/LCPan/pggb_vgx/logs/execution.log 2>&1

sudo chown -R $USER:$USER results/C4_TEST/LCPan

# Canonical output:
# - results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4.gfa

# Optional normalization before vg convert:
# The same orphan-link cleanup used for vg mode can be applied here before
# exporting an alternative P-lines encoding.
mkdir -p results/C4_TEST/LCPan/pggb_vgx/outputs/artifacts
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
' results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4.gfa \
> results/C4_TEST/LCPan/pggb_vgx/outputs/artifacts/lcpan_C4_vg_ready.gfa

docker compose run --rm progressivecactus bash -lc \
"vg convert -g -f -W /results/C4_TEST/LCPan/pggb_vgx/outputs/artifacts/lcpan_C4_vg_ready.gfa > /results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4_with_plines.gfa.tmp" && \
mv results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4_with_plines.gfa.tmp \
  results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4_with_plines.gfa

cp results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4.gfa \
  results/C4_TEST/LCPan/pggb_vgx/outputs/lcpan_C4_with_wlines.gfa
```

### PGGB (C4_TEST)

```bash
cd /home/azureuser/constructionBS
THREADS="${THREADS:-16}"
./utils/clean_outputs.sh C4_TEST PGGB
cat input_data/C4_TEST/ASSEMBLIES/C4-*.fa > input_data/C4_TEST/ASSEMBLIES/c4_total.fa
docker compose run --rm pggb bash -lc "samtools faidx /input_data/C4_TEST/ASSEMBLIES/c4_total.fa"
/usr/bin/time -v -o results/C4_TEST/PGGB/logs/timing.log -- \
docker compose run --rm pggb bash -lc "pggb -i /input_data/C4_TEST/ASSEMBLIES/c4_total.fa -n 96 -t ${THREADS} -o /results/C4_TEST/PGGB/outputs" \
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
```

### MC_vg (Parameterized)

```bash
cd /home/azureuser/constructionBS

# Configuration: change only these variables for the current dataset.
DATASET="KIR_TEST"
TOOL_NAME="MC_vg"
SEQFILE_NAME="kir_test_seqfile.txt"
REFERENCE_NAME="KIR-GRCh38"
REFERENCE_FASTA="input_data/KIR_TEST/ASSEMBLIES/KIR-00GRCh38.fa"
OUT_NAME="result_cactus_new"
AUTOINDEX_PREFIX="result_autoindex"
MAX_CORES="16"

# C4_TEST note:
# - use SEQFILE_NAME="c4_test_seqfile.txt"
# - use REFERENCE_NAME="C4-GRCh38"
# - use REFERENCE_FASTA="input_data/C4_TEST/ASSEMBLIES_CACTUS_SANITIZED/C4-00GRCh38.fa"
# The C4_TEST ASSEMBLIES directory can contain placeholder symlinks, while
# ASSEMBLIES_CACTUS_SANITIZED contains the real FASTA files used by Cactus.

RUN_DIR="results/${DATASET}/${TOOL_NAME}"
OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
SEQFILE_PATH="${RUN_DIR}/${SEQFILE_NAME}"
ARTIFACTS_DIR="${RUN_DIR}/artifacts"

mkdir -p "${OUTPUT_DIR}" "${LOG_DIR}"
sudo chown -R $USER:$USER "${RUN_DIR}"

python utils/make_minigraphcactus_seqfile.py "${DATASET}" \
  --output "${SEQFILE_PATH}"

# Run cactus-pangenome
/usr/bin/time -v \
  -o "${LOG_DIR}/timing_cactus_pangenome.log" -- \
docker compose run --rm minigraphcactus bash -lc \
"cactus-pangenome \
 /${RUN_DIR}/jobstore \
 /${SEQFILE_PATH} \
 --outDir /${OUTPUT_DIR} \
 --outName ${OUT_NAME} \
 --reference ${REFERENCE_NAME} \
 --vcf --giraffe --gfa --gbz \
 --batchSystem single_machine \
 --maxCores ${MAX_CORES}" \
> "${LOG_DIR}/execution_cactus_pangenome.log" 2>&1

sudo chown -R $USER:$USER "${RUN_DIR}"

# Build the reference FASTA for vg autoindex.
# The FASTA header must match the contig name used in the cactus-produced VCF,
# so derive it dynamically instead of hardcoding dataset-specific values.
VCF_CONTIG="$(
  gzip -dc "${OUTPUT_DIR}/${OUT_NAME}.vcf.gz" \
  | awk -F'[=,>]' '/^##contig=<ID=/{print $3; exit}'
)"

awk -v contig="$VCF_CONTIG" 'NR==1{print ">" contig; next} {print}' \
"${REFERENCE_FASTA}" \
> "${OUTPUT_DIR}/result_autoindex_ref.fa"

# Run vg autoindex as a secondary, reference-centric indexing branch.
/usr/bin/time -v \
  -o "${LOG_DIR}/timing_vg_autoindex.log" -- \
docker compose run --rm minigraphcactus bash -lc \
"vg autoindex \
 --workflow sr-giraffe \
 --prefix /${OUTPUT_DIR}/${AUTOINDEX_PREFIX} \
 --ref-fasta /${OUTPUT_DIR}/result_autoindex_ref.fa \
 --vcf /${OUTPUT_DIR}/${OUT_NAME}.vcf.gz \
 --threads ${MAX_CORES}" \
> "${LOG_DIR}/execution_vg_autoindex.log" 2>&1

sudo chown -R $USER:$USER "${RUN_DIR}"

# Export the autoindex graph as GFA, then unchop it with vg mod -u.
# Write to temporary files first so failed commands do not leave misleading
# final outputs behind.
docker compose run --rm minigraphcactus bash -lc \
"vg convert -f \
 /${OUTPUT_DIR}/${AUTOINDEX_PREFIX}.giraffe.gbz \
 > /${OUTPUT_DIR}/result_autoindex_c.gfa.tmp"
mv "${OUTPUT_DIR}/result_autoindex_c.gfa.tmp" \
  "${OUTPUT_DIR}/result_autoindex_c.gfa"

docker compose run --rm minigraphcactus bash -lc \
"vg mod -u \
 /${OUTPUT_DIR}/result_autoindex_c.gfa \
 > /${OUTPUT_DIR}/result_autoindex.gfa.tmp"
mv "${OUTPUT_DIR}/result_autoindex.gfa.tmp" \
  "${OUTPUT_DIR}/result_autoindex.gfa"

sudo chown -R $USER:$USER "${RUN_DIR}"

# Create an editor-friendly uncompressed copy of the cactus GFA.
gzip -dc "${OUTPUT_DIR}/${OUT_NAME}.gfa.gz" \
  > "${OUTPUT_DIR}/${OUT_NAME}.gfa"

# Final organization:
# - keep the main cactus outputs, primary indices, and the three readable GFAs
#   in outputs
# - move diagnostic and secondary files into artifacts
mkdir -p "${ARTIFACTS_DIR}"

mv \
  "${OUTPUT_DIR}/${OUT_NAME}.raw.vcf.gz" \
  "${OUTPUT_DIR}/${OUT_NAME}.raw.vcf.gz.tbi" \
  "${OUTPUT_DIR}/${OUT_NAME}.full.hal" \
  "${OUTPUT_DIR}/${OUT_NAME}.gaf.gz" \
  "${OUTPUT_DIR}/${OUT_NAME}.paf" \
  "${OUTPUT_DIR}/${OUT_NAME}.paf.unfiltered.gz" \
  "${OUTPUT_DIR}/${OUT_NAME}.paf.filter.log" \
  "${OUTPUT_DIR}/${OUT_NAME}.snarls" \
  "${OUTPUT_DIR}/${OUT_NAME}.stats.tgz" \
  "${OUTPUT_DIR}/${OUT_NAME}.sv.gfa.gz" \
  "${OUTPUT_DIR}/${OUT_NAME}.sv.gfa.fa.gz" \
  "${OUTPUT_DIR}/${OUT_NAME}.d2.gbz" \
  "${ARTIFACTS_DIR}/"

mv \
  "${OUTPUT_DIR}/chrom-alignments" \
  "${OUTPUT_DIR}/chrom-subproblems" \
  "${ARTIFACTS_DIR}/"
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
```

### LCPan MC vg/vgx (Parameterized)

```bash
cd /home/azureuser/constructionBS

# Configuration: change only these variables for the current dataset.
DATASET="KIR_TEST"
REFERENCE_FASTA_SOURCE="input_data/${DATASET}/ASSEMBLIES/KIR-00GRCh38.fa"
CACTUS_VCF_GZ="results/${DATASET}/MC_vg/outputs/result_cactus_new.vcf.gz"

LCPAN_DIR="results/${DATASET}/LCPan"
MC_VG_RUN_DIR="${LCPAN_DIR}/mc_vg"
MC_VGX_RUN_DIR="${LCPAN_DIR}/mc_vgx"

REF_FASTA_FOR_LCPAN="${LCPAN_DIR}/inputs/reference_from_cactus.fa"
VCF_FOR_LCPAN="${LCPAN_DIR}/inputs/variants_from_cactus.vcf"

VG_OUTPUT_DIR="${MC_VG_RUN_DIR}/outputs"
VG_LOG_DIR="${MC_VG_RUN_DIR}/logs"
VGX_OUTPUT_DIR="${MC_VGX_RUN_DIR}/outputs"
VGX_LOG_DIR="${MC_VGX_RUN_DIR}/logs"

mkdir -p \
  "${LCPAN_DIR}/inputs" \
  "${VG_OUTPUT_DIR}" \
  "${VG_LOG_DIR}" \
  "${VGX_OUTPUT_DIR}" \
  "${VGX_LOG_DIR}"
sudo chown -R $USER:$USER "${LCPAN_DIR}"

VCF_CONTIG="$(
  gzip -dc "${CACTUS_VCF_GZ}" \
  | awk -F'[=,>]' '/^##contig=<ID=/{print $3; exit}'
)"

awk -v contig="${VCF_CONTIG}" 'NR==1{print ">" contig; next} {print}' \
  "${REFERENCE_FASTA_SOURCE}" \
  > "${REF_FASTA_FOR_LCPAN}"

docker compose run --rm pggb bash -lc \
"samtools faidx /${REF_FASTA_FOR_LCPAN}"

gzip -dc "${CACTUS_VCF_GZ}" > "${VCF_FOR_LCPAN}"

/usr/bin/time -v -o "${VG_LOG_DIR}/timing.log" -- \
docker compose run --rm lcpan bash -lc \
"/lcpan/bin/lcpan -vg --gfa -t 32 \
 -r /${REF_FASTA_FOR_LCPAN} \
 -v /${VCF_FOR_LCPAN} \
 -p /${VG_OUTPUT_DIR}/lcpan_from_cactus \
 && /lcpan/lcpan-merge.sh /${VG_OUTPUT_DIR}/lcpan_from_cactus.log" \
> "${VG_LOG_DIR}/execution.log" 2>&1

mkdir -p "${VG_OUTPUT_DIR}/artifacts"
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
' "${VG_OUTPUT_DIR}/lcpan_from_cactus.gfa" \
> "${VG_OUTPUT_DIR}/artifacts/lcpan_from_cactus_vg_ready.gfa"

docker compose run --rm progressivecactus bash -lc \
"vg convert -g -f -W /${VG_OUTPUT_DIR}/artifacts/lcpan_from_cactus_vg_ready.gfa > /${VG_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp"
mv "${VG_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp" \
  "${VG_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa"
cp "${VG_OUTPUT_DIR}/lcpan_from_cactus.gfa" \
  "${VG_OUTPUT_DIR}/lcpan_from_cactus_with_wlines.gfa"

/usr/bin/time -v -o "${VGX_LOG_DIR}/timing.log" -- \
docker compose run --rm lcpan bash -lc \
"/lcpan/bin/lcpan -vgx --gfa -t 32 \
 -r /${REF_FASTA_FOR_LCPAN} \
 -v /${VCF_FOR_LCPAN} \
 -p /${VGX_OUTPUT_DIR}/lcpan_from_cactus \
 && /lcpan/lcpan-merge.sh /${VGX_OUTPUT_DIR}/lcpan_from_cactus.log" \
> "${VGX_LOG_DIR}/execution.log" 2>&1

mkdir -p "${VGX_OUTPUT_DIR}/artifacts"
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
' "${VGX_OUTPUT_DIR}/lcpan_from_cactus.gfa" \
> "${VGX_OUTPUT_DIR}/artifacts/lcpan_from_cactus_vg_ready.gfa"

docker compose run --rm progressivecactus bash -lc \
"vg convert -g -f -W /${VGX_OUTPUT_DIR}/artifacts/lcpan_from_cactus_vg_ready.gfa > /${VGX_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp"
mv "${VGX_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp" \
  "${VGX_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa"
cp "${VGX_OUTPUT_DIR}/lcpan_from_cactus.gfa" \
  "${VGX_OUTPUT_DIR}/lcpan_from_cactus_with_wlines.gfa"

sudo chown -R $USER:$USER "${LCPAN_DIR}"
```

- Permission issues after container runs:
  ```bash
  sudo chown -R $USER:$USER results/<DATASET>/<TOOL>
  ```
