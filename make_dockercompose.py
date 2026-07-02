"""
Generate the project ``docker-compose.yml`` from ``tools_config.yml`` and
prepare per-dataset results folders after checking dataset readiness.
"""

from pathlib import Path

import yaml

from tool_registry import COMMON_VOLUMES, TOOL_SERVICE_SPECS
from utils.dataset_inspection import find_datasets, inspect_dataset
from utils.results_layout import create_results_structure


def build_service_definition(tool_name: str) -> tuple[str, dict]:
    """
    Build one docker-compose service definition from the tool spec.
    """
    spec = TOOL_SERVICE_SPECS.get(tool_name)
    if spec is None:
        raise ValueError(f"No service template defined for {tool_name}")

    return spec["service_name"], {
        "stdin_open": True,
        "tty": True,
        "build": {
            "context": "./",
            "dockerfile": spec["dockerfile"],
        },
        "volumes": [volume.copy() for volume in COMMON_VOLUMES],
        "command": ["/bin/bash", "-c", spec["command"]],
    }


def build_docker_compose_services(config: dict) -> dict[str, dict]:
    """
    Build all docker-compose services for the configured tools.
    """
    services: dict[str, dict] = {}

    for tool_name in config:
        service_name, service_definition = build_service_definition(tool_name)
        services[service_name] = service_definition

    return services


def write_docker_compose(config: dict, output_path: Path = Path("docker-compose.yml")) -> None:
    """
    Generate docker-compose.yml from the selected tool configuration.
    """
    compose_config = {"services": build_docker_compose_services(config)}
    with open(output_path, "w", encoding="utf-8") as file_tmp:
        yaml.safe_dump(compose_config, file_tmp, sort_keys=False)


def discover_ready_datasets(input_data_path: Path) -> list[dict]:
    """
    Return reports for datasets that are ready for real runs.
    """
    ready_datasets = []
    for dataset_path in find_datasets(input_data_path):
        report = inspect_dataset(dataset_path)
        if report["structure"]["structure_ok"] and report["ready_for_real_runs"]:
            ready_datasets.append(report)
    return ready_datasets


def bootstrap_results_structure(input_data_path: Path, tool_names: list[str]) -> list[Path]:
    """
    Ensure the standard results structure exists for every detected dataset.
    """
    datasets = find_datasets(input_data_path)
    for dataset_path in datasets:
        create_results_structure(dataset_path.name, tool_names)
    return datasets


def main() -> None:
    """
    Generate docker-compose.yml from tools configuration and check dataset readiness.
    """
    with open("tools_config.yml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    write_docker_compose(config)
    print("\nSuccessfully created docker-compose.yml for help tests.\n")

    input_data_path = Path("input_data")
    ready_datasets = discover_ready_datasets(input_data_path)

    if not ready_datasets:
        print("\nNo datasets ready for real runs. Generating help-only docker-compose.\n")

    datasets = bootstrap_results_structure(input_data_path, list(config.keys()))

    if datasets:
        print("Results structure ensured for detected datasets.\n")


if __name__ == "__main__":
    main()
