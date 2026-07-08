FROM ubuntu:24.04@sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90

RUN apt-get update && apt-get install -y     git     build-essential     cmake     zlib1g-dev     time     bash     && rm -rf /var/lib/apt/lists/*

RUN git clone --recursive https://github.com/albertjimenezbl/theseus-lib.git /theseus-lib
WORKDIR /theseus-lib
RUN git checkout f59b35f66707be01bf664524d2a67b5983ac8f5e
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF
RUN cmake --build build --parallel
RUN cmake --install build
RUN ln -sf /theseus-lib/build/tools/theseus_msa /usr/local/bin/theseus_msa
RUN ln -sf /theseus-lib/build/tools/theseus_aligner /usr/local/bin/theseus_aligner

RUN mkdir -p /results /input_data

CMD ["/bin/bash"]

    