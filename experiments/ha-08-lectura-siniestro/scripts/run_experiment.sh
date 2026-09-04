#!/usr/bin/env bash
set -euo pipefail

ARM="${1:?Uso: run_experiment.sh <A|B|C|C_PRIME> <run_id>}"
RUN_ID="${2:?Falta run_id}"

echo "==> Corrida ${RUN_ID}, brazo ${ARM}"

# 1. Reiniciar estado volátil: caché vacío, pools frescos, shared_buffers limpio
docker compose stop api projector simulator
docker compose exec -T redis redis-cli FLUSHALL
docker compose restart postgres
docker compose exec -T postgres sh -c 'until pg_isready -U solventa; do sleep 1; done'

# 2. Arrancar con la estrategia del brazo
READ_STRATEGY="${ARM}" docker compose up -d api projector simulator
sleep 20   # estabilización de pools y consumer group

# 3. Verificar paridad del payload entre brazos
./scripts/verify_parity.sh

# 4. Ejecutar la carga
READ_STRATEGY="${ARM}" RUN_ID="${RUN_ID}" \
  docker compose --profile load run --rm k6

# 5. Recolectar métricas de recursos y del proyector
docker stats --no-stream --format \
  "{{.Name}},{{.CPUPerc}},{{.MemUsage}}" > "results/raw/stats_${ARM}_${RUN_ID}.csv"
curl -s localhost:8001/metrics | grep ha08_projection_lag \
  > "results/raw/lag_${ARM}_${RUN_ID}.txt"

echo "==> Listo: results/raw/summary_${ARM}_${RUN_ID}.json"
