FROM ubuntu:22.04

RUN apt-get update && apt-get install -y     git     make     g++     zlib1g-dev

RUN git clone https://github.com/lh3/minigraph.git
WORKDIR /minigraph
RUN git checkout 7e3e65c
RUN make

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    