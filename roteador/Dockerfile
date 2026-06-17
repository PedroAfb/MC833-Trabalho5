FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends iproute2 iputils-ping && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
CMD ["sleep", "infinity"]
