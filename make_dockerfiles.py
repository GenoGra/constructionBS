import yaml
import os
import shutil
from pathlib import Path

DOCKERFILES = {
    
    'cactus': '''\
FROM quay.io/comparative-genomics-toolkit/cactus:{}

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
    zlib1g-dev

RUN git clone https://github.com/lh3/minigraph.git
WORKDIR /minigraph
RUN git checkout {}
RUN make

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    ''',

    'minigraphcactus': '''\
FROM quay.io/comparative-genomics-toolkit/cactus:{}

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    ''',

    'pggb': '''\
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    git \
    make \
    curl \
    wget \
    python3 \
    python3-pip \
    bash

RUN git clone https://github.com/pangenome/pggb.git
WORKDIR /pggb
RUN git checkout {}
RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    ''',

    'progressivecactus': '''\
FROM quay.io/comparative-genomics-toolkit/cactus:{}

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    '''
}

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

    for tool in config:
        os.chdir(os.path.join(DOCKERFILES_FOLDER, tool))
        file_tmp = open('Dockerfile', 'w')
        file_tmp.write(DOCKERFILES[tool.lower()].format(config[tool]['version']))
        file_tmp.close()

    print('\nSuccessfully created dockerfiles for the following tools:')
    for tool in config:
        print(f'\t{tool}')
    print()

if __name__ == '__main__':
    main()