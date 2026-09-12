#!/usr/bin/env bash
set -euo pipefail

ARM="${1:?Uso: run_experiment.sh <A|B|C|C_PRIME> <run_id> [ttl_segundos]}"
RUN_ID="${2:?Falta run_id}"
# TTL opcional para las variantes de sensibilidad (punto de sensibilidad 2 del
# diseño). Si no se pasa, usa el valor de .env (30s, el del protocolo
# formal) — así las 9 corridas contrabalanceadas ya ejecutadas no se ven
# afectadas por este cambio.
TTL="${3:-${CACHE_TTL_SECONDS:-30}}"

echo "==> Corrida ${RUN_ID}, brazo ${ARM}, TTL=${TTL}s"

# 1. Reiniciar estado volátil: caché vacío, pools frescos, shared_buffers limpio
docker compose stop api projector simulator
docker compose exec -T redis redis-cli FLUSHALL
docker compose restart postgres
docker compose exec -T postgres sh -c 'until pg_isready -U solventa; do sleep 1; done'

# 2. Arrancar con la estrategia del brazo y el TTL de esta corrida
READ_STRATEGY="${ARM}" CACHE_TTL_SECONDS="${TTL}" docker compose up -d api projector simulator
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

# 5. Recolectar métricas del proyector y de caché
# Los contadores ha08_cache_hits_total/misses_total viven en el proceso de
# la API y se reinician cada vez que el contenedor se recrea (siguiente
# corrida = siguiente brazo). Si no se capturan aquí, al mirar el hit-rate
# más tarde ya se perdió — ver EVALUACION_EJECUCION_HA-08.md §3.5.
curl -s localhost:8001/metrics | grep ha08_projection_lag \
  > "results/raw/lag_${ARM}_${RUN_ID}.txt"
curl -s localhost:8000/metrics | grep ha08_cache_ \
  > "results/raw/cache_${ARM}_${RUN_ID}.txt"

echo "==> Listo: results/raw/summary_${ARM}_${RUN_ID}.json"
