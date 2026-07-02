FROM ubuntu:22.04@sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982

RUN apt-get update && apt-get install -y     git     make     gcc     g++     zlib1g-dev     time     bash     && rm -rf /var/lib/apt/lists/*

RUN git clone --recursive https://github.com/BilkentCompGen/lcpan.git /lcpan
WORKDIR /lcpan
RUN git checkout 8cb89b5013f034e86f8f6aab3a328aab22494c63
RUN git submodule update --init --recursive
RUN make install && make

RUN mkdir -p /results /input_data

ENV PATH="/lcpan:${PATH}"

CMD ["/bin/bash"]
    
    