"""
Run one graph-construction tool on one dataset, end to end.

    python run_tool.py <DATASET> <TOOL> [--dry-run] [--skip-optional] [--no-timing]

The orchestrator turns the copy-paste runbook blocks into a single reproducible
command. It reads every dataset-specific value from META/dataset_info.yml and
from the resolved input files, builds each step from the declarative tool spec
in utils/tool_commands.py, wraps the timed step with /usr/bin/time, runs it via
`docker compose run`, organizes outputs, and writes a provenance manifest.

Pilot scope: Minigraph and PGGB. Other tools become runnable by adding an entry
to utils/tool_commands.py; this file does not change per tool.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import shlex
import subprocess
import sys

import yaml

from run_config import INPUT_DATA_ROOT
from tool_registry import EXPECTED_SOURCE_BY_TOOL
from utils.dataset_common import get_sample_name_rewrites, normalize_sample_name
from utils.dataset_inspection import inspect_dataset
from utils.dataset_metadata import (
    get_dataset_short_name,
    get_metadata_value,
    load_dataset_metadata_dict,
)
from utils.input_resolution import get_tool_inputs
from utils.results_layout import (
    build_wrapped_command,
    create_results_structure,
    get_tool_logs_path,
    get_tool_outputs_path,
    get_tool_results_path,
    to_container_path,
)
from utils.tool_commands import ParamSpec, Step, ToolCommandSpec, get_tool_command_spec


REPO_ROOT = Path(__file__).resolve().parent


class OrchestratorError(Exception):
    """Raised for user-facing configuration/gating errors."""


# ---------------------------------------------------------------------------
# Gating and parameter resolution
# ---------------------------------------------------------------------------

def check_supported(tool_name: str, report: dict) -> None:
    """
    Fail unless the dataset declares this tool in supported_workflows.

    This promotes supported_workflows from documentation to a real execution
    gate. The workflow key is the lowercased tool name.
    """
    supported = report.get("supported_workflows", {})
    workflow_key = tool_name.lower()

    if isinstance(supported, dict):
        allowed = supported.get(workflow_key, False)
    else:  # legacy list form
        allowed = workflow_key in {str(item).lower() for item in supported}

    if not allowed:
        raise OrchestratorError(
            f"{tool_name} is not enabled for this dataset "
            f"(supported_workflows.{workflow_key} is not true)."
        )


def resolve_params(specs: tuple[ParamSpec, ...], metadata: dict) -> dict:
    """
    Resolve declared metadata parameters, failing on missing required ones.
    """
    resolved: dict = {}
    for spec in specs:
        value = get_metadata_value(metadata, spec.metadata_key)
        if value is None and spec.fallback_key:
            value = get_metadata_value(metadata, spec.fallback_key)
        if value is None:
            if spec.required:
                keys = spec.metadata_key
                if spec.fallback_key:
                    keys += f"' or '{spec.fallback_key}"
                raise OrchestratorError(
                    f"required parameter '{spec.name}' missing: set "
                    f"'{keys}' in META/dataset_info.yml."
                )
            value = spec.default
        resolved[spec.name] = value
    return resolved


# ---------------------------------------------------------------------------
# PanSN preparation (shared by PGGB/POASTA/Theseus)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Render context
# ---------------------------------------------------------------------------

def build_render_context(
    tool_name: str,
    spec: ToolCommandSpec,
    dataset_name: str,
    report: dict,
    metadata: dict,
) -> dict:
    """
    Assemble every value the step templates can reference for this run.
    """
    dataset_short = get_dataset_short_name(INPUT_DATA_ROOT / dataset_name)
    dataset_path = Path(report["dataset_path"])
    assemblies_dir = dataset_path / "ASSEMBLIES"

    out_dir_host = get_tool_outputs_path(dataset_name, tool_name)
    out_dir = to_container_path(out_dir_host)

    # Resolved input files (host paths -> container paths).
    tool_inputs = get_tool_inputs(tool_name, report)
    if not tool_inputs["resolved"]:
        reason = tool_inputs["reason"] or "inputs could not be resolved"
        missing = ", ".join(tool_inputs.get("missing", []))
        raise OrchestratorError(f"{tool_name}: {reason} [{missing}]")

    inputs_container: dict = {}
    for key, value in tool_inputs["inputs"].items():
        if isinstance(value, list):
            inputs_container[key] = [_input_to_container(p) for p in value]
        else:
            inputs_container[key] = _input_to_container(value)

    context: dict = {
        "dataset": dataset_name,
        "dataset_short": dataset_short,
        "tool": tool_name,
        "out_dir": out_dir,
        "out_dir_host": str(out_dir_host),
        "assemblies_dir": str(assemblies_dir),
        "inputs": inputs_container,
        "canonical_gfa": f"{out_dir}/{tool_name.lower()}_{dataset_short}.gfa",
        "canonical_hal": f"{out_dir}/{tool_name.lower()}_{dataset_short}.hal",
        # Seqfile: host path for the host-side generator, container path for the
        # in-container cactus run.
        "seqfile_host": str(out_dir_host / f"{dataset_name.lower()}_seqfile.txt"),
        "seqfile": f"{out_dir}/{dataset_name.lower()}_seqfile.txt",
        # Toil jobstore (host path) — removed pre-run for tools that declare it
        # in clean_before_run, so a half-built jobstore from a failed run does
        # not block the next one.
        "jobstore_host": str(out_dir_host / "jobstore"),
    }

    # Tool-specific derived context (e.g. joined assembly list for Minigraph).
    if spec.context_builder is not None:
        context.update(spec.context_builder(context))

    # NOTE: PanSN-based tools (PGGB/POASTA/Theseus) are not modeled here yet;
    # their PanSN preparation (utils/make_pansn.py) is ready but not wired,
    # pending a suite-wide sample-naming convention. See utils/tool_commands.py.

    # Metadata params (e.g. threads / max_cores). Resolve before tool-specific
    # context that depends on them (e.g. MC_vg needs ref_name).
    context.update(resolve_params(spec.params, metadata))

    # MC_vg: the vg-autoindex reference FASTA is the assembly whose sample name
    # equals ref_name. Resolve it agnostically via normalize_sample_name (same
    # naming used everywhere else), so no dataset-specific path is hardcoded.
    if tool_name == "MC_vg":
        context["ref_fasta_host"] = _resolve_reference_fasta(
            dataset_path, context["ref_name"]
        )

    return context


def _resolve_reference_fasta(dataset_path: Path, ref_name: str) -> str:
    """
    Find the assembly FASTA whose derived sample name equals ref_name.

    Reuses normalize_sample_name + the dataset's rewrites, so the reference is
    identified the same way samples are named everywhere else (agnostic; no
    hardcoded per-dataset path). Prefers ASSEMBLIES; falls back to the sanitized
    copies used by Cactus-family (some datasets keep real files only there).
    """
    from utils.dataset_common import find_fasta_files, get_sample_name_rewrites, normalize_sample_name

    rewrites = get_sample_name_rewrites(REPO_ROOT, dataset_path.name)
    for subdir in ("ASSEMBLIES", "ASSEMBLIES_CACTUS_SANITIZED"):
        directory = dataset_path / subdir
        if not directory.is_dir():
            continue
        for fasta in find_fasta_files(directory):
            if normalize_sample_name(fasta, rewrites) == ref_name:
                return str(fasta)
    raise OrchestratorError(
        f"MC_vg: no assembly found whose sample name is '{ref_name}' "
        f"(reference_name in metadata). Checked ASSEMBLIES and sanitized copies."
    )


def _input_to_container(host_path: str) -> str:
    """
    Map a resolved input file (host path under input_data/) to its container path.

    Do NOT resolve symlinks: for some datasets (e.g. C4_TEST) ASSEMBLIES/ is a
    symlink view of ASSEMBLIES_CACTUS_SANITIZED/, and the container mount exposes
    the logical ``/input_data/<DATASET>/ASSEMBLIES/...`` path. Resolving would
    rewrite the path to the physical directory, which may not match the mount.
    """
    candidate = Path(host_path)
    for root in (INPUT_DATA_ROOT, INPUT_DATA_ROOT.resolve()):
        try:
            rel = candidate.relative_to(root)
            return f"/input_data/{rel.as_posix()}"
        except ValueError:
            continue
    # Fallback: last resort, resolve both sides.
    rel = candidate.resolve().relative_to(INPUT_DATA_ROOT.resolve())
    return f"/input_data/{rel.as_posix()}"


# ---------------------------------------------------------------------------
# Step rendering
# ---------------------------------------------------------------------------

def render_step(step: Step, context: dict, dataset_name: str, tool_name: str) -> str:
    """
    Render one step's shell command.

    The timed step is wrapped by /usr/bin/time. A ``workdir`` is prepended as an
    unmeasured ``cd`` OUTSIDE the timing wrap, so the measurement covers only the
    tool binary (matching the runbook policy).
    """
    try:
        command = step.template.format(**context)
    except KeyError as error:
        raise OrchestratorError(
            f"step '{step.label or step.kind}' references unknown field {error}."
        )

    if step.timed and not step.host:
        command = build_wrapped_command(
            dataset_name, tool_name, command, timing_log_name=step.timing_log
        )

    if step.workdir:
        command = f"cd {shlex.quote(step.workdir)} && {command}"

    return command


def step_service(step: Step, spec: ToolCommandSpec) -> str:
    """Return the compose service for a step (step override or tool default)."""
    return step.service or spec.service


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def plan_run(
    dataset_name: str,
    tool_name: str,
    skip_optional: bool,
) -> tuple[ToolCommandSpec, dict, list[tuple[Step, str, str]]]:
    """
    Build the full execution plan without running anything.

    Returns (spec, context, [(step, service, rendered_command), ...]).
    """
    dataset_path = INPUT_DATA_ROOT / dataset_name
    if not dataset_path.is_dir():
        raise OrchestratorError(f"dataset not found: {dataset_path}")

    report = inspect_dataset(dataset_path)

    # Gate on the dataset's declared workflows BEFORE checking whether the tool
    # is modeled: a disabled tool should report "not enabled for this dataset",
    # not "not modeled yet".
    check_supported(tool_name, report)

    spec = get_tool_command_spec(tool_name)
    if spec is None:
        raise OrchestratorError(
            f"no command spec for '{tool_name}' yet "
            f"(modeled tools: add an entry in utils/tool_commands.py)."
        )

    metadata = load_dataset_metadata_dict(dataset_path)
    context = build_render_context(tool_name, spec, dataset_name, report, metadata)

    planned: list[tuple[Step, str, str]] = []
    for step in spec.steps:
        if step.optional and skip_optional:
            continue
        command = render_step(step, context, dataset_name, tool_name)
        planned.append((step, step_service(step, spec), command))

    return spec, context, planned


def compose_run_command(service: str, inner_command: str) -> list[str]:
    """
    Build the `docker compose run` argv for one step's inner command.
    """
    return [
        "docker", "compose", "run", "--rm", "-T", service,
        "bash", "-lc", inner_command,
    ]


def _tool_version(tool_name: str) -> dict:
    """
    Read the pinned source/ref for a tool from tools_config.yml (best effort).
    """
    config_path = REPO_ROOT / "tools_config.yml"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    entry = config.get(tool_name, {})
    return {"source": entry.get("source"), "ref": entry.get("ref")}


def build_manifest(
    dataset_name: str,
    tool_name: str,
    spec: ToolCommandSpec,
    context: dict,
    planned: list[tuple[Step, str, str]],
) -> dict:
    """
    Build the provenance manifest for one run.

    Records what was run and with which inputs/params/versions so a produced
    graph can be traced back to (tool@version, dataset, parameters). This is the
    third reproducibility layer (environment=pinning, execution=orchestrator,
    result=this manifest).
    """
    return {
        "dataset": dataset_name,
        "dataset_short": context.get("dataset_short"),
        "tool": tool_name,
        "tool_version": _tool_version(tool_name),
        "service": spec.service,
        "params": {p.name: context.get(p.name) for p in spec.params},
        "pggb_n_note": (
            "derived at run time via grep -c '^>' on the PanSN input"
            if tool_name == "PGGB"
            else None
        ),
        "canonical_output": context.get("canonical_gfa"),
        "steps": [
            {
                "index": index,
                "kind": step.kind,
                "label": step.label,
                "timed": step.timed,
                "optional": step.optional,
                "service": service,
                "command": command,
            }
            for index, (step, service, command) in enumerate(planned, start=1)
        ],
    }


def write_manifest(dataset_name: str, tool_name: str, manifest: dict) -> Path:
    """
    Write the run manifest next to the tool's results.
    """
    logs_dir = get_tool_logs_path(dataset_name, tool_name)
    logs_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = logs_dir / "run_manifest.yml"
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return manifest_path


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def canonical_output_candidates(
    dataset_name: str, tool_name: str, context: dict, spec: ToolCommandSpec
) -> list[Path]:
    """
    Host paths of the canonical output(s) to guard against overwrite.

    When the tool declares explicit ``canonical_outputs`` (MC_vg: three fixed
    filenames), guard exactly those. Otherwise use the default convention
    ``<tool>_<short>.gfa`` plus its ``.gfa.gz`` form (MinigraphCactus emits the
    compressed one as primary). A run is refused if ANY candidate already exists.
    """
    outputs = get_tool_outputs_path(dataset_name, tool_name)
    if spec.canonical_outputs:
        return [outputs / name for name in spec.canonical_outputs]
    dataset_short = context.get("dataset_short", "")
    stem = f"{tool_name.lower()}_{dataset_short}"
    return [outputs / f"{stem}.gfa", outputs / f"{stem}.gfa.gz"]


def prep_cache_is_fresh(step: Step, context: dict) -> tuple[bool, str]:
    """
    Decide whether a prep step's cached artifact is fresh and can be skipped.

    Fresh iff the cache file exists and is newer than every source path listed
    in ``cache_sources`` (or newer than every file within, for directories).
    Returns (fresh, reason).
    """
    if step.cache_key is None:
        return (False, "no cache key")

    cache_value = context.get(step.cache_key)
    if not isinstance(cache_value, str):
        return (False, "cache target not in context")

    # cache_key may be a container path (/input_data/..., /results/...) or an
    # already-host path (for host-side steps). Handle both.
    if cache_value.startswith(("/input_data/", "/results/")):
        cache_host = _container_to_host(cache_value)
    else:
        cache_host = Path(cache_value)
    if cache_host is None or not cache_host.exists():
        return (False, "cache artifact missing")

    cache_mtime = cache_host.stat().st_mtime
    newest_source = 0.0
    for source_key in step.cache_sources:
        source_value = context.get(source_key)
        if not isinstance(source_value, str):
            continue
        source_path = Path(source_value)
        if source_path.is_dir():
            for child in source_path.iterdir():
                if child.is_file():
                    newest_source = max(newest_source, child.stat().st_mtime)
        elif source_path.exists():
            newest_source = max(newest_source, source_path.stat().st_mtime)

    if cache_mtime >= newest_source:
        return (True, f"cache fresh (artifact newer than sources): {cache_host}")
    return (False, "cache stale (a source is newer)")


def _container_to_host(container_path: str) -> Path | None:
    """
    Map a /input_data or /results container path back to a host path.
    """
    if container_path.startswith("/input_data/"):
        return INPUT_DATA_ROOT / container_path[len("/input_data/"):]
    if container_path.startswith("/results/"):
        from run_config import RESULTS_ROOT
        return RESULTS_ROOT / container_path[len("/results/"):]
    return None


def clean_before_run(spec: ToolCommandSpec, context: dict) -> list[str]:
    """
    Remove directories a tool requires to be absent at start (e.g. Toil
    jobstore). Targeted: only the declared dirs, never the canonical output.

    Uses `sudo rm -rf` because Docker may have written them as root, but guards
    the path: it must live under the results tree and end in a known-safe name.
    """
    from run_config import RESULTS_ROOT
    results_root = str(RESULTS_ROOT.resolve())
    messages: list[str] = []

    for key in spec.clean_before_run:
        target = context.get(key)
        if not isinstance(target, str):
            continue
        target_abs = str(Path(target).resolve())
        # Safety: must be inside the results tree and be a jobstore dir.
        if not target_abs.startswith(results_root + "/"):
            messages.append(f"[clean] skip {target} (outside results tree)")
            continue
        if Path(target_abs).name != "jobstore":
            messages.append(f"[clean] skip {target} (not a jobstore dir)")
            continue
        if Path(target_abs).exists():
            subprocess.run(["sudo", "rm", "-rf", target_abs], check=False)
            messages.append(f"[clean] removed stale {target_abs}")
    return messages


def execute_plan(
    dataset_name: str,
    tool_name: str,
    spec: ToolCommandSpec,
    context: dict,
    planned: list[tuple[Step, str, str]],
) -> int:
    """
    Execute each planned step via `docker compose run`, stopping on first error.

    stdout/stderr of every step is appended to the tool's execution.log. Prep
    steps with a fresh cache are skipped. Returns a process exit code.
    """
    execution_log = get_tool_logs_path(dataset_name, tool_name) / "execution.log"
    execution_log.parent.mkdir(parents=True, exist_ok=True)

    # Remove directories that must be absent at start (targeted, not the output).
    for msg in clean_before_run(spec, context):
        print("    " + msg)

    with execution_log.open("w", encoding="utf-8") as log:
        for index, (step, service, command) in enumerate(planned, start=1):
            header = f"\n===== step {index} [{step.label or step.kind}] service={service} =====\n"
            log.write(header)
            log.flush()
            print(f"[{index}/{len(planned)}] {step.label or step.kind} ...", flush=True)

            if step.kind == "prep":
                fresh, reason = prep_cache_is_fresh(step, context)
                if fresh:
                    msg = f"[cache] skipping {step.label}: {reason}\n"
                    log.write(msg)
                    print("    " + msg.strip())
                    continue

            if step.host:
                # Host-side step: run locally in the repo root, not in a container.
                argv = ["bash", "-lc", command]
                result = subprocess.run(
                    argv, stdout=log, stderr=subprocess.STDOUT, cwd=str(REPO_ROOT)
                )
            else:
                argv = compose_run_command(service, command)
                result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                fail = f"[FAIL] step {index} ({step.label}) exited {result.returncode}\n"
                log.write(fail)
                print("    " + fail.strip(), file=sys.stderr)
                return result.returncode

    return 0


def fix_ownership(dataset_name: str, tool_name: str) -> None:
    """
    Reclaim ownership of container-written outputs (Docker writes as root).
    Best effort: a failure here is non-fatal (files still exist).
    """
    run_dir = get_tool_results_path(dataset_name, tool_name)
    import os
    user = os.environ.get("USER", "")
    if not user:
        return
    subprocess.run(
        ["sudo", "chown", "-R", f"{user}:{user}", str(run_dir)],
        check=False,
    )


def organize(dataset_name: str, tool_name: str) -> None:
    """
    Run organize_outputs.py on the tool's outputs directory.
    """
    outputs = get_tool_outputs_path(dataset_name, tool_name)
    subprocess.run(
        [sys.executable, "utils/organize_outputs.py", tool_name, str(outputs)],
        check=False,
        cwd=str(REPO_ROOT),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one tool on one dataset.")
    parser.add_argument("dataset", help="Dataset name under input_data/")
    parser.add_argument("tool", help="Tool name (e.g. Minigraph, PGGB)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the rendered plan without executing anything.",
    )
    parser.add_argument(
        "--skip-optional",
        action="store_true",
        help="Skip optional (derived-output) steps.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing canonical output (otherwise the run is refused).",
    )
    args = parser.parse_args()

    try:
        spec, context, planned = plan_run(args.dataset, args.tool, args.skip_optional)
    except OrchestratorError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 2

    manifest = build_manifest(args.dataset, args.tool, spec, context, planned)

    print(f"# Plan: {args.tool} on {args.dataset}")
    print(f"# tool version: {manifest['tool_version']}")
    print(f"# service default: {spec.service}")
    for index, (step, service, command) in enumerate(planned, start=1):
        tag = f"{step.kind}{' timed' if step.timed else ''}"
        tag += " optional" if step.optional else ""
        if step.host:
            print(f"\n[{index}] ({tag} HOST)")
            print("    bash -lc " + shlex.quote(command))
        else:
            print(f"\n[{index}] ({tag}) service={service}")
            print("    " + " ".join(shlex.quote(part) for part in
                                    compose_run_command(service, command)))

    if args.dry_run:
        print("\n# --dry-run: nothing executed. Manifest preview:")
        print(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
        return 0

    # Overwrite protection: refuse to clobber a validated canonical output
    # (either the uncompressed or compressed form).
    candidates = canonical_output_candidates(args.dataset, args.tool, context, spec)
    existing = next((c for c in candidates if c.exists()), None)
    canonical = candidates[0]
    if existing is not None and not args.force:
        print(
            f"\n[ERROR] canonical output already exists: {existing}\n"
            f"        Refusing to overwrite a validated run. Re-run with --force "
            f"to override.",
            file=sys.stderr,
        )
        return 3

    # Ensure results structure exists before running.
    create_results_structure(args.dataset, [args.tool])

    print("\n# Executing ...")
    code = execute_plan(args.dataset, args.tool, spec, context, planned)

    fix_ownership(args.dataset, args.tool)

    if code != 0:
        print(f"\n[ERROR] run failed (exit {code}); see execution.log.", file=sys.stderr)
        # Still write the manifest to record what was attempted.
        write_manifest(args.dataset, args.tool, manifest)
        return code

    # Tools that declare their own canonical_outputs manage output layout via
    # their own steps (MC_vg), so skip the shared organize_outputs (which has no
    # spec for them and would fail). Others delegate to organize_outputs.
    if not spec.canonical_outputs:
        organize(args.dataset, args.tool)
    manifest_path = write_manifest(args.dataset, args.tool, manifest)
    print(f"\n# Done. Canonical output: {canonical}")
    print(f"# Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
