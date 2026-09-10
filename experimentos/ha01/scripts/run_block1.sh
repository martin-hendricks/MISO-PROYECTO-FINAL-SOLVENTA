#!/usr/bin/env bash
# BLOQUE 1 — estrategia contra estado del proveedor.
# Fija: acierto 96 %, 100 sol/s, interruptor por tasa.
# Varia: brazo (A, B, C) x estado (5) x 3 repeticiones = 45 corridas.
# Sub-hipotesis: HD-01.1, HD-01.2, HD-01.3.
#
# El orden de los brazos se ROTA entre repeticiones (contrabalanceo) para que
# un efecto de calentamiento del entorno no se confunda con un efecto del
# brazo. El bucle lo hace solo; la permutacion queda registrada en el log.
#
#   Uso: run_block1.sh [repeticiones]   (por defecto 3)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

export TARGET_HIT_RATE="${TARGET_HIT_RATE:-0.96}"
export BREAKER_POLICY="${BREAKER_POLICY:-rate}"
REPS="${1:-3}"
ESTADOS=(sano lento degradado sin_respuesta caido)
BRAZOS=(direct cache_blocking cache_opportunistic)

for rep in $(seq 1 "${REPS}"); do
  # Rotacion circular de los brazos segun la repeticion.
  n=${#BRAZOS[@]}
  orden=()
  for i in $(seq 0 $((n - 1))); do
    orden+=("${BRAZOS[$(( (i + rep - 1) % n ))]}")
  done
  echo "=== repeticion r${rep} — orden de brazos: ${orden[*]} ==="

  for arm in "${orden[@]}"; do
    for st in "${ESTADOS[@]}"; do
      corrida_segura corrida "${arm}" "b1_r${rep}_${st}" "${st}"
    done
  done
done

resumen_bloque
