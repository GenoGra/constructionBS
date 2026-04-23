FROM ubuntu:22.04

RUN apt-get update && apt-get install -y     git     make     curl     wget     python3     python3-pip     bash     time

RUN git clone https://github.com/pangenome/pggb.git
WORKDIR /pggb
RUN git checkout e25486b
RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    