# constructionBS

constructionBS is a **reproducible benchmark suite** for pangenome graph
construction. It runs several containerized graph-construction tools on the same
datasets, under pinned environments, and records enough provenance that a run
can be reproduced and compared months later.

The suite is built around three reproducibility guarantees:

1. **Environment** — every container is pinned (base image by digest, git
   sources by commit SHA), so a rebuild is byte-stable. See [Reproducibility](#reproducibility).
2. **Execution** — a single orchestrator (`run_tool.py`) runs a tool end to end
   from declarative specs, reading all dataset-specific values from versioned
   config instead of hand-edited shell blocks. See [Running a tool](#running-a-tool).
3. **Result** — each run writes a `run_manifest.yml` next to its outputs
   (tool, version, params, commands, timing), so results are self-describing.

## Repository layout

```
constructionBS/
├── run_tool.py              # orchestrator: run one tool on one dataset, end to end
├── tools_config.yml         # per-tool version pins (ref + pin); source of truth for builds
├── tool_registry.py         # per-tool metadata: source, compose service, requirements, input specs
├── make_dockerfiles.py      # generates Dockerfiles/ from tools_config.yml (+ templates)
├── make_dockercompose.py    # generates docker-compose.yml from the registry
├── docker-compose.yml       # GENERATED — one service per tool
├── run_config.py            # repo roots (input_data/results) + expected file types
├── config/
│   └── datasets/<DS>.yml     # VERSIONED dataset config (see Dataset config)
├── Dockerfiles/<Tool>/       # GENERATED per-tool Dockerfiles
├── patches/                  # source patches applied at build time (e.g. Theseus)
├── utils/                    # seqfile generators, output/timing summarizers, helpers
├── docs/
│   └── runbook_commands.md   # raw command blocks for tools not yet orchestrated
├── input_data/  ->  symlink to the data mount (datasets live outside git)
└── results/     ->  symlink to the results mount
```

`input_data/` and `results/` are symlinks to a data mount — the heavy data is
**not** in git. Dataset *configuration* is, under `config/datasets/`.

## Prerequisites

- Python 3.8+ with `pyyaml` (`pip install pyyaml`)
- Docker and Docker Compose
- `gawk` on the host (host-side awk steps rely on GNU awk; the containers ship
  only `mawk`)

## Supported tools

Nine tools are registered. Five are driven end to end by the orchestrator; the
other four still run via the runbook (see [Tool status](#tool-status)).

| Tool | Type | Container base |
|------|------|----------------|
| Minigraph | git | ubuntu (build from source) |
| Cactus | image | cactus |
| ProgressiveCactus | image | cactus |
| MinigraphCactus | image | cactus (`cactus-pangenome`) |
| MC_vg | image | cactus + `vg autoindex` branch |
| PGGB | image | pggb |
| POASTA | git | rust (build from source) |
| Theseus | git | ubuntu (build from source, patched) |
| LCPan | git | ubuntu (VCF-driven, single-reference) |

## Dataset structure

Each dataset directory (under the `input_data/` mount) follows:

```
<DATASET>/
├── ASSEMBLIES/                   # primary per-sample FASTA inputs
├── ASSEMBLIES_CACTUS_SANITIZED/  # sanitized copies for Cactus-family workflows
├── AUXILIARY_INPUTS/             # helper FASTA (concatenated *_total.fa, *_reference.fa, ...)
├── GRAPH/                        # graph/VCF inputs (LCPan reference + VCF live here)
└── META/
    └── dataset_info.yml          # legacy config location (see below)
```

Conventions:
- `ASSEMBLIES/` holds only the primary per-sample FASTA inputs used by
  graph-construction workflows. Helper/aggregate FASTA go in `AUXILIARY_INPUTS/`
  and are intentionally ignored by the seqfile generators.
- `C4_TEST` is a validated historical exception: its `ASSEMBLIES/` is a
  symlink view of `ASSEMBLIES_CACTUS_SANITIZED/`.

## Dataset config

Dataset configuration is **version-controlled** in `config/datasets/<DATASET>.yml`.
The suite resolves config by preferring that versioned file, falling back to the
legacy `META/dataset_info.yml` inside the (unversioned) data mount when it is
absent — so datasets that predate the migration keep working unchanged.

A config file declares the readiness, the enabled workflows (used as an
execution gate), and the tool parameters that the orchestrator reads instead of
hand-edited variables:

```yaml
dataset_short: C4                 # short token used in output filenames
status: ready
reference_name: C4-GRCh38         # reference sample (Cactus-family, MC_vg)
threads: 16                       # global default; per-tool overrides below
supported_workflows:              # execution gate: only enabled tools may run
  cactus: true
  minigraph: true
  minigraphcactus: true
  progressivecactus: true
  mc_vg: true
cactus:
  max_cores: 32                   # per-tool override of the global `threads`
seqfile:
  sample_name_rewrites:           # generic header rewrites (no dataset names in code)
    "00GRCh38": "GRCh38"
```

## Running a tool

The orchestrator runs one tool on one dataset end to end:

```bash
python run_tool.py <DATASET> <TOOL> [--dry-run] [--skip-optional] [--force]
```

- `--dry-run` — print the rendered plan (every step, fully expanded) and the
  provenance manifest, without executing anything. **Start here** to see exactly
  what will run.
- `--skip-optional` — skip optional (derived-output) steps.
- `--force` — overwrite an existing canonical output. Without it, the run is
  **refused** when a canonical output already exists, to protect validated runs.

Example:

```bash
python run_tool.py C4_TEST Minigraph --dry-run   # inspect the plan
python run_tool.py C4_TEST Minigraph             # execute
```

What a run does, in order:

1. Inspect the dataset and **gate** on `supported_workflows` (refuse if the tool
   is not enabled for that dataset).
2. Resolve inputs from the dataset files and parameters from the config
   (per-tool override, then global fallback).
3. Execute each declarative step (`prep` / `timed` / `post`): host-side steps run
   locally with `gawk`/Python; container steps run via `docker compose run`. The
   timed step(s) are wrapped with `/usr/bin/time`, each writing its own timing log.
4. Fix output ownership, organize outputs into canonical names, and write
   `run_manifest.yml`.

Tool commands are declarative specs in `utils/tool_commands.py`
(`Step` / `ParamSpec` / `ToolCommandSpec`); `run_tool.py` itself does not change
per tool. Environment roots can be overridden with `CONSTRUCTIONBS_INPUT_DATA`
and `CONSTRUCTIONBS_RESULTS`.

### Tool status

- **Orchestrated (via `run_tool.py`)** — validated at runtime:
  Minigraph, Cactus, ProgressiveCactus, MinigraphCactus, MC_vg.
  These are the tools whose per-sample naming is recoverable from the FASTA
  filename.
- **Runbook only** — PGGB, POASTA, Theseus, LCPan. These depend on a PanSN /
  cross-tool naming convention that is not yet settled, so they still run from
  the raw command blocks in [`docs/runbook_commands.md`](docs/runbook_commands.md).
  They re-enter the orchestrator once the cross-tool naming is decided
  (`utils/make_pansn.py` is a ready, dataset-agnostic PanSN builder for that).

## Reproducibility

### Pinning (`tools_config.yml`)

Each tool declares a human-readable version and the immutable identity the build
actually uses:

```yaml
Minigraph:
  source: git
  ref: v0.21                                  # human-readable version
  pin: 7e3e65c5e55a10e2968f32cef5c04eee9330521b  # commit SHA the build checks out

Cactus:
  source: image
  ref: v3.1.4
  pin: sha256:c0ded40e585f6d5346c64d83485a3f021eab4b400fc4019caf30aff82feb413e
```

- `source: image` → `pin` is the base-image digest.
- `source: git` → `pin` is the commit SHA (`git checkout`, or `cargo --rev`).

Base images for git-built tools (ubuntu/rust) are pinned by digest directly in
the Dockerfile templates in `make_dockerfiles.py`, since they are a property of
the build recipe rather than a per-tool version. apt package versions are
intentionally **not** pinned (they vanish from Ubuntu repos on security updates
and would break builds).

To update a tool: resolve the new commit/digest, set `ref` + `pin`, regenerate,
rebuild, and re-validate. Note git tags may be **annotated** — dereference to the
commit (`git ls-remote <repo> 'refs/tags/<tag>^{}'`) or the pin will be wrong.

### Build

```bash
python make_dockerfiles.py     # regenerate Dockerfiles/ from tools_config.yml
python make_dockercompose.py   # regenerate docker-compose.yml + prep results dirs
docker compose build <service> # e.g. minigraph
```

`Dockerfiles/` and `docker-compose.yml` are **generated** — edit the config and
templates, not the generated files.

## Validating datasets

Inspect dataset structure and per-tool runnability:

```bash
python -m utils.check_inputs                       # all datasets under input_data/
python -m utils.check_inputs --dataset C4_TEST     # one dataset
python -m utils.check_inputs --input-data /path --dataset C4_TEST
```

## Summaries

After runs complete, build compact Markdown summaries for a dataset:

```bash
python -m utils.summarize_timing_logs <DATASET>    # -> results/<DATASET>/timing_summary.md
python -m utils.summarize_output_graphs <DATASET>  # -> results/<DATASET>/output_summary.md
```

Both prefer the `dataset_short` config field when present, falling back to
stripping a trailing `_TEST`.

## Results structure

```
results/<DATASET>/<TOOL>/
├── outputs/                # canonical graph(s) + artifacts/
│   └── run_manifest.yml    # provenance for the run
└── logs/                   # execution.log + timing log(s)
```

## Key scripts

- `run_tool.py` — orchestrator; run one tool on one dataset end to end
- `utils/tool_commands.py` — declarative per-tool command specs (the 5 orchestrated tools)
- `tool_registry.py` — central per-tool metadata (source, service, requirements, inputs)
- `make_dockerfiles.py` / `make_dockercompose.py` — generators for the build environment
- `utils/check_inputs.py` — dataset validation and inspection
- `utils/organize_outputs.py` — normalize tool outputs into canonical names + artifacts/
- `utils/summarize_timing_logs.py` / `utils/summarize_output_graphs.py` — per-dataset summaries
- `utils/make_cactus_seqfile.py` / `utils/make_minigraphcactus_seqfile.py` — seqfile generators
- `utils/make_pansn.py` — dataset-agnostic PanSN FASTA builder (ready for the PanSN tools)
- `utils/clean_outputs.sh` — reset one dataset/tool results directory before reruns
- `utils/dataset_utils.py` — compatibility facade re-exporting dataset helpers

## Adding a dataset

Plug-and-play, no code: create the dataset directory under the data mount with
`ASSEMBLIES/` (+ `GRAPH/` for LCPan) and add `config/datasets/<DATASET>.yml`
with `dataset_short`, `supported_workflows`, and any tool parameters. Nothing in
the code hardcodes dataset names.

## Adding a tool

1. Add the version pin to `tools_config.yml` (`ref` + `pin`).
2. Add the tool entry to `tool_registry.py` (source, compose service,
   requirements, input specs).
3. Add the Dockerfile template to `make_dockerfiles.py`, then regenerate.
4. Add a `ToolCommandSpec` to `utils/tool_commands.py` to make it orchestrated.
5. Validate: `--dry-run` against the runbook, then a real run compared to the
   validated baseline (md5 for deterministic tools, structural S/L/P/W + bp +
   sample names for non-deterministic ones).
