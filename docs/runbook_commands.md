# Runbook Commands

Last validated: 2026-05-15

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

## C4 End-to-End Commands By Tool

### Minigraph (C4_TEST)

```bash
cd /home/azureuser/constructionBS
mkdir -p results/C4_TEST/Minigraph/{logs,outputs}
./utils/clean_outputs.sh C4_TEST Minigraph
/usr/bin/time -v -o results/C4_TEST/Minigraph/logs/timing.log -- \
docker compose run --rm minigraph bash -lc "cd /minigraph && ./minigraph -cxggs /input_data/C4_TEST/ASSEMBLIES/C4-*.fa > /results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa" \
> results/C4_TEST/Minigraph/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/Minigraph
python utils/organize_outputs.py Minigraph results/C4_TEST/Minigraph/outputs
# Canonical output: results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa

# Optional: reference-only derived encodings from Minigraph canonical rGFA.
# These commands recover only the reference backbone (rank 0), not sample paths.
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f /results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa > /results/C4_TEST/Minigraph/outputs/minigraph_C4_with_wlines.gfa"
docker compose run --rm progressivecactus bash -lc "vg convert -g -r 0 -f -W /results/C4_TEST/Minigraph/outputs/minigraph_C4.gfa > /results/C4_TEST/Minigraph/outputs/minigraph_C4_with_plines.gfa"
sudo chown $USER:$USER \
  results/C4_TEST/Minigraph/outputs/minigraph_C4_with_wlines.gfa \
  results/C4_TEST/Minigraph/outputs/minigraph_C4_with_plines.gfa
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

### LCPan PGGB vg/vgx (Parameterized)

```bash
cd /home/azureuser/constructionBS

DATASET="C4_TEST"
DATASET_SHORT="C4"      # e.g. C4, KIR, MHC
THREADS="32"
VARIANT="pggb_vg"       # pggb_vg or pggb_vgx
MODE_FLAG="-vg"         # -vg for pggb_vg, -vgx for pggb_vgx
REFERENCE_FASTA="/input_data/${DATASET}/GRAPH/c4_reference_pansn.fa"
INPUT_VCF="/input_data/${DATASET}/GRAPH/lcpan_${DATASET_SHORT}.vcf"
OUT_PREFIX="/results/${DATASET}/LCPan/${VARIANT}/outputs/lcpan_${DATASET_SHORT}"
LOG_DIR="results/${DATASET}/LCPan/${VARIANT}/logs"

mkdir -p "results/${DATASET}/LCPan/${VARIANT}/outputs" "${LOG_DIR}"
sudo chown -R $USER:$USER "results/${DATASET}/LCPan"

/usr/bin/time -v -o "${LOG_DIR}/timing.log" -- \
docker compose run --rm lcpan bash -lc \
"/lcpan/bin/lcpan ${MODE_FLAG} --gfa -t ${THREADS} -r ${REFERENCE_FASTA} -v ${INPUT_VCF} -p ${OUT_PREFIX} && /lcpan/lcpan-merge.sh ${OUT_PREFIX}.log" \
> "${LOG_DIR}/execution.log" 2>&1

sudo chown -R $USER:$USER "results/${DATASET}/LCPan"
python utils/organize_outputs.py LCPan "results/${DATASET}/LCPan/${VARIANT}/outputs"
```

### PGGB (C4_TEST)

```bash
cd /home/azureuser/constructionBS
THREADS="${THREADS:-16}"
mkdir -p results/C4_TEST/PGGB/{logs,outputs}
./utils/clean_outputs.sh C4_TEST PGGB
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

docker compose run --rm pggb bash -lc "samtools faidx /input_data/C4_TEST/AUXILIARY_INPUTS/c4_total_pansn.fa"
/usr/bin/time -v -o results/C4_TEST/PGGB/logs/timing.log -- docker compose run --rm pggb bash -lc "pggb -i /input_data/C4_TEST/AUXILIARY_INPUTS/c4_total_pansn.fa -n 96 -t ${THREADS} -o /results/C4_TEST/PGGB/outputs" > results/C4_TEST/PGGB/logs/execution.log 2>&1
sudo chown -R $USER:$USER results/C4_TEST/PGGB
python utils/organize_outputs.py PGGB results/C4_TEST/PGGB/outputs
# Canonical output: results/C4_TEST/PGGB/outputs/pggb_C4.gfa

