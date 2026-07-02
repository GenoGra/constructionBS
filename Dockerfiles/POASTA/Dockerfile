FROM rust:1.86-slim@sha256:57d415bbd61ce11e2d5f73de068103c7bd9f3188dc132c97cef4a8f62989e944

RUN apt-get update && apt-get install -y     git     build-essential     time     bash     && rm -rf /var/lib/apt/lists/*

ENV RUSTFLAGS="-C target-cpu=native"
RUN cargo install --locked --git https://github.com/broadinstitute/poasta --rev c9009a1444538adc5418f0e0d9b189565d109600 --root /usr/local

RUN mkdir -p /results /input_data

CMD ["/bin/bash"]

    