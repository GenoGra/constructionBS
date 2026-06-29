# Runbook Commands

Last validated: 2026-06-19

This file collects copy-paste commands used to run graph-construction tools in this repository.

Conventions:
- Run from repo root: `/home/azureuser/constructionBS`
- Standard flow: `clean -> run -> chown -> organize`
- `execution.log` and `timing.log` are written under `results/<DATASET>/<TOOL>/logs`
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


Input-layout policy for assembly datasets:
- `input_data/<DATASET>/ASSEMBLIES/` contains only primary per-sample FASTA inputs.
- `input_data/<DATASET>/ASSEMBLIES_CACTUS_SANITIZED/` contains only sanitized
  copies of those same primary assemblies for Cactus-family workflows.
- `C4_TEST` is a validated historical exception: `ASSEMBLIES/` is currently a
  symlink-based view of `ASSEMBLIES_CACTUS_SANITIZED/`, so the visible primary
  inputs there are already the sanitized files.
- `input_data/<DATASET>/AUXILIARY_INPUTS/` stores helper FASTA files that must
  not be treated as runnable assemblies, including `*_total.fa`,
  `*_total_pansn.fa`, `*_reference.fa`, `*_queries.fa`, and original
  multi-FASTA helper inputs.
- Seqfile generators are expected to ignore those helper files.

Graph-visualization normalization policy:
- Never overwrite the canonical graph output from a validated run.
- If a viewer needs the reference as a `P`-line, write a derived GFA just for
  visualization.
- For `Cactus`, `ProgressiveCactus`, and `MinigraphCactus`, replace only the
  reference `W` with a `P`; leave every other sample `W` unchanged.
- For `Minigraph`, derive only the reference path from the rGFA backbone tags
  (`vg convert -g -r 0 ...`); sample paths are not recoverable from the
  canonical rGFA.
- For `LCPan`, current outputs preserve the reference `P` but not sample `W`
  records, so sample `P` records are not derivable from the current GFA files.

Optional metadata overrides (safe, opt-in only):
- Existing validated workflows do not need any metadata changes.
- For future datasets that should not depend on historical naming, `input_data/<DATASET>/META/dataset_info.yml` may define:
  - `dataset_short`
  - `lcpan.reference_fasta`
  - `lcpan.variants_vcf`
  - `reference_name`
- These keys only act as overrides when present; if absent, all current commands and fallbacks remain unchanged.
- Keep override targets inside `input_data/<DATASET>/...`; this preserves the current structure checks, mounted paths, and rerun behavior.

`GRAPH/` policy for validated assembly datasets:
- keep official `LCPan` runtime inputs there: `lcpan_*.vcf`, `*_reference_pansn.fa`, and their indexes
- keep temporary derivation work under `GRAPH/tmp/` only as non-canonical build scratch space
- keep concatenated and helper FASTA files in `AUXILIARY_INPUTS/`, not in `GRAPH/`

## Common Setup

```bash
cd /home/azureuser/constructionBS
```

## LCPan Layout Migration (Legacy -> Canonical)

Use this when a dataset still has legacy LCPan folders such as `outputs`,
`outputs_vgx`, `logs`, `logs_vgx`, or `cactus_vcf_test/...`.

```bash
cd /home/azureuser/constructionBS
python -m utils.results_layout migrate-lcpan C4_TEST --dry-run
python -m utils.results_layout migrate-lcpan C4_TEST
```

Canonical target layout:
- `results/<DATASET>/LCPan/pggb_vg/{outputs,logs}`
- `results/<DATASET>/LCPan/pggb_vgx/{outputs,logs}`
- `results/<DATASET>/LCPan/mc_vg/{outputs,logs}`
- `results/<DATASET>/LCPan/mc_vgx/{outputs,logs}`

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
- Timing summaries may still mention repeated runs or variants, but that does not promote their derived files to canonical dataset outputs.
- For LCPan specifically, branch names such as `pggb_vg`, `pggb_vgx`, `from_MC_vg`, and `from_MC_vgx` identify variants of the same tool, not separate top-level tools.
- `organize_outputs.py` and `summarize_output_graphs.py` prefer `dataset_short` from metadata when available; otherwise they keep the legacy `_TEST -> short token` fallback.
- `timing_summary.md` stays the dataset-wide cross-tool report

## Parameterized Commands By Tool