# Cross-tool normalization for C4 only:
# - keep GRCh38#0#C4 as the only P-line
# - convert every non-reference sample path to a W-line
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
''' results/C4_TEST/PGGB/outputs/pggb_C4.gfa > results/C4_TEST/PGGB/outputs/pggb_C4_refP_sampleW.gfa

awk '''BEGIN{h=0;s=0;l=0;p=0;w=0} /^H	/{h++} /^S	/{s++} /^L	/{l++} /^P	/{p++} /^W	/{w++} END{print "H="h,"S="s,"L="l,"P="p,"W="w}'''   results/C4_TEST/PGGB/outputs/pggb_C4_refP_sampleW.gfa
# Expected for C4_TEST normalized view: P=1, W=95
```

### POASTA (C4_TEST)

POASTA performs partial-order multiple sequence alignment from a single
multi-FASTA. It reuses the same PanSN-headered concatenation produced for PGGB
(`c4_total_pansn.fa`) so sample names match the other tools. Sample paths are
emitted as `W` lines (the PanSN string is preserved in the seqid field).

Note on `docker compose run -T`: POASTA needs the `-T` flag (disable pseudo-TTY
allocation). Without it the `docker compose run` client receives `SIGTTOU` and
suspends (state `T`) after the container finishes, leaving the terminal hung and
`/usr/bin/time` unable to write `timing.log`. With `-T` the command returns
normally and both logs are written, exactly like the other tools. POASTA itself
is silent on success, so `execution.log` only holds the `Container ...` lines;
an empty body there means the run succeeded, not that it failed.

```bash
cd /home/azureuser/constructionBS
mkdir -p results/C4_TEST/POASTA/{logs,outputs}
./utils/clean_outputs.sh C4_TEST POASTA

# Reuse the PGGB PanSN concatenation; regenerate it only if missing.
if [ ! -s input_data/C4_TEST/AUXILIARY_INPUTS/c4_total_pansn.fa ]; then
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
fi

# time -v stays OUTSIDE (same as every other tool); the only difference is `-T`.
# align builds the native .poasta graph; two `view` passes derive GFA + MSA
# without re-aligning.
/usr/bin/time -v -o results/C4_TEST/POASTA/logs/timing.log -- \
docker compose run --rm -T poasta bash -lc "\
poasta align -O poasta -o /results/C4_TEST/POASTA/outputs/poasta_C4.poasta /input_data/C4_TEST/AUXILIARY_INPUTS/c4_total_pansn.fa && \
poasta view -O gfa -o /results/C4_TEST/POASTA/outputs/poasta_C4.gfa /results/C4_TEST/POASTA/outputs/poasta_C4.poasta && \
poasta view -O fasta -o /results/C4_TEST/POASTA/outputs/poasta_C4_msa.fasta /results/C4_TEST/POASTA/outputs/poasta_C4.poasta" \
> results/C4_TEST/POASTA/logs/execution.log 2>&1

sudo chown -R $USER:$USER results/C4_TEST/POASTA
python utils/organize_outputs.py POASTA results/C4_TEST/POASTA/outputs
# Canonical output: results/C4_TEST/POASTA/outputs/poasta_C4.gfa
# Auxiliary outputs: poasta_C4.poasta (native graph), poasta_C4_msa.fasta (MSA)
```

### MinigraphCactus (C4_TEST)

```bash
cd /home/azureuser/constructionBS
mkdir -p results/C4_TEST/MinigraphCactus/{logs,outputs}
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

# Derived encodings from the canonical GFA for visualization only.
# Keep the canonical file unchanged. The reference normalization below replaces
# only `W  C4-GRCh38` with `P  C4-GRCh38` and leaves every other sample `W`
# unchanged.
cp results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa \
  results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_with_wlines.gfa
awk -v ref="C4-GRCh38" -F '\t' '
BEGIN { OFS="\t" }
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
' results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa \
  > results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_ref_as_path.gfa
sudo chown $USER:$USER \
  results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4.gfa \
  results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_with_wlines.gfa \
  results/C4_TEST/MinigraphCactus/outputs/minigraphcactus_C4_ref_as_path.gfa
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
mkdir -p results/C4_TEST/Cactus/{logs,outputs}
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

# Derived encodings from the canonical GFA for visualization only.
# Keep the canonical file unchanged. The reference normalization below replaces
# only `W  C4-GRCh38` with `P  C4-GRCh38` and leaves every other sample `W`
# unchanged.
cp results/C4_TEST/Cactus/outputs/cactus_C4.gfa \
  results/C4_TEST/Cactus/outputs/cactus_C4_with_wlines.gfa
awk -v ref="C4-GRCh38" -F '\t' '
BEGIN { OFS="\t" }
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
' results/C4_TEST/Cactus/outputs/cactus_C4.gfa \
  > results/C4_TEST/Cactus/outputs/cactus_C4_ref_as_path.gfa
sudo chown -R $USER:$USER results/C4_TEST/Cactus
```

### ProgressiveCactus (C4_TEST)

```bash
cd /home/azureuser/constructionBS
mkdir -p results/C4_TEST/ProgressiveCactus/{logs,outputs}
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

# Derived encodings from the canonical GFA for visualization only.
# Keep the canonical file unchanged. The reference normalization below replaces
# only `W  C4-GRCh38` with `P  C4-GRCh38` and leaves every other sample `W`
# unchanged.
cp results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.gfa \
  results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4_with_wlines.gfa
awk -v ref="C4-GRCh38" -F '\t' '
BEGIN { OFS="\t" }
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
' results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4.gfa \
  > results/C4_TEST/ProgressiveCactus/outputs/progressivecactus_C4_ref_as_path.gfa
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
if [ -s "${VG_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp" ]; then
  mv "${VG_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp" \
    "${VG_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa"
else
  rm -f "${VG_OUTPUT_DIR}/lcpan_from_cactus_with_plines.gfa.tmp"
  echo "[WARN] Skipping lcpan_from_cactus_with_plines.gfa for from_MC_vg; vg convert -W may exceed available RAM on larger graphs." >&2
fi
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

For `LCPan/from_MC_vg`, treat `lcpan_from_cactus_with_plines.gfa` as optional.
If `vg convert -W` is OOM-killed on larger graphs, keep the canonical GFA plus
`lcpan_from_cactus_with_wlines.gfa` and consider the run valid.

- Permission issues after container runs:
  ```bash
  sudo chown -R $USER:$USER results/<DATASET>/<TOOL>
  ```
