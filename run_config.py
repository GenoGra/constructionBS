"""
Central configuration describing which dataset directories and input file types
each tool requires, plus how tool inputs should be resolved from a dataset.
"""

ASSEMBLIES_META_REQUIRED_DIRS = ["ASSEMBLIES", "META"]
ASSEMBLIES_INPUT_SPEC = {
    "assemblies": {"source": "ASSEMBLIES", "mode": "many"},
}

ASSEMBLIES_ONLY_TOOLS = (
    "Cactus",
    "Minigraph",
    "MinigraphCactus",
    "PGGB",
)

TOOL_REQUIREMENTS = {
    tool_name: {"required_dirs": ASSEMBLIES_META_REQUIRED_DIRS.copy()}
    for tool_name in ASSEMBLIES_ONLY_TOOLS
}
TOOL_REQUIREMENTS["ProgressiveCactus"] = {
    "required_dirs": ["ASSEMBLIES", "TREE", "META"],
}

EXPECTED_FILE_TYPES = {
    "ASSEMBLIES": [".fa", ".fasta", ".fna"],
    "GRAPH": [".gfa", ".rgfa"],
    "READS": [".fa", ".fasta", ".fq", ".fastq", ".txt"],
    "TREE": [".nwk", ".newick", ".tree"],
}

TOOL_INPUT_SPECS = {
    tool_name: ASSEMBLIES_INPUT_SPEC.copy()
    for tool_name in ASSEMBLIES_ONLY_TOOLS
}
TOOL_INPUT_SPECS["Cactus"] = {
    "assemblies": {"source": "ASSEMBLIES", "mode": "many", "min_count": 2},
}
TOOL_INPUT_SPECS["Minigraph"] = {
    "assemblies": {"source": "ASSEMBLIES", "mode": "many", "min_count": 2},
}
TOOL_INPUT_SPECS["ProgressiveCactus"] = {
    **ASSEMBLIES_INPUT_SPEC,
    "tree": {"source": "TREE", "mode": "single"},
}
