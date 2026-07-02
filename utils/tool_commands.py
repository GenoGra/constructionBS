"""
Declarative, per-tool command definitions for the run orchestrator.

Each tool is modeled as an ordered list of steps rather than a single command,
so multi-step pipelines (prepare inputs -> construct graph -> post-process) are
expressible uniformly. Exactly one step per tool is marked ``timed=True``: that
is the graph-construction step wrapped by ``/usr/bin/time`` (the benchmark
measurement). Other steps are input preparation (cacheable), unmeasured
conversions, or optional derived-output steps.

This module holds no dataset-specific knowledge: every value that varies by
dataset (reference name, thread count, PanSN naming, ...) arrives via the
``params`` resolved from ``META/dataset_info.yml`` plus the input files resolved
by ``input_resolution``. Adding a new tool means adding one entry here; the
orchestrator itself does not change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# Kinds of step, used by the orchestrator to decide how to run each one.
#   prep : input preparation; may declare a cache output that is reused when
#          fresh (skipped if the cache file is newer than its sources).
#   run  : the graph-construction step; the single timed step per tool.
#   post : conversions / derived outputs; unmeasured. ``optional`` post steps
#          are skipped when the caller passes --skip-optional.
STEP_KINDS = ("prep", "run", "post")


@dataclass(frozen=True)
class ParamSpec:
    """
    One tool parameter sourced from dataset metadata.

    ``metadata_key`` is a dotted path read from META/dataset_info.yml (e.g.
    "pggb.n_haplotypes"). ``required`` params with no value and no default make
    the orchestrator fail *before* launching Docker, with a clear message.
    """

    name: str
    metadata_key: str
    required: bool = False
    default: object | None = None
    # Optional fallback metadata key tried when metadata_key is absent, before
    # falling back to `default`. Used for per-tool overrides of a global value:
    # e.g. metadata_key="cactus.max_cores", fallback_key="threads".
    fallback_key: str | None = None


@dataclass(frozen=True)
class Step:
    """
    One step in a tool pipeline.

    ``template`` is a shell command with ``{placeholder}`` fields filled from the
    render context (resolved inputs, resolved params, and layout paths). ``kind``
    is one of STEP_KINDS. For ``run`` steps ``timed`` must be True. ``cache_key``
    (prep only) names the context key whose file, when newer than every path in
    ``cache_sources``, lets the orchestrator skip this step. ``optional`` marks
    derived-output steps that --skip-optional drops.
    """

    kind: str
    template: str
    timed: bool = False
    optional: bool = False
    host: bool = False  # run on the host (Python/shell) instead of in a container
    service: str | None = None  # docker compose service; None -> tool default
    workdir: str | None = None  # cd here first (kept OUTSIDE the timing wrap)
    cache_key: str | None = None
    cache_sources: tuple[str, ...] = ()
    label: str = ""
    # Timing log filename (under logs/) for a timed step. Defaults to
    # "timing.log". Tools with MORE THAN ONE timed step (e.g. MC_vg times both
    # cactus-pangenome and vg autoindex) give each a distinct name so their
    # measurements do not overwrite each other. Single-timed tools omit it.
    timing_log: str = "timing.log"


@dataclass(frozen=True)
class ToolCommandSpec:
    """
    Full command definition for one tool: which compose service it runs in,
    which metadata-driven params it needs, and its ordered steps.
    """

    tool_name: str
    service: str
    steps: tuple[Step, ...]
    params: tuple[ParamSpec, ...] = ()
    # Render-context keys naming directories that MUST NOT exist when the run
    # starts, e.g. the Toil {jobstore} for Cactus-family/MC tools. The
    # orchestrator removes these (targeted, host-side) before executing, without
    # touching the canonical output. A failed run leaves a half-built jobstore
    # that would otherwise block the next run (JobStoreExistsException).
    clean_before_run: tuple[str, ...] = ()
    # Canonical output filenames (relative to outputs/) for overwrite protection.
    # Most tools follow the default "<tool>_<short>.gfa[.gz]" convention and leave
    # this empty; MC_vg is the exception (its outputs are named result_cactus_new.gfa,
    # result_autoindex.gfa, result_autoindex_c.gfa — all three are canonical).
    # When set, the orchestrator guards these instead of the default name.
    canonical_outputs: tuple[str, ...] = ()
    # Optional hook to compute derived context values from resolved inputs/params
    # (e.g. an assembly glob, an output prefix). Kept as a function so tool
    # entries stay declarative for the common case.
    context_builder: Callable[[dict], dict] | None = None

    def timed_steps(self) -> tuple[Step, ...]:
        return tuple(step for step in self.steps if step.timed)


# ---------------------------------------------------------------------------
# Tool definitions.
#
# Pilot scope: Minigraph (single timed step) and PGGB (prep + timed + optional).
# The remaining tools are added here later as further entries; nothing else in
# the orchestrator needs to change to support them.
# ---------------------------------------------------------------------------

def _minigraph_context(ctx: dict) -> dict:
    """
    Minigraph consumes all assemblies as a space-separated list, reference first.
    ``assemblies`` are already resolved container paths (reference at index 0 by
    the sorted ASSEMBLIES order, matching the seqfile/runbook convention).
    """
    assemblies = ctx["inputs"]["assemblies"]
    return {"assemblies_joined": " ".join(assemblies)}


TOOL_COMMANDS: dict[str, ToolCommandSpec] = {
    "Minigraph": ToolCommandSpec(
        tool_name="Minigraph",
        service="minigraph",
        params=(),
        context_builder=_minigraph_context,
        steps=(
            Step(
                kind="run",
                timed=True,
                label="minigraph-construct",
                workdir="/minigraph",
                template="./minigraph -cxggs {assemblies_joined} > {canonical_gfa}",
            ),
            Step(
                kind="post",
                optional=True,
                service="progressivecactus",
                label="derive-wlines",
                template=(
                    "vg convert -g -r 0 -f {canonical_gfa} > {out_dir}/minigraph_{dataset_short}_with_wlines.gfa"
                ),
            ),
            Step(
                kind="post",
                optional=True,
                service="progressivecactus",
                label="derive-plines",
                template=(
                    "vg convert -g -r 0 -f -W {canonical_gfa} > {out_dir}/minigraph_{dataset_short}_with_plines.gfa"
                ),
            ),
        ),
    ),
    # NOTE: PGGB / POASTA / Theseus are intentionally NOT modeled here yet.
    # They consume a PanSN-headered input whose sample-naming convention is not
    # yet unified with the filename-based naming the other tools use (the
    # historical PanSN names were inconsistent across datasets). Per the design
    # decision, only tools whose naming is naturally recoverable from the
    # filename live in the orchestrator; PanSN tools stay in the runbook until a
    # suite-wide naming convention is settled. utils/make_pansn.py implements a
    # correct, dataset-agnostic PanSN builder ready for that future work.
}


# --- Cactus family (Cactus, ProgressiveCactus) -----------------------------
#
# Both run the same binary (`cactus`) producing a HAL, then export HAL->VG->GFA
# with hal2vg + vg view (unmeasured), then an optional derived P-lines view.
# The seqfile is generated on the HOST via make_cactus_seqfile.py.
#
# {seqfile_host} is the host seqfile path; {seqfile} its container path.
# {out_dir}/{jobstore}/{canonical_hal}/{canonical_gfa} are container paths.
# {vg_out} is the intermediate .vg (container). {ref_name} comes from metadata.

def _cactus_family_steps(tool_lower: str) -> tuple[Step, ...]:
    return (
        Step(
            kind="prep",
            host=True,
            label="make-seqfile",
            template=(
                "python utils/make_cactus_seqfile.py {dataset} --output {seqfile_host}"
            ),
        ),
        Step(
            kind="run",
            timed=True,
            label="cactus-construct",
            template=(
                "cactus {out_dir}/jobstore {seqfile} {canonical_hal} "
                "--batchSystem single_machine --maxCores {max_cores}"
            ),
        ),
        Step(
            kind="run",
            label="hal2vg",
            template=f"hal2vg {{canonical_hal}} > {{out_dir}}/{tool_lower}_{{dataset_short}}.vg",
        ),
        Step(
            kind="run",
            label="vg-view-gfa",
            template=(
                f"vg view -g {{out_dir}}/{tool_lower}_{{dataset_short}}.vg "
                f"> {{canonical_gfa}}"
            ),
        ),
    )


TOOL_COMMANDS["Cactus"] = ToolCommandSpec(
    tool_name="Cactus",
    service="cactus",
    params=(
        ParamSpec("ref_name", "reference_name", required=False),
        ParamSpec("max_cores", "cactus.max_cores", fallback_key="threads",
                  required=False, default=32),
    ),
    steps=_cactus_family_steps("cactus"),
    clean_before_run=("jobstore_host",),
)

TOOL_COMMANDS["ProgressiveCactus"] = ToolCommandSpec(
    tool_name="ProgressiveCactus",
    service="progressivecactus",
    params=(
        ParamSpec("ref_name", "reference_name", required=False),
        ParamSpec("max_cores", "progressivecactus.max_cores", fallback_key="threads",
                  required=False, default=32),
    ),
    steps=_cactus_family_steps("progressivecactus"),
    clean_before_run=("jobstore_host",),
)


# --- MinigraphCactus --------------------------------------------------------
#
# Single `cactus-pangenome` command that emits the GFA directly (no separate
# HAL->VG export). The seqfile is generated on the HOST via
# make_minigraphcactus_seqfile.py. --reference and --maxCores come from metadata.
# {outname} is the cactus-pangenome --outName; the tool writes
# <outDir>/<outName>.gfa[.gz].

TOOL_COMMANDS["MinigraphCactus"] = ToolCommandSpec(
    tool_name="MinigraphCactus",
    service="minigraphcactus",
    params=(
        ParamSpec("ref_name", "reference_name", required=True),
        ParamSpec("max_cores", "minigraphcactus.max_cores", fallback_key="threads",
                  required=False, default=32),
    ),
    steps=(
        Step(
            kind="prep",
            host=True,
            label="make-seqfile",
            template=(
                "python utils/make_minigraphcactus_seqfile.py {dataset} "
                "--output {seqfile_host}"
            ),
        ),
        Step(
            kind="run",
            timed=True,
            label="cactus-pangenome",
            template=(
                "cactus-pangenome {out_dir}/jobstore {seqfile} "
                "--outDir {out_dir} --outName minigraphcactus_{dataset_short} "
                "--reference {ref_name} --gfa clip "
                "--batchSystem single_machine --maxCores {max_cores}"
            ),
        ),
    ),
    clean_before_run=("jobstore_host",),
)


# --- MC_vg ------------------------------------------------------------------
#
# The longest pipeline: cactus-pangenome (with --vcf/--giraffe/--gbz) then a
# reference-centric vg autoindex branch, then GFA exports. TWO timed steps
# (cactus-pangenome and vg autoindex), each with its own timing log. Naming is
# recoverable (make_minigraphcactus_seqfile → sample from filename), so MC_vg
# qualifies for the orchestrator. Its outputs use fixed names (result_cactus_new,
# result_autoindex, result_autoindex_c) — all three GFAs are canonical.
#
# OUT_NAME=result_cactus_new, AUTOINDEX_PREFIX=result_autoindex (as in runbook).
# {vcf_contig} is extracted at run time from the cactus VCF (like pggb_n): the
# reference FASTA header must match the VCF contig id.

TOOL_COMMANDS["MC_vg"] = ToolCommandSpec(
    tool_name="MC_vg",
    service="minigraphcactus",
    params=(
        ParamSpec("ref_name", "reference_name", required=True),
        ParamSpec("max_cores", "mc_vg.max_cores", fallback_key="threads",
                  required=False, default=16),
    ),
    clean_before_run=("jobstore_host",),
    canonical_outputs=(
        "result_cactus_new.gfa",
        "result_autoindex.gfa",
        "result_autoindex_c.gfa",
    ),
    steps=(
        Step(
            kind="prep",
            host=True,
            label="make-seqfile",
            template=(
                "python -m utils.make_minigraphcactus_seqfile {dataset} "
                "--output {seqfile_host}"
            ),
        ),
        Step(
            kind="run",
            timed=True,
            timing_log="timing_cactus_pangenome.log",
            label="cactus-pangenome",
            template=(
                "cactus-pangenome {out_dir}/jobstore {seqfile} "
                "--outDir {out_dir} --outName result_cactus_new "
                "--reference {ref_name} --vcf --giraffe --gfa --gbz "
                "--batchSystem single_machine --maxCores {max_cores}"
            ),
        ),
        # Build the vg-autoindex reference FASTA on the HOST: extract the contig
        # id from the cactus VCF at run time and rewrite the reference header to
        # match it (awk → host, and the value is only known post-cactus).
        Step(
            kind="prep",
            host=True,
            label="build-autoindex-ref",
            template=(
                "VCF_CONTIG=$(bgzip -dc {out_dir_host}/result_cactus_new.vcf.gz "
                "| gawk -F'[=,>]' '/^##contig=<ID=/{{print $3; exit}}') && "
                "gawk -v contig=\"$VCF_CONTIG\" 'NR==1{{print \">\" contig; next}} {{print}}' "
                "{ref_fasta_host} > {out_dir_host}/result_autoindex_ref.fa"
            ),
        ),
        Step(
            kind="run",
            timed=True,
            timing_log="timing_vg_autoindex.log",
            label="vg-autoindex",
            template=(
                "vg autoindex --workflow sr-giraffe "
                "--prefix {out_dir}/result_autoindex "
                "--ref-fasta {out_dir}/result_autoindex_ref.fa "
                "--vcf {out_dir}/result_cactus_new.vcf.gz --threads {max_cores}"
            ),
        ),
        # Export autoindex graph to GFA, then unchop. Write to .tmp then mv so a
        # failed command does not leave a misleading final output (runbook pattern).
        Step(
            kind="run",
            label="export-autoindex-gfa",
            template=(
                "vg convert -f {out_dir}/result_autoindex.giraffe.gbz "
                "> {out_dir}/result_autoindex_c.gfa.tmp && "
                "mv {out_dir}/result_autoindex_c.gfa.tmp {out_dir}/result_autoindex_c.gfa && "
                "vg mod -u {out_dir}/result_autoindex_c.gfa "
                "> {out_dir}/result_autoindex.gfa.tmp && "
                "mv {out_dir}/result_autoindex.gfa.tmp {out_dir}/result_autoindex.gfa"
            ),
        ),
        # Uncompressed, editor-friendly copy of the cactus GFA (host: bgzip).
        Step(
            kind="post",
            host=True,
            label="decompress-cactus-gfa",
            template=(
                "bgzip -dc {out_dir_host}/result_cactus_new.gfa.gz "
                "> {out_dir_host}/result_cactus_new.gfa"
            ),
        ),
    ),
)


def get_tool_command_spec(tool_name: str) -> ToolCommandSpec | None:
    """
    Return the command spec for a tool, or None when not yet modeled.
    """
    return TOOL_COMMANDS.get(tool_name)
