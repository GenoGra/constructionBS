FROM rust:1.86-slim

RUN apt-get update && apt-get install -y     git     build-essential     time     bash     && rm -rf /var/lib/apt/lists/*

ENV RUSTFLAGS="-C target-cpu=native"
RUN cargo install --locked --git https://github.com/broadinstitute/poasta --tag v0.1.0 --root /usr/local

RUN mkdir -p /results /input_data

CMD ["/bin/bash"]

    