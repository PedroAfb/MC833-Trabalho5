#!/bin/bash
set -e

# Mesma lógica das vítimas: aponta default para o roteador interno (.254 da subnet).
IFACE_IP=$(ip -4 -o addr show eth0 | awk '{print $4}' | cut -d/ -f1)
SUBNET_PREFIX=$(echo "$IFACE_IP" | cut -d. -f1-3)
ROUTER_IP="${SUBNET_PREFIX}.254"

ip route del default 2>/dev/null || true
ip route add default via "$ROUTER_IP" 2>/dev/null || true

exec "$@"
