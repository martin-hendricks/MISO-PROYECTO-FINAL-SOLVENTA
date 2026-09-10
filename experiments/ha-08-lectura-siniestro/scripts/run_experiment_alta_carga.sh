#!/usr/bin/env bash
# Variante de run_experiment.sh para la iteración de alta carga (150/300/600
# req/s, ver INFORME.md §2.4/§5): mismo procedimiento de reinicio de estado
# volátil y verificación de paridad, pero corre read_estado_alta_carga.js en
# vez del protocolo formal (read_estado.js) via `docker run` directo, para no
# alterar el servicio "k6" del compose que usa el protocolo formal.
set -euo pipefail

ARM="${1:?Uso: run_experiment_alta_carga.sh <A|B|C|C_PRIME> <run_id>}"
RUN_ID="${2:?Falta run_id}"
NETWORK="solventa-ha08_default"

echo "==> [Alta carga] Corrida ${RUN_ID}, brazo ${ARM}"

# 1. Reiniciar estado volátil: caché vacío, pools frescos, shared_buffers limpio
docker compose stop api projector simulator
docker compose exec -T redis redis-cli FLUSHALL
docker compose restart postgres
docker compose exec -T postgres sh -c 'until pg_isready -U solventa; do sleep 1; done'

# 2. Arrancar con la estrategia del brazo
READ_STRATEGY="${ARM}" docker compose up -d api projector simulator
sleep 20   # estabilización de pools y consumer group

# 3. Aserción dura: la API debe estar sirviendo el brazo que se va a medir
# (ver comentario extenso en run_experiment.sh — mismo riesgo aplica aquí).
ARM_ACTIVO=$(curl -s localhost:8000/health | jq -r .arm)
[ "$ARM_ACTIVO" = "$ARM" ] || { echo "ERROR: la API sirve ${ARM_ACTIVO}, se esperaba ${ARM}"; exit 1; }

# 4. Ejecutar la carga de alta intensidad, capturando docker stats en serie
# durante toda la corrida (ver comentario extenso en run_experiment.sh).
STATS_FILE="results/raw/stats_${ARM}_${RUN_ID}.csv"
echo "timestamp,name,cpu_perc,mem_usage" > "${STATS_FILE}"
(
  while true; do
    ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" \
      | grep "^ha08-" | sed "s/^/${ts},/" >> "${STATS_FILE}"
    sleep 10
  done
) &
STATS_PID=$!

docker run --rm --network "${NETWORK}" \
  -e K6_PROMETHEUS_RW_SERVER_URL=http://prometheus:9090/api/v1/write \
  -e K6_PROMETHEUS_RW_TREND_STATS="p(50),p(95),p(99),avg,max" \
  -e BASE_URL=http://api:8000 \
  -e ARM="${ARM}" \
  -e RUN_ID="${RUN_ID}" \
  -v "$(pwd)/load/k6:/scripts:ro" \
  -v "$(pwd)/results/raw:/results" \
  grafana/k6:0.53.0 run \
  --out experimental-prometheus-rw \
  --summary-export="/results/summary_${ARM}_${RUN_ID}.json" \
  /scripts/read_estado_alta_carga.js

# pkill -P mata también al "docker stats" hijo que quedaría huérfano con
# solo kill "$STATS_PID" (verificado en run_experiment.sh).
pkill -P "${STATS_PID}" 2>/dev/null || true
kill "${STATS_PID}" 2>/dev/null || true

# 5. Recolectar métricas del proyector
curl -s localhost:8001/metrics | grep ha08_projection_lag \
  > "results/raw/lag_${ARM}_${RUN_ID}.txt"

echo "==> Listo: results/raw/summary_${ARM}_${RUN_ID}.json"
