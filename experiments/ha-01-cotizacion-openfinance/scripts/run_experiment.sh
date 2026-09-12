#!/usr/bin/env bash
# Ejecuta una corrida completa para un brazo: arranca con la estrategia
# indicada, recorre los estados del proveedor definidos en el Anexo A
# (healthy -> degraded -> unresponsive -> down -> recovery) y corre k6
# contra el escalón de operación regular en cada estado.
set -euo pipefail

ARM="${1:?Uso: run_experiment.sh <A|B|C|C_PRIME> <run_id>}"
RUN_ID="${2:?Falta run_id}"

echo "==> Corrida ${RUN_ID}, brazo ${ARM}"

docker compose stop api
docker compose exec -T redis redis-cli FLUSHALL

READ_STRATEGY="${ARM}" docker compose up -d api
sleep 10   # estabilización del pool de conexiones

for STATE in healthy degraded unresponsive down recovery; do
  ./scripts/configure_toxiproxy.sh "${STATE}"
  sleep 5   # estabilización del interruptor de circuito tras el cambio

  READ_STRATEGY="${ARM}" RUN_ID="${RUN_ID}_${STATE}" \
    docker compose --profile load run --rm k6

  curl -s "http://localhost:8100/metrics" \
    > "results/raw/metrics_${ARM}_${RUN_ID}_${STATE}.txt"
done

echo "==> Listo: results/raw/summary_${ARM}_${RUN_ID}_<estado>.json"