The sections below are written to be copy-paste friendly across datasets while
preserving the same result layout used by `C4_TEST`.

---

### Minigraph (Parameterized)

```bash
cd /home/azureuser/constructionBS

DATASET="C4_TEST"
DATASET_SHORT="C4"          # e.g. C4, KIR, MHC
TOOL="Minigraph"
ASSEMBLY_GLOB="/input_data/${DATASET}/ASSEMBLIES/${DATASET_SHORT}-*.fa"
RUN_DIR="results/${DATASET}/${TOOL}"
OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
CANONICAL_GFA="${OUTPUT_DIR}/minigraph_${DATASET_SHORT}.gfa"

mkdir -p "${LOG_DIR}" "${OUTPUT_DIR}"
./utils/clean_outputs.sh "${DATASET}" "${TOOL}"
/usr/bin/time -v -o "${LOG_DIR}/timing.log" -- docker compose run --rm minigraph bash -lc "cd /minigraph && ./minigraph -cxggs ${ASSEMBLY_GLOB} > ${CANONICAL_GFA}" > "${LOG_DIR}/execution.log" 2>&1
sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/organize_outputs.py "${TOOL}" "${OUTPUT_DIR}"
# Canonical output: ${CANONICAL_GFA}

# Derived outputs (optional, keep the canonical rGFA unchanged):
# - ${OUTPUT_DIR}/minigraph_${DATASET_SHORT}_with_wlines.gfa
# - ${OUTPUT_DIR}/minigraph_${DATASET_SHORT}_with_plines.gfa
# These recover only the reference backbone (rank 0), not sample paths.
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f /${CANONICAL_GFA} > /${OUTPUT_DIR}/minigraph_${DATASET_SHORT}_with_wlines.gfa"
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f -W /${CANONICAL_GFA} > /${OUTPUT_DIR}/minigraph_${DATASET_SHORT}_with_plines.gfa"
sudo chown $USER:$USER   "${OUTPUT_DIR}/minigraph_${DATASET_SHORT}_with_wlines.gfa"   "${OUTPUT_DIR}/minigraph_${DATASET_SHORT}_with_plines.gfa"
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

---

### LCPan PGGB vg/vgx (Parameterized)

```bash
cd /home/azureuser/constructionBS

DATASET="C4_TEST"
DATASET_SHORT="C4"      # e.g. C4, KIR, MHC
THREADS="32"
VARIANT="pggb_vg"       # pggb_vg or pggb_vgx
MODE_FLAG="-vg"         # -vg for pggb_vg, -vgx for pggb_vgx
REFERENCE_FASTA="/input_data/${DATASET}/GRAPH/${DATASET_SHORT,,}_reference_pansn.fa"
INPUT_VCF="/input_data/${DATASET}/GRAPH/lcpan_${DATASET_SHORT}.vcf"

LCPAN_DIR="results/${DATASET}/LCPan"
RUN_DIR="${LCPAN_DIR}/${VARIANT}"
OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
OUT_PREFIX="/results/${DATASET}/LCPan/${VARIANT}/outputs/lcpan_${DATASET_SHORT}"
CANONICAL_GFA="${OUTPUT_DIR}/lcpan_${DATASET_SHORT}.gfa"

mkdir -p "${OUTPUT_DIR}" "${LOG_DIR}"
sudo chown -R $USER:$USER "${LCPAN_DIR}"

/usr/bin/time -v -o "${LOG_DIR}/timing.log" -- \
docker compose run --rm lcpan bash -lc \
"/lcpan/bin/lcpan ${MODE_FLAG} --gfa -t ${THREADS} -r ${REFERENCE_FASTA} -v ${INPUT_VCF} -p ${OUT_PREFIX} && /lcpan/lcpan-merge.sh ${OUT_PREFIX}.log" \
> "${LOG_DIR}/execution.log" 2>&1

sudo chown -R $USER:$USER "${LCPAN_DIR}"
python utils/organize_outputs.py LCPan "${OUTPUT_DIR}"
# Canonical output: ${CANONICAL_GFA}

