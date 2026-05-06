"""
Central registry describing supported tools and their shared metadata.
"""

from __future__ import annotations


COMMON_VOLUMES = [
    {"type": "bind", "source": "./results", "target": "/results"},
    {"type": "bind", "source": "./input_data", "target": "/input_data"},
]


TOOL_REGISTRY = {
    "Cactus": {
        "source": "image",
        "service": {
            "service_name": "cactus",
            "dockerfile": "Dockerfiles/Cactus/Dockerfile",
            "command": "mkdir -p /results && cactus --help > /results/cactus_help.txt 2>&1",
        },
        "requirements": {"required_dirs": ["ASSEMBLIES", "META"]},
        "input_specs": {
            "assemblies": {"source": "ASSEMBLIES", "mode": "many", "min_count": 2},
        },
    },
    "Minigraph": {
        "source": "git",
        "service": {
            "service_name": "minigraph",
            "dockerfile": "Dockerfiles/Minigraph/Dockerfile",
            "command": (
                "mkdir -p /results && cd /minigraph && "
                "./minigraph > /results/minigraph_help.txt 2>&1 || true"
            ),
        },
        "requirements": {"required_dirs": ["ASSEMBLIES", "META"]},
        "input_specs": {
            "assemblies": {"source": "ASSEMBLIES", "mode": "many", "min_count": 2},
        },
    },
    "MinigraphCactus": {
        "source": "image",
        "service": {
            "service_name": "minigraphcactus",
            "dockerfile": "Dockerfiles/MinigraphCactus/Dockerfile",
            "command": (
                "mkdir -p /results && "
                "cactus-pangenome --help > /results/minigraphcactus_help.txt 2>&1"
            ),
        },
        "requirements": {"required_dirs": ["ASSEMBLIES", "META"]},
        "input_specs": {
            "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
        },
    },
    "PGGB": {
        "source": "image",
        "service": {
            "service_name": "pggb",
            "dockerfile": "Dockerfiles/PGGB/Dockerfile",
            "command": "mkdir -p /results && pggb --help > /results/pggb_help.txt 2>&1 || true",
        },
        "requirements": {"required_dirs": ["ASSEMBLIES", "META"]},
        "input_specs": {
            "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
        },
    },
    "ProgressiveCactus": {
        "source": "image",
        "service": {
            "service_name": "progressivecactus",
            "dockerfile": "Dockerfiles/ProgressiveCactus/Dockerfile",
            "command": (
                "mkdir -p /results && "
                "cactus --help > /results/progressivecactus_help.txt 2>&1"
            ),
        },
        "requirements": {"required_dirs": ["ASSEMBLIES", "META"]},
        "input_specs": {
            "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
        },
    },
    "LCPan": {
        "source": "git",
        "service": {
            "service_name": "lcpan",
            "dockerfile": "Dockerfiles/LCPan/Dockerfile",
            "command": (
                "mkdir -p /results && "
                "/lcpan/bin/lcpan --help > /results/lcpan_help.txt 2>&1 || true"
            ),
        },
        "requirements": {"required_dirs": ["ASSEMBLIES", "GRAPH", "META"]},
        "input_specs": {
            "reference": {"source": "ASSEMBLIES", "mode": "single", "name_pattern": "*_total.fa"},
            "variants": {"source": "GRAPH", "mode": "single", "name_pattern": "lcpan_*.vcf"},
        },
    },
}


EXPECTED_SOURCE_BY_TOOL = {
    tool_name: tool_spec["source"]
    for tool_name, tool_spec in TOOL_REGISTRY.items()
}

TOOL_SERVICE_SPECS = {
    tool_name: tool_spec["service"]
    for tool_name, tool_spec in TOOL_REGISTRY.items()
}

TOOL_REQUIREMENTS = {
    tool_name: tool_spec["requirements"]
    for tool_name, tool_spec in TOOL_REGISTRY.items()
}

TOOL_INPUT_SPECS = {
    tool_name: tool_spec["input_specs"]
    for tool_name, tool_spec in TOOL_REGISTRY.items()
}
