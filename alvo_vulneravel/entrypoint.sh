#!/bin/bash
set -e

# Aponta o default gateway para o roteador interno do lab (.254 da subnet local).
# Isso permite que tráfego para outras sub-redes (172.28.0.0/16) seja roteado
# através do container 'roteador'.
IFACE_IP=$(ip -4 -o addr show eth0 | awk '{print $4}' | cut -d/ -f1)
SUBNET_PREFIX=$(echo "$IFACE_IP" | cut -d. -f1-3)
ROUTER_IP="${SUBNET_PREFIX}.254"

ip route del default 2>/dev/null || true
ip route add default via "$ROUTER_IP" 2>/dev/null || true

# Desliga ASLR para o CMD e qualquer processo lançado dentro do container.
exec setarch x86_64 -R "$@"
