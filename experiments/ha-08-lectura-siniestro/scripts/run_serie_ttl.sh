#!/usr/bin/env bash
# Repite las variantes de sensibilidad TTL (punto de sensibilidad 2 del
# diseño) con n=3 cada una en vez de n=1 (hallazgo §3.7 de
# EVALUACION_EJECUCION_HA-08.md), usando el script ya corregido con la
# aserción de /health. Solo el brazo C usa caché, así que solo C es
# relevante para esta sensibilidad.
set -euo pipefail

CORRIDAS=(
  "ttl0_r1 0" "ttl0_r2 0" "ttl0_r3 0"
  "ttl300_r1 300" "ttl300_r2 300" "ttl300_r3 300"
)

for par in "${CORRIDAS[@]}"; do
  read -r RUN_ID TTL <<< "$par"
  echo ""
  echo "================================================================"
  echo "  Corrida ${RUN_ID} — brazo C, TTL=${TTL}s  ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  echo "================================================================"
  ./scripts/run_experiment.sh C "${RUN_ID}" "${TTL}"
done

echo ""
echo "==> Serie TTL (6 corridas) finalizada sin errores."
