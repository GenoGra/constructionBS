FROM ubuntu:22.04

RUN apt-get update && apt-get install -y     git     make     gcc     g++     zlib1g-dev     time     bash     && rm -rf /var/lib/apt/lists/*

RUN git clone --recursive https://github.com/BilkentCompGen/lcpan.git /lcpan
WORKDIR /lcpan
RUN git checkout v1.1
RUN git submodule update --init --recursive
RUN make install && make

RUN mkdir -p /results /input_data

ENV PATH="/lcpan:${PATH}"

CMD ["/bin/bash"]
    
    