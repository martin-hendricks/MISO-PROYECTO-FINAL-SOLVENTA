#!/usr/bin/env bash
# Enumera, en orden, las corridas que componen el experimento TAL COMO SE
# EJECUTA y las escribe en results/plan.txt. Lo consume estado.py.
#
# La lista sale de los propios scripts de bloque (modo SOLO_LISTAR de
# corrida_segura), no de una copia a mano: si un bloque cambia, el estado del
# experimento lo refleja solo.
set -euo pipefail
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${RAIZ}"

{
  for s in run_block3.sh run_decisivo.sh run_plan_reducido.sh; do
    SOLO_LISTAR=1 "./scripts/${s}" 2>/dev/null | grep '^PLAN|' || true
  done
} > results/plan.txt

echo "plan del experimento: $(wc -l < results/plan.txt | tr -d ' ') corridas -> results/plan.txt"
