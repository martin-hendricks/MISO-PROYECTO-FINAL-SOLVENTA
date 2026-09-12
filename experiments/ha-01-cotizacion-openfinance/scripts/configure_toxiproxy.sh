#!/usr/bin/env bash
# Configura el proxy de Toxiproxy y aplica uno de los 6 estados del
# proveedor definidos en el Anexo A del diseño del experimento HA-01:
# healthy | slow | degraded | unresponsive | down | recovery
set -euo pipefail

TOXIPROXY_URL="${TOXIPROXY_URL:-http://localhost:8474}"
STATE="${1:?Uso: configure_toxiproxy.sh <healthy|slow|degraded|unresponsive|down|recovery>}"

# Crea el proxy si no existe (idempotente).
curl -s -X POST "${TOXIPROXY_URL}/proxies" \
  -H "Content-Type: application/json" \
  -d '{"name":"openfinance","listen":"0.0.0.0:9001","upstream":"provider_double:9000"}' \
  >/dev/null 2>&1 || true

# Limpia toxics previos.
curl -s -X GET "${TOXIPROXY_URL}/proxies/openfinance/toxics" \
  | jq -r '.[].name' 2>/dev/null \
  | while read -r toxic; do
      [ -n "$toxic" ] && curl -s -X DELETE "${TOXIPROXY_URL}/proxies/openfinance/toxics/${toxic}" >/dev/null
    done

case "$STATE" in
  healthy|recovery)
    echo "==> Proveedor sano (sin alteración de conexión)"
    ;;
  slow)
    echo "==> Proveedor lento (latencia de aplicación configurada en el doble; sin alteración de red)"
    ;;
  degraded)
    echo "==> Proveedor degradado (+150 ms de latencia de red inyectada)"
    curl -s -X POST "${TOXIPROXY_URL}/proxies/openfinance/toxics" \
      -H "Content-Type: application/json" \
      -d '{"name":"degraded_latency","type":"latency","attributes":{"latency":150,"jitter":30}}' >/dev/null
    ;;
  unresponsive)
    echo "==> Proveedor sin respuesta (acepta conexión, nunca envía datos)"
    curl -s -X POST "${TOXIPROXY_URL}/proxies/openfinance/toxics" \
      -H "Content-Type: application/json" \
      -d '{"name":"no_response","type":"timeout","attributes":{"timeout":0}}' >/dev/null
    ;;
  down)
    echo "==> Proveedor caído (conexión rechazada)"
    curl -s -X POST "${TOXIPROXY_URL}/proxies/openfinance/toxics" \
      -H "Content-Type: application/json" \
      -d '{"name":"reset","type":"reset_peer","attributes":{"timeout":0}}' >/dev/null
    ;;
  *)
    echo "Estado desconocido: ${STATE}" >&2
    exit 1
    ;;
esac

echo "==> Estado del proveedor: ${STATE}"
