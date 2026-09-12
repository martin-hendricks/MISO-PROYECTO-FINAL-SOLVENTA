#!/usr/bin/env bash
# Encadena las 9 corridas contrabalanceadas del protocolo formal (Latin
# square: R1=A->B->C, R2=B->C->A, R3=C->A->B) usando run_experiment.sh, ya
# corregido con la aserción de /health (ver INFORME.md §0). Se detiene
# inmediatamente si cualquier corrida falla la aserción o k6, en vez de
# continuar produciendo datos inválidos como pasó el 2026-09-08.
set -euo pipefail

CORRIDAS=(
  "A r1" "B r1" "C r1"
  "B r2" "C r2" "A r2"
  "C r3" "A r3" "B r3"
)

for par in "${CORRIDAS[@]}"; do
  read -r ARM RUN_ID <<< "$par"
  echo ""
  echo "================================================================"
  echo "  Corrida ${RUN_ID} — brazo ${ARM}  ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  echo "================================================================"
  ./scripts/run_experiment.sh "${ARM}" "${RUN_ID}"
done

echo ""
echo "==> Serie completa (9 corridas) finalizada sin errores."