# Derived outputs (optional, keep the canonical GFA unchanged):
# - ${OUTPUT_DIR}/lcpan_${DATASET_SHORT}_with_plines.gfa
# - ${OUTPUT_DIR}/lcpan_${DATASET_SHORT}_with_wlines.gfa
# LCPan can emit orphan L-links after variant-only filtering, so clean the GFA
# before asking vg to derive a reference-only P-lines view.
mkdir -p "${OUTPUT_DIR}/artifacts"
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
' "${CANONICAL_GFA}" > "${OUTPUT_DIR}/artifacts/lcpan_${DATASET_SHORT}_vg_ready.gfa"

docker compose run --rm progressivecactus bash -lc \
"vg convert -g -f -W /${OUTPUT_DIR}/artifacts/lcpan_${DATASET_SHORT}_vg_ready.gfa > /${OUTPUT_DIR}/lcpan_${DATASET_SHORT}_with_plines.gfa.tmp"
mv "${OUTPUT_DIR}/lcpan_${DATASET_SHORT}_with_plines.gfa.tmp" \
  "${OUTPUT_DIR}/lcpan_${DATASET_SHORT}_with_plines.gfa"
cp "${CANONICAL_GFA}" \
  "${OUTPUT_DIR}/lcpan_${DATASET_SHORT}_with_wlines.gfa"

sudo chown -R $USER:$USER "${LCPAN_DIR}"
```

---

### PGGB (Parameterized)

```bash
cd /home/azureuser/constructionBS

DATASET="C4_TEST"
DATASET_SHORT="C4"               # e.g. C4, KIR, MHC
THREADS="${THREADS:-16}"
PGGB_N="96"                      # number of PanSN sequences in the input
REFERENCE_PAN_NAME="GRCh38#0#C4" # exact P-line name to preserve in the derived view

RUN_DIR="results/${DATASET}/PGGB"
OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
AUX_DIR="input_data/${DATASET}/AUXILIARY_INPUTS"
TOTAL_FA="${AUX_DIR}/${DATASET_SHORT,,}_total.fa"
PAN_INPUT="${AUX_DIR}/${DATASET_SHORT,,}_total_pansn.fa"
CANONICAL_GFA="${OUTPUT_DIR}/pggb_${DATASET_SHORT}.gfa"
DERIVED_GFA="${OUTPUT_DIR}/pggb_${DATASET_SHORT}_refP_sampleW.gfa"

mkdir -p "${LOG_DIR}" "${OUTPUT_DIR}"
./utils/clean_outputs.sh "${DATASET}" PGGB

# Build the concatenated FASTA used for PGGB.
cat "input_data/${DATASET}/ASSEMBLIES/${DATASET_SHORT}-"*.fa > "${TOTAL_FA}"

# Rewrite headers into PanSN format.
# Choose the header rewrite that matches the dataset naming convention:
# - C4-style FASTA headers like SAMPLE_HAP -> >SAMPLE#HAP#<DATASET_SHORT>
# - KIR-style per-file naming is often easier with a file-by-file loop
awk -v locus="${DATASET_SHORT}" '
/^>/ {
  h = substr($0, 2)
  if (match(h, /^(.*)_([0-9]+)$/, a)) {
    print ">" a[1] "#" a[2] "#" locus
  } else {
    print "ERROR: unrecognized header -> " h > "/dev/stderr"
    exit 1
  }
  next
}
{ print }
' "${TOTAL_FA}" > "${PAN_INPUT}"

docker compose run --rm pggb bash -lc "samtools faidx /${PAN_INPUT}"
/usr/bin/time -v -o "${LOG_DIR}/timing.log" -- \
docker compose run --rm pggb bash -lc \
"pggb -i /${PAN_INPUT} -n ${PGGB_N} -t ${THREADS} -o /${OUTPUT_DIR}" \
> "${LOG_DIR}/execution.log" 2>&1
sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/organize_outputs.py PGGB "${OUTPUT_DIR}"
# Canonical output: ${CANONICAL_GFA}

