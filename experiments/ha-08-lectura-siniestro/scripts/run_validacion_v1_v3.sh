#!/usr/bin/env bash
# Valida los hallazgos V1/V3/V6 de AUDITORIA_EXTERNA_HA-08.md: repite el
# brazo A con shared_buffers bajo (64MB, sugerido por Guia_Tecnica_HA-08.md
# §14 para el síntoma "p95 sospechosamente bajo") y con el hot set disperso
# (read_estado_hotset_disperso.js — múltiplos de 100 en vez de IDs 1-10000
# consecutivos, que son físicamente contiguos en el heap).
#
# No modifica .env ni docker-compose.yml: pasa PG_SHARED_BUFFERS y
# PG_EFFECTIVE_CACHE_SIZE como override de entorno solo para esta corrida,
# y recrea (--force-recreate) el contenedor de Postgres para que el nuevo
# valor de shared_buffers se aplique (un simple restart no lo hace, porque
# el parámetro se fija en el "command:" del compose al crear el
# contenedor). El volumen pgdata persiste — no se pierde el dataset.
set -euo pipefail

ARM="A"
RUN_ID="v1v3_r1"
export PG_SHARED_BUFFERS=64MB
export PG_EFFECTIVE_CACHE_SIZE=128MB

echo "==> Validación V1/V3/V6 — brazo ${ARM}, shared_buffers=${PG_SHARED_BUFFERS}, hot set disperso"

# 1. Reiniciar estado volátil, recreando Postgres para aplicar shared_buffers
docker compose stop api projector simulator
docker compose exec -T redis redis-cli FLUSHALL
docker compose up -d --force-recreate postgres
docker compose exec -T postgres sh -c 'until pg_isready -U solventa; do sleep 1; done'
echo "==> Confirmando shared_buffers real aplicado:"
docker compose exec -T postgres psql -U solventa -d solventa -c "SHOW shared_buffers;"

# 2. Arrancar con brazo A
READ_STRATEGY="${ARM}" docker compose up -d api projector simulator
sleep 20

# 3. Aserción dura
ARM_ACTIVO=$(curl -s localhost:8000/health | jq -r .arm)
[ "$ARM_ACTIVO" = "$ARM" ] || { echo "ERROR: la API sirve ${ARM_ACTIVO}, se esperaba ${ARM}"; exit 1; }

# 4. Ejecutar la carga con hot set disperso, capturando docker stats en serie
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

docker run --rm --name ha08-k6-validacion --network solventa-ha08_default \
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
  --summary-trend-stats="avg,min,med,max,p(90),p(95),p(99)" \
  /scripts/read_estado_hotset_disperso.js

pkill -P "${STATS_PID}" 2>/dev/null || true
kill "${STATS_PID}" 2>/dev/null || true

# 5. Métricas de proyector y caché
curl -s localhost:8001/metrics | grep ha08_projection_lag \
  > "results/raw/lag_${ARM}_${RUN_ID}.txt"
curl -s localhost:8000/metrics | grep ha08_cache_ \
  > "results/raw/cache_${ARM}_${RUN_ID}.txt"

echo "==> Listo: results/raw/summary_${ARM}_${RUN_ID}.json"
echo "==> IMPORTANTE: Postgres queda con shared_buffers=64MB. Restaurar con:"
echo "    docker compose up -d --force-recreate postgres  (usa .env, vuelve a 256MB)"
