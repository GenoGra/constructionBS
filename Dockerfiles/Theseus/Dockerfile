FROM ubuntu:24.04

RUN apt-get update && apt-get install -y     git     build-essential     cmake     zlib1g-dev     time     bash     && rm -rf /var/lib/apt/lists/*

RUN git clone --recursive https://github.com/albertjimenezbl/theseus-lib.git /theseus-lib
WORKDIR /theseus-lib
RUN git checkout 45e6471a398090dd87462b187d93432062e49de8
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF
RUN cmake --build build --parallel
RUN cmake --install build
RUN ln -sf /theseus-lib/build/tools/theseus_msa /usr/local/bin/theseus_msa
RUN ln -sf /theseus-lib/build/tools/theseus_aligner /usr/local/bin/theseus_aligner

RUN mkdir -p /results /input_data

CMD ["/bin/bash"]

    