FROM ubuntu:22.04

RUN apt-get update && apt-get install -y     git     make     g++     zlib1g-dev     time

RUN git clone https://github.com/lh3/minigraph.git
WORKDIR /minigraph
RUN git checkout v0.21
RUN make

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    