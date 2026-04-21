TOOL_REQUIREMENTS = {
    "Cactus": {
        "required_dirs": ["ASSEMBLIES", "META"],
    },
    "Minigraph": {
        "required_dirs": ["ASSEMBLIES", "META"],
    },
    "MinigraphCactus": {
        "required_dirs": ["ASSEMBLIES", "META"],
    },
    "PGGB": {
        "required_dirs": ["ASSEMBLIES", "META"],
    },
    "ProgressiveCactus": {
        "required_dirs": ["ASSEMBLIES", "TREE", "META"],
    },
}

EXPECTED_FILE_TYPES = {
    "ASSEMBLIES": [".fa", ".fasta", ".fna"],
    "GRAPH": [".gfa", ".rgfa"],
    "READS": [".fa", ".fasta", ".fq", ".fastq", ".txt"],
    "TREE": [".nwk", ".newick", ".tree"],
}

TOOL_INPUT_SPECS = {
    "Cactus": {
        "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
    },
    "Minigraph": {
        "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
    },
    "MinigraphCactus": {
        "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
    },
    "PGGB": {
        "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
    },
    "ProgressiveCactus": {
        "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
        "tree": {"source": "TREE", "mode": "single"},
    },
}