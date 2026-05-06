"""
Central configuration describing expected dataset file types and tool input
requirements derived from the shared tool registry.
"""

from tool_registry import TOOL_INPUT_SPECS, TOOL_REQUIREMENTS


EXPECTED_FILE_TYPES = {
    "ASSEMBLIES": [".fa", ".fasta", ".fna"],
    "GRAPH": [".gfa", ".rgfa", ".vcf"],
    "READS": [".fa", ".fasta", ".fq", ".fastq", ".txt"],
    "TREE": [".nwk", ".newick", ".tree"],
}
