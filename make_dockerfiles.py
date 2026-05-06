"""
Create Dockerfiles for each configured tool reference using the templates defined
in this module and the refs declared in ``tools_config.yml``.
"""

import os
import shutil
from pathlib import Path
import yaml

from tool_registry import EXPECTED_SOURCE_BY_TOOL

DOCKERFILES = {
    
    'cactus': '''\
FROM quay.io/comparative-genomics-toolkit/cactus{}

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    ''',

    'minigraph': '''\
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git \
    make \
    g++ \
    zlib1g-dev \
    time

RUN git clone https://github.com/lh3/minigraph.git
WORKDIR /minigraph
RUN git checkout {}
RUN make

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    ''',

    'minigraphcactus': '''\
FROM quay.io/comparative-genomics-toolkit/cactus{}

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    ''',

    'pggb': '''\
FROM ghcr.io/pangenome/pggb{}

RUN mkdir -p /results /input_data

CMD ["/bin/bash"]

    ''',

    'progressivecactus': '''\
FROM quay.io/comparative-genomics-toolkit/cactus{}

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    ''',

    'lcpan': '''\
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \\
    git \\
    make \\
    gcc \\
    g++ \\
    zlib1g-dev \\
    time \\
    bash \\
    && rm -rf /var/lib/apt/lists/*

RUN git clone --recursive https://github.com/BilkentCompGen/lcpan.git /lcpan
WORKDIR /lcpan
RUN git checkout {}
RUN git submodule update --init --recursive
RUN make install && make

RUN mkdir -p /results /input_data

ENV PATH="/lcpan:${{PATH}}"

CMD ["/bin/bash"]
    
    '''
}

def resolve_ref(tool_name: str, tool_config: dict) -> str:
    """
    Read the canonical ``ref`` field, keeping backward compatibility with
    legacy ``version`` entries.
    """
    ref = tool_config.get("ref", tool_config.get("version"))
    if not ref:
        raise ValueError(f"{tool_name}: missing 'ref' in tools_config.yml")
    return str(ref)


def validate_source(tool_name: str, tool_config: dict) -> None:
    """
    Validate optional source metadata so config stays explicit and consistent.
    """
    declared_source = tool_config.get("source")
    expected_source = EXPECTED_SOURCE_BY_TOOL.get(tool_name)
    if not expected_source:
        raise ValueError(f"{tool_name}: unsupported tool in make_dockerfiles.py")
    if declared_source and declared_source != expected_source:
        raise ValueError(
            f"{tool_name}: source '{declared_source}' does not match expected "
            f"'{expected_source}' for this Dockerfile template"
        )


def build_template_ref(tool_name: str, tool_config: dict) -> str:
    """
    Build the string inserted into FROM/checkouts from a canonical ref.
    Image refs support both tags and digests.
    """
    ref = resolve_ref(tool_name, tool_config)
    source = tool_config.get("source", EXPECTED_SOURCE_BY_TOOL[tool_name])

    if source == "image":
        if ref.startswith("sha256:"):
            return f"@{ref}"
        if ref.startswith("@"):
            return ref
        return f":{ref}"
    return ref


def main():
    with open('tools_config.yml', 'r') as file:
        config = yaml.safe_load(file)

    if not os.path.exists('Dockerfiles'):
        os.makedirs('Dockerfiles')

    DOCKERFILES_FOLDER = os.path.join(os.getcwd(), 'Dockerfiles')
    os.chdir(DOCKERFILES_FOLDER)

    folder_list = [f for f in Path(DOCKERFILES_FOLDER).glob('**/*') if not f.is_file()]
    for dir in folder_list:
        shutil.rmtree(os.path.join(DOCKERFILES_FOLDER, dir))

    for tool in config:
        os.makedirs(tool)

    for tool, tool_config in config.items():
        validate_source(tool, tool_config)
        ref = build_template_ref(tool, tool_config)
        os.chdir(os.path.join(DOCKERFILES_FOLDER, tool))
        with open('Dockerfile', 'w') as file_tmp:
            file_tmp.write(DOCKERFILES[tool.lower()].format(ref))

    print('\nSuccessfully created dockerfiles for the following tools:')
    for tool in config:
        print(f'\t{tool}')
    print()

if __name__ == '__main__':
    main()
