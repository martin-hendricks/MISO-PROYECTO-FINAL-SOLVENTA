#!/usr/bin/env bash
# BLOQUE 2 — sensibilidad a la tasa de acierto.
# Fija: brazos B y C, proveedor degradado, 100 sol/s.
# Varia: acierto 99 / 96 / 90 / 50 % x 3 repeticiones = 24 corridas.
# Sub-hipotesis: HD-01.4 (tasa de acierto minima que sostiene el ASR).
#
#   Uso: run_block2.sh [repeticiones]
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

export BREAKER_POLICY="${BREAKER_POLICY:-rate}"
REPS="${1:-3}"

for rep in $(seq 1 "${REPS}"); do
  for hr in 0.99 0.96 0.90 0.50; do
    for arm in cache_blocking cache_opportunistic; do
      export TARGET_HIT_RATE="${hr}"
      corrida "${arm}" "b2_r${rep}_hr${hr}" "degradado"
    done
  done
done