# Derived output (optional, use when the canonical GFA still contains sample P-lines):
# - keep ${REFERENCE_PAN_NAME} as the only P-line
# - convert every other P-line into a W-line when possible
awk -v ref="${REFERENCE_PAN_NAME}" '
BEGIN {
  FS = OFS = "	"
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
' "${CANONICAL_GFA}" > "${DERIVED_GFA}"

awk 'BEGIN{h=0;s=0;l=0;p=0;w=0} /^H	/{h++} /^S	/{s++} /^L	/{l++} /^P	/{p++} /^W	/{w++} END{print "H="h,"S="s,"L="l,"P="p,"W="w}' \
  "${DERIVED_GFA}"
# Expected when derivation applies cleanly: P=1, W=<number_of_non_reference_paths>
```

---

### POASTA (Parameterized)

POASTA performs partial-order multiple sequence alignment from a single
multi-FASTA. It should reuse the same PanSN-headered concatenation produced for
PGGB so sample names stay aligned across tools. Sample paths are emitted as `W`
lines (the PanSN string is preserved in the seqid field).

Note on `docker compose run -T`: POASTA needs the `-T` flag (disable pseudo-TTY
allocation). Without it the `docker compose run` client receives `SIGTTOU` and
suspends (state `T`) after the container finishes, leaving the terminal hung and
`/usr/bin/time` unable to write `timing.log`. With `-T` the command returns
normally and both logs are written, exactly like the other tools. POASTA itself
is silent on success, so `execution.log` only holds the `Container ...` lines;
an empty body there means the run succeeded, not that it failed.

```bash
cd /home/azureuser/constructionBS

DATASET="C4_TEST"
DATASET_SHORT="C4"  # e.g. C4, KIR, MHC
RUN_DIR="results/${DATASET}/POASTA"
OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
AUX_DIR="input_data/${DATASET}/AUXILIARY_INPUTS"
PAN_INPUT="${AUX_DIR}/${DATASET_SHORT,,}_total_pansn.fa"

mkdir -p "${LOG_DIR}" "${OUTPUT_DIR}"
./utils/clean_outputs.sh "${DATASET}" POASTA

# Reuse the PGGB PanSN concatenation; create it first with the PGGB section.
if [ ! -s "${PAN_INPUT}" ]; then
  echo "Missing ${PAN_INPUT}; create it with the PGGB PanSN-preparation step first." >&2
  exit 1
fi

/usr/bin/time -v -o "${LOG_DIR}/timing.log" -- \
docker compose run --rm -T poasta bash -lc "\
poasta align -O poasta -o /${OUTPUT_DIR}/poasta_${DATASET_SHORT}.poasta /${PAN_INPUT} && \
poasta view -O gfa -o /${OUTPUT_DIR}/poasta_${DATASET_SHORT}.gfa /${OUTPUT_DIR}/poasta_${DATASET_SHORT}.poasta && \
poasta view -O fasta -o /${OUTPUT_DIR}/poasta_${DATASET_SHORT}_msa.fasta /${OUTPUT_DIR}/poasta_${DATASET_SHORT}.poasta" \
> "${LOG_DIR}/execution.log" 2>&1

sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/organize_outputs.py POASTA "${OUTPUT_DIR}"
# Canonical output: ${OUTPUT_DIR}/poasta_${DATASET_SHORT}.gfa
# Auxiliary outputs:
# - ${OUTPUT_DIR}/poasta_${DATASET_SHORT}.poasta
# - ${OUTPUT_DIR}/poasta_${DATASET_SHORT}_msa.fasta
```

---

### MinigraphCactus (Parameterized)

```bash
cd /home/azureuser/constructionBS

DATASET="C4_TEST"
DATASET_SHORT="C4"         # e.g. C4, KIR, MHC
REFERENCE_NAME="C4-GRCh38" # exact W-line sample name to preserve as derived P
MAX_CORES="32"
RUN_DIR="results/${DATASET}/MinigraphCactus"
OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
SEQFILE_PATH="${OUTPUT_DIR}/${DATASET,,}_seqfile.txt"
CANONICAL_GFA="${OUTPUT_DIR}/minigraphcactus_${DATASET_SHORT}.gfa"

mkdir -p "${LOG_DIR}" "${OUTPUT_DIR}"
./utils/clean_outputs.sh "${DATASET}" MinigraphCactus
python utils/make_minigraphcactus_seqfile.py "${DATASET}"
/usr/bin/time -v -o "${LOG_DIR}/timing.log" -- \
docker compose run --rm minigraphcactus bash -lc \
"cactus-pangenome /${OUTPUT_DIR}/jobstore /${SEQFILE_PATH} --outDir /${OUTPUT_DIR} --outName minigraphcactus_${DATASET_SHORT} --reference ${REFERENCE_NAME} --gfa clip --batchSystem single_machine --maxCores ${MAX_CORES}" \
> "${LOG_DIR}/execution.log" 2>&1
sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/organize_outputs.py MinigraphCactus "${OUTPUT_DIR}"
# Canonical outputs:
# - ${OUTPUT_DIR}/minigraphcactus_${DATASET_SHORT}.gfa.gz
# - ${CANONICAL_GFA}

# Derived output (optional, keep the canonical GFA unchanged):
# - ${OUTPUT_DIR}/minigraphcactus_${DATASET_SHORT}_with_plines.gfa
awk -v ref="${REFERENCE_NAME}" -F '	' '
BEGIN { OFS="	" }
$1=="W" && $2==ref {
  walk=$7
  gsub(/>/, ",", walk)
  gsub(/</, ",-", walk)
  sub(/^,/, "", walk)
  n=split(walk, a, ",")
  path=""
  for (i=1; i<=n; i++) {
    if (a[i]=="") continue
    if (a[i] ~ /^-/) path = path (path ? "," : "") substr(a[i],2) "-"
    else path = path (path ? "," : "") a[i] "+"
  }
  print "P", ref, path, "*"
  found=1
  next
}
{ print }
END {
  if (!found) {
    print "[WARN] W-line for " ref " not found" > "/dev/stderr"
    exit 1
  }
}
' "${CANONICAL_GFA}" \
  > "${OUTPUT_DIR}/minigraphcactus_${DATASET_SHORT}_with_plines.gfa"
sudo chown $USER:$USER \
  "${OUTPUT_DIR}/minigraphcactus_${DATASET_SHORT}_with_plines.gfa"
```

---

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
  bgzip -dc "${OUTPUT_DIR}/${OUT_NAME}.vcf.gz" \
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
bgzip -dc "${OUTPUT_DIR}/${OUT_NAME}.gfa.gz" \
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

---

### Cactus (Parameterized)

```bash
cd /home/azureuser/constructionBS

DATASET="C4_TEST"
DATASET_SHORT="C4"         # e.g. C4, KIR, MHC
REFERENCE_NAME="C4-GRCh38" # exact W-line sample name to preserve as derived P
MAX_CORES="32"
RUN_DIR="results/${DATASET}/Cactus"
OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
SEQFILE_PATH="${OUTPUT_DIR}/${DATASET,,}_seqfile.txt"
CANONICAL_GFA="${OUTPUT_DIR}/cactus_${DATASET_SHORT}.gfa"
CANONICAL_HAL="${OUTPUT_DIR}/cactus_${DATASET_SHORT}.hal"

mkdir -p "${LOG_DIR}" "${OUTPUT_DIR}"
./utils/clean_outputs.sh "${DATASET}" Cactus
python utils/make_cactus_seqfile.py "${DATASET}"
/usr/bin/time -v -o "${LOG_DIR}/timing.log" -- \
docker compose run --rm cactus bash -lc \
"cactus /${OUTPUT_DIR}/jobstore /${SEQFILE_PATH} /${CANONICAL_HAL} --batchSystem single_machine --maxCores ${MAX_CORES}" \
> "${LOG_DIR}/execution.log" 2>&1
sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/organize_outputs.py Cactus "${OUTPUT_DIR}"

# Export to VG/GFA from the HAL output.
# organize_outputs.py normalizes and preserves these files if they already
# exist, but it does not perform the HAL -> VG/GFA conversion itself.
docker compose run --rm cactus bash -lc \
"hal2vg /${CANONICAL_HAL} > /${OUTPUT_DIR}/cactus_${DATASET_SHORT}.vg"
docker compose run --rm cactus bash -lc \
"vg view -g /${OUTPUT_DIR}/cactus_${DATASET_SHORT}.vg > /${CANONICAL_GFA}"
# Canonical output: ${CANONICAL_GFA}

# Derived outputs (optional, keep the canonical GFA unchanged):
# - ${OUTPUT_DIR}/cactus_${DATASET_SHORT}_with_wlines.gfa
# - ${OUTPUT_DIR}/cactus_${DATASET_SHORT}_ref_as_path.gfa
awk -v ref="${REFERENCE_NAME}" -F '	' '
BEGIN { OFS="	" }
$1=="W" && $2==ref {
  walk=$7
  gsub(/>/, ",", walk)
  gsub(/</, ",-", walk)
  sub(/^,/, "", walk)
  n=split(walk, a, ",")
  path=""
  for (i=1; i<=n; i++) {
    if (a[i]=="") continue
    if (a[i] ~ /^-/) path = path (path ? "," : "") substr(a[i],2) "-"
    else path = path (path ? "," : "") a[i] "+"
  }
  print "P", ref, path, "*"
  found=1
  next
}
{ print }
END {
  if (!found) {
    print "[WARN] W-line for " ref " not found" > "/dev/stderr"
    exit 1
  }
}
' "${CANONICAL_GFA}" \
  > "${OUTPUT_DIR}/cactus_${DATASET_SHORT}_with_plines.gfa"
sudo chown -R $USER:$USER "${RUN_DIR}"
```

---

### ProgressiveCactus (Parameterized)

```bash
cd /home/azureuser/constructionBS

DATASET="C4_TEST"
DATASET_SHORT="C4"         # e.g. C4, KIR, MHC
REFERENCE_NAME="C4-GRCh38" # exact W-line sample name to preserve as derived P
MAX_CORES="32"
RUN_DIR="results/${DATASET}/ProgressiveCactus"
OUTPUT_DIR="${RUN_DIR}/outputs"
LOG_DIR="${RUN_DIR}/logs"
SEQFILE_PATH="${OUTPUT_DIR}/${DATASET,,}_seqfile.txt"
CANONICAL_GFA="${OUTPUT_DIR}/progressivecactus_${DATASET_SHORT}.gfa"
CANONICAL_HAL="${OUTPUT_DIR}/progressivecactus_${DATASET_SHORT}.hal"

mkdir -p "${LOG_DIR}" "${OUTPUT_DIR}"
./utils/clean_outputs.sh "${DATASET}" ProgressiveCactus
python utils/make_cactus_seqfile.py "${DATASET}" --output "${SEQFILE_PATH}"
/usr/bin/time -v -o "${LOG_DIR}/timing.log" -- \
docker compose run --rm progressivecactus bash -lc \
"cactus /${OUTPUT_DIR}/jobstore /${SEQFILE_PATH} /${CANONICAL_HAL} --batchSystem single_machine --maxCores ${MAX_CORES}" \
> "${LOG_DIR}/execution.log" 2>&1
sudo chown -R $USER:$USER "${RUN_DIR}"
python utils/organize_outputs.py ProgressiveCactus "${OUTPUT_DIR}"

# Export to VG/GFA from the HAL output.
# organize_outputs.py normalizes and preserves these files if they already
# exist, but it does not perform the HAL -> VG/GFA conversion itself.
docker compose run --rm progressivecactus bash -lc \
"hal2vg /${CANONICAL_HAL} > /${OUTPUT_DIR}/progressivecactus_${DATASET_SHORT}.vg"
docker compose run --rm progressivecactus bash -lc \
"vg view -g /${OUTPUT_DIR}/progressivecactus_${DATASET_SHORT}.vg > /${CANONICAL_GFA}"
# Canonical output: ${CANONICAL_GFA}

# Derived output (optional, keep the canonical GFA unchanged):
# - ${OUTPUT_DIR}/progressivecactus_${DATASET_SHORT}_with_plines.gfa
awk -v ref="${REFERENCE_NAME}" -F '	' '
BEGIN { OFS="	" }
$1=="W" && $2==ref {
  walk=$7
  gsub(/>/, ",", walk)
  gsub(/</, ",-", walk)
  sub(/^,/, "", walk)
  n=split(walk, a, ",")
  path=""
  for (i=1; i<=n; i++) {
    if (a[i]=="") continue
    if (a[i] ~ /^-/) path = path (path ? "," : "") substr(a[i],2) "-"
    else path = path (path ? "," : "") a[i] "+"
  }
  print "P", ref, path, "*"
  found=1
  next
}
{ print }
END {
  if (!found) {
    print "[WARN] W-line for " ref " not found" > "/dev/stderr"
    exit 1
  }
}
' "${CANONICAL_GFA}" \
  > "${OUTPUT_DIR}/progressivecactus_${DATASET_SHORT}_with_plines.gfa"
sudo chown -R $USER:$USER "${RUN_DIR}"
```

---

### LCPan MC vg/vgx (Parameterized)

```bash
cd /home/azureuser/constructionBS

# Configuration: change only these variables for the current dataset.
DATASET="KIR_TEST"
DATASET_SHORT="KIR"  # e.g. C4, KIR, MHC
REFERENCE_FASTA_SOURCE="input_data/${DATASET}/ASSEMBLIES/${DATASET_SHORT}-00GRCh38.fa"
CACTUS_VCF_GZ="results/${DATASET}/MC_vg/outputs/result_cactus_new.vcf.gz"
THREADS="32"

LCPAN_DIR="results/${DATASET}/LCPan"
REF_FASTA_FOR_LCPAN="${LCPAN_DIR}/inputs/reference_from_cactus.fa"
VCF_FOR_LCPAN="${LCPAN_DIR}/inputs/variants_from_cactus.vcf"

for VARIANT in mc_vg mc_vgx; do
  if [ "${VARIANT}" = "mc_vg" ]; then
    MODE_FLAG="-vg"
  else
    MODE_FLAG="-vgx"
  fi

  RUN_DIR="${LCPAN_DIR}/${VARIANT}"
  OUTPUT_DIR="${RUN_DIR}/outputs"
  LOG_DIR="${RUN_DIR}/logs"
  OUT_PREFIX="/${OUTPUT_DIR}/lcpan_from_cactus"

  mkdir -p "${LCPAN_DIR}/inputs" "${OUTPUT_DIR}" "${LOG_DIR}"
  sudo chown -R $USER:$USER "${LCPAN_DIR}"

  VCF_CONTIG="$(
    bgzip -dc "${CACTUS_VCF_GZ}" \
    | awk -F'[=,>]' '/^##contig=<ID=/{print $3; exit}'
  )"

  awk -v contig="${VCF_CONTIG}" 'NR==1{print ">" contig; next} {print}' \
    "${REFERENCE_FASTA_SOURCE}" > "${REF_FASTA_FOR_LCPAN}"

  docker compose run --rm pggb bash -lc "samtools faidx /${REF_FASTA_FOR_LCPAN}"
  bgzip -dc "${CACTUS_VCF_GZ}" > "${VCF_FOR_LCPAN}"

  /usr/bin/time -v -o "${LOG_DIR}/timing.log" -- \
  docker compose run --rm lcpan bash -lc \
  "/lcpan/bin/lcpan ${MODE_FLAG} --gfa -t ${THREADS} -r /${REF_FASTA_FOR_LCPAN} -v /${VCF_FOR_LCPAN} -p ${OUT_PREFIX} && /lcpan/lcpan-merge.sh ${OUT_PREFIX}.log" \
  > "${LOG_DIR}/execution.log" 2>&1

  mkdir -p "${OUTPUT_DIR}/artifacts"
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
' "${OUTPUT_DIR}/lcpan_from_cactus.gfa" > "${OUTPUT_DIR}/artifacts/lcpan_from_cactus_vg_ready.gfa"

  docker compose run --rm progressivecactus bash -lc \
  "vg convert -g -f -W /${OUTPUT_DIR}/artifacts/lcpan_from_cactus_vg_ready.gfa > /${OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp"

  if [ -s "${OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp" ]; then
    mv "${OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp" \
      "${OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa"
  else
    rm -f "${OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp"
    if [ "${VARIANT}" = "mc_vg" ]; then
      echo "[WARN] Skipping lcpan_from_cactus_with_plines.gfa for ${VARIANT}; vg convert -W may exceed available RAM on larger graphs." >&2
    else
      echo "[WARN] Empty with_plines output for ${VARIANT}." >&2
    fi
  fi

  cp "${OUTPUT_DIR}/lcpan_from_cactus.gfa" \
    "${OUTPUT_DIR}/lcpan_from_cactus_with_wlines.gfa"
done

sudo chown -R $USER:$USER "${LCPAN_DIR}"
```

For `LCPan/from_MC_vg`, treat `lcpan_from_cactus_with_plines.gfa` as optional.
If `vg convert -W` is OOM-killed on larger graphs, keep the canonical GFA plus
`lcpan_from_cactus_with_wlines.gfa` and consider the run valid.

- Permission issues after container runs:
  ```bash
  sudo chown -R $USER:$USER results/<DATASET>/<TOOL>
  ```
- Permission issues after container runs:
  ```bash
  sudo chown -R $USER:$USER results/<DATASET>/<TOOL>
  ```
