#!/usr/bin/env bash
# Consolida los summary_<ARM>_<RUN_ID>.json producidos por k6 en un único CSV,
# con las columnas de la plantilla de registro de resultados (Anexo C del
# diseño del experimento: brazo, corrida, p50/p95/p99, error, hit-rate, lag).
set -euo pipefail

RESULTS_DIR="results/raw"
echo "brazo,corrida,rps_objetivo,p50_ms,p95_ms,p99_ms,error_rate,hit_rate,lag_p95_s"

for summary in "${RESULTS_DIR}"/summary_*.json; do
  [ -e "$summary" ] || continue
  filename=$(basename "$summary" .json)
  arm=$(echo "$filename" | sed -E 's/^summary_([A-Z_]+)_([a-zA-Z0-9]+)$/\1/')
  run_id=$(echo "$filename" | sed -E 's/^summary_([A-Z_]+)_([a-zA-Z0-9]+)$/\2/')

  p50=$(jq -r '.metrics.ha08_estado_duration.values["p(50)"] // "n/a"' "$summary")
  p95=$(jq -r '.metrics.ha08_estado_duration.values["p(95)"] // "n/a"' "$summary")
  p99=$(jq -r '.metrics.ha08_estado_duration.values["p(99)"] // "n/a"' "$summary")
  error_rate=$(jq -r '.metrics.http_req_failed.values.rate // "n/a"' "$summary")

  lag_file="${RESULTS_DIR}/lag_${arm}_${run_id}.txt"
  lag_p95="n/a"
  if [ -f "$lag_file" ]; then
    lag_p95=$(grep -oE '^ha08_projection_lag_seconds.*quantile="0.95".* [0-9.]+$' "$lag_file" \
      | awk '{print $NF}' || echo "n/a")
    [ -z "$lag_p95" ] && lag_p95="n/a"
  fi

  echo "${arm},${run_id},n/a,${p50},${p95},${p99},${error_rate},n/a,${lag_p95}"
done
