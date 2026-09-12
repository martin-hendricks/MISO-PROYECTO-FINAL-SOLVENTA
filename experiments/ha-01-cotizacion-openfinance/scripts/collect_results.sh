#!/usr/bin/env bash
# Consolida los summary_<ARM>_<RUN_ID>_<estado>.json de k6 en un CSV,
# siguiendo el formato de la plantilla de registro de resultados
# (Anexo C del diseño del experimento HA-01).
set -euo pipefail

RESULTS_DIR="results/raw"
echo "brazo,corrida,estado,p50_ms,p95_ms,p99_ms,error_rate"

for summary in "${RESULTS_DIR}"/summary_*.json; do
  [ -e "$summary" ] || continue
  filename=$(basename "$summary" .json)
  # summary_<ARM>_<RUNID>_<ESTADO>
  arm=$(echo "$filename" | cut -d'_' -f2)
  run_estado=$(echo "$filename" | cut -d'_' -f3-)
  run_id=$(echo "$run_estado" | rev | cut -d'_' -f2- | rev)
  estado=$(echo "$run_estado" | rev | cut -d'_' -f1 | rev)

  p50=$(jq -r '.metrics.ha01_cotizacion_duration.values["p(50)"] // "n/a"' "$summary")
  p95=$(jq -r '.metrics.ha01_cotizacion_duration.values["p(95)"] // "n/a"' "$summary")
  p99=$(jq -r '.metrics.ha01_cotizacion_duration.values["p(99)"] // "n/a"' "$summary")
  error_rate=$(jq -r '.metrics.http_req_failed.values.rate // "n/a"' "$summary")

  echo "${arm},${run_id},${estado},${p50},${p95},${p99},${error_rate}"
done
