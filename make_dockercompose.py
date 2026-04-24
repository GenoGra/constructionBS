"""
Generate the project ``docker-compose.yml`` from ``tools_config.yml`` and
prepare per-dataset results folders after checking dataset readiness.
"""

from pathlib import Path

import yaml

from dataset_utils import create_results_structure, find_datasets, inspect_dataset


COMMON_VOLUMES = [
    {"type": "bind", "source": "./results", "target": "/results"},
    {"type": "bind", "source": "./input_data", "target": "/input_data"},
]

TOOL_SERVICE_SPECS = {
    "Cactus": {
        "service_name": "cactus",
        "dockerfile": "Dockerfiles/Cactus/Dockerfile",
        "command": "mkdir -p /results && cactus-pangenome --help > /results/cactus_pangenome_help.txt 2>&1",
    },
    "Minigraph": {
        "service_name": "minigraph",
        "dockerfile": "Dockerfiles/Minigraph/Dockerfile",
        "command": "mkdir -p /results && cd /minigraph && ./minigraph > /results/minigraph_help.txt 2>&1 || true",
    },
    "MinigraphCactus": {
        "service_name": "minigraphcactus",
        "dockerfile": "Dockerfiles/MinigraphCactus/Dockerfile",
        "command": "mkdir -p /results && cactus-pangenome --help > /results/minigraphcactus_help.txt 2>&1",
    },
    "PGGB": {
        "service_name": "pggb",
        "dockerfile": "Dockerfiles/PGGB/Dockerfile",
        "command": "mkdir -p /results && cd /pggb && ./pggb --help > /results/pggb_help.txt 2>&1 || true",
    },
    "ProgressiveCactus": {
        "service_name": "progressivecactus",
        "dockerfile": "Dockerfiles/ProgressiveCactus/Dockerfile",
        "command": "mkdir -p /results && cactus --help > /results/progressivecactus_help.txt 2>&1",
    },
}


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


def main() -> None:
    """
    Generate docker-compose.yml from tools configuration and check dataset readiness.
    """
    with open("tools_config.yml", "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    compose_config = {"services": build_docker_compose_services(config)}
    with open("docker-compose.yml", "w", encoding="utf-8") as file_tmp:
        yaml.safe_dump(compose_config, file_tmp, sort_keys=False)

    print("\nSuccessfully created docker-compose.yml for help tests.\n")

    input_data_path = Path("input_data")
    datasets = find_datasets(input_data_path)
    ready_datasets = []
    for dataset_path in datasets:
        report = inspect_dataset(dataset_path)
        if report["structure"]["structure_ok"] and report["ready_for_real_runs"]:
            ready_datasets.append(report)

    if not ready_datasets:
        print("\nNo datasets ready for real runs. Generating help-only docker-compose.\n")

    for dataset_path in datasets:
        create_results_structure(dataset_path.name, list(config.keys()))

    if datasets:
        print("Results structure ensured for detected datasets.\n")


if __name__ == "__main__":
    main()
