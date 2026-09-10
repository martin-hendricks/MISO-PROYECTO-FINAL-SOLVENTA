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

# 3. Aserción dura: la API debe estar sirviendo el brazo que se va a medir.
# verify_parity.sh (paso previo, fuera de esta corrida) recrea el contenedor
# api con A/B/C en un bucle para comparar payloads; si esta corrida se lanzó
# sin volver a levantar la API con READ_STRATEGY=${ARM} después de esa
# verificación, la API quedaría sirviendo el último brazo del bucle en vez
# del brazo de esta corrida. Este chequeo corta la ejecución antes de medir
# el brazo equivocado.
ARM_ACTIVO=$(curl -s localhost:8000/health | jq -r .arm)
[ "$ARM_ACTIVO" = "$ARM" ] || { echo "ERROR: la API sirve ${ARM_ACTIVO}, se esperaba ${ARM}"; exit 1; }

# 4. Ejecutar la carga, capturando docker stats en serie durante toda la
# corrida (antes solo se tomaba un snapshot al final — no permitía ver la
# evolución de CPU/memoria por contenedor a lo largo de los escalones de
# carga, solo el punto final. cAdvisor se evaluó como alternativa para tener
# esto vía Prometheus, pero no resuelve nombres de contenedor en Docker
# Desktop/macOS — limitación de la plataforma, no de la config; se descartó).
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

READ_STRATEGY="${ARM}" RUN_ID="${RUN_ID}" \
  docker compose --profile load run --rm k6

# kill "$STATS_PID" solo mata el subshell del while; el "docker stats" hijo
# que esté a mitad de ejecución en ese instante queda huérfano (verificado:
# deja procesos "docker stats" corriendo indefinidamente en macOS/Docker
# Desktop). pkill -P mata también a los hijos directos del PID.
pkill -P "${STATS_PID}" 2>/dev/null || true
kill "${STATS_PID}" 2>/dev/null || true

# 5. Recolectar métricas del proyector
curl -s localhost:8001/metrics | grep ha08_projection_lag \
  > "results/raw/lag_${ARM}_${RUN_ID}.txt"

echo "==> Listo: results/raw/summary_${ARM}_${RUN_ID}.json"
