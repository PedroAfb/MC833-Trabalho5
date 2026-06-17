# ---- Estágio de build: só existe para compilar o binário ----
FROM ubuntu:20.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY server.c .
# -fno-stack-protector: desliga stack canary
# -z execstack: permite executar código na pilha (necessário para o shellcode)
RUN gcc -fno-stack-protector -z execstack -o server server.c

# ---- Estágio de runtime: só o necessário para rodar o serviço vulnerável ----
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends socat iproute2 gdb netcat python3 python3-pip gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /build/server ./server
RUN echo false > /app/infectado.txt
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 9090
# entrypoint.sh configura rota default e em seguida faz `exec setarch x86_64 -R "$@"`,
# desligando ASLR para o CMD e qualquer processo lançado dentro do container.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["socat", "TCP-LISTEN:9090,reuseaddr,fork", "EXEC:./server"]
