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
    "MC_vg": {
        # MC_vg is a Minigraph-Cactus-derived, reference-centric indexing branch
        # (cactus-pangenome --vcf/--giraffe/--gbz then vg autoindex). It runs in
        # the same minigraphcactus image and consumes the same ASSEMBLIES inputs.
        "source": "image",
        "service": {
            "service_name": "minigraphcactus",
            "dockerfile": "Dockerfiles/MinigraphCactus/Dockerfile",
            "command": (
                "mkdir -p /results && "
                "cactus-pangenome --help > /results/mc_vg_help.txt 2>&1"
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
    "Theseus": {
        "source": "git",
        "service": {
            "service_name": "theseus",
            "dockerfile": "Dockerfiles/Theseus/Dockerfile",
            "command": (
                "mkdir -p /results && "
                "theseus_msa > /results/theseus_help.txt 2>&1 || true"
            ),
        },
        "requirements": {"required_dirs": ["ASSEMBLIES", "META"]},
        "input_specs": {
            "assemblies": {"source": "ASSEMBLIES", "mode": "many", "min_count": 2},
        },
    },

    "POASTA": {
        "source": "git",
        "service": {
            "service_name": "poasta",
            "dockerfile": "Dockerfiles/POASTA/Dockerfile",
            "command": (
                "mkdir -p /results && "
                "poasta align --help > /results/poasta_help.txt 2>&1 || true"
            ),
        },
        "requirements": {"required_dirs": ["ASSEMBLIES", "META"]},
        "input_specs": {
            "assemblies": {"source": "ASSEMBLIES", "mode": "many", "min_count": 2},
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
            "reference": {
                "source": "GRAPH",
                "mode": "single",
                "name_pattern": "*_reference_pansn.fa",
            },
            "variants": {"source": "GRAPH", "mode": "single", "name_pattern": "lcpan_*.vcf"},
        },
    },
    "vg": {
        # vg toolkit as an independent tool. Its construction inputs (reference
        # FASTA + VCF + GFA-with-W-lines) are the OUTPUTS of a prior MinigraphCactus
        # run (result_cactus_new.{vcf.gz,gfa.gz}), so vg has no input_specs sourced
        # from input_data/ — the orchestrator resolves its inputs from the
        # MinigraphCactus results directory (see TOOL_COMMANDS["MC_vg"]). The tool
        # runs in its OWN pinned image (quay.io/vgteam/vg), not in the cactus image.
        "source": "image",
        "service": {
            "service_name": "vg",
            "dockerfile": "Dockerfiles/vg/Dockerfile",
            "command": "mkdir -p /results && vg version > /results/vg_help.txt 2>&1 || true",
        },
        "requirements": {"required_dirs": ["META"]},
        "input_specs": {},
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
