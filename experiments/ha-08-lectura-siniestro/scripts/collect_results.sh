#!/usr/bin/env bash
# Consolida los summary_<ARM>_<RUN_ID>.json producidos por k6 en un único CSV,
# con las columnas de la plantilla de registro de resultados (Anexo C del
# diseño del experimento: brazo, corrida, p50/p95/p99, error, hit-rate, lag).
set -euo pipefail

RESULTS_DIR="results/raw"
echo "brazo,corrida,rps_objetivo,p50_ms,p95_ms,p99_ms,error_rate,hit_rate,lag_p95_s_aprox"

for summary in "${RESULTS_DIR}"/summary_*.json; do
  [ -e "$summary" ] || continue
  filename=$(basename "$summary" .json)
  arm=$(echo "$filename" | sed -E 's/^summary_([A-Z_]+)_([a-zA-Z0-9]+)$/\1/')
  run_id=$(echo "$filename" | sed -E 's/^summary_([A-Z_]+)_([a-zA-Z0-9]+)$/\2/')

  # La métrica de k6 vive directo en .metrics.ha08_estado_duration, sin el
  # nivel intermedio ".values" que asumía la primera versión de este script.
  # Esta versión de k6 expone "med" (mediana), no "p(50)".
  p50=$(jq -r '.metrics.ha08_estado_duration.med // "n/a"' "$summary")
  p95=$(jq -r '.metrics.ha08_estado_duration["p(95)"] // "n/a"' "$summary")
  p99=$(jq -r '.metrics.ha08_estado_duration["p(99)"] // "n/a"' "$summary")
  # http_req_failed es un rate metric: .value es la tasa (0-1), no
  # passes/fails (esos cuentan "check" pass/fail, no la tasa de error).
  error_rate=$(jq -r '.metrics.http_req_failed.value // "n/a"' "$summary")

  # ha08_projection_lag_seconds es un Histogram de Prometheus expuesto con
  # buckets acumulativos (_bucket{le=...}), no un Summary con quantiles.
  # No hay percentil exacto sin los datos crudos; se aproxima por el primer
  # bucket que acumula >= 95% del total de observaciones (_count).
  lag_file="${RESULTS_DIR}/lag_${arm}_${run_id}.txt"
  lag_p95="n/a"
  if [ -f "$lag_file" ]; then
    total=$(grep -oE '^ha08_projection_lag_seconds_count [0-9.]+' "$lag_file" | awk '{print $2}')
    if [ -n "${total:-}" ] && [ "$total" != "0" ]; then
      threshold=$(python3 -c "print(${total} * 0.95)")
      lag_p95=$(grep -E '^ha08_projection_lag_seconds_bucket' "$lag_file" | \
        sed -E 's/.*le="([^"]+)".* ([0-9.]+)$/\1 \2/' | \
        awk -v thr="$threshold" '{ if ($2+0 >= thr+0) { print $1; exit } }')
      [ -z "$lag_p95" ] && lag_p95="n/a"
    fi
  fi

  echo "${arm},${run_id},n/a,${p50},${p95},${p99},${error_rate},n/a,${lag_p95}"
done
