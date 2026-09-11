#!/usr/bin/env bash
# MINIMO DECISIVO — los tres brazos con el proveedor LENTO.
#
# `lento` es el estado que deberia separar la cache simple (B) del diseno
# propuesto (C). En `degradado`, `sin_respuesta` y `caido` el interruptor abre
# en segundos y a partir de ahi B tambien falla rapido: en el piloto B y C
# dieron el mismo p99 agregado (64,9 ms) con el proveedor degradado. En `lento`
# el proveedor responde dentro del timeout duro, el interruptor NUNCA abre y B
# paga ~500 ms en cada fallo de cache, mientras C queda acotado por el
# presupuesto. Con acierto 96 % el p95 cae siempre en los aciertos, asi que el
# percentil que discrimina es el p99.
#
# Mismos parametros fijos que el bloque 1 (acierto 96 %, 100 sol/s,
# interruptor por tasa) y mismos nombres que sus celdas `lento` de la primera
# repeticion: las corridas son reutilizables como datos del bloque 1.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

export TARGET_HIT_RATE="${TARGET_HIT_RATE:-0.96}"
export BREAKER_POLICY="${BREAKER_POLICY:-rate}"

for arm in direct cache_blocking cache_opportunistic; do
  corrida_segura corrida "${arm}" "b1_r1_lento" "lento"
done

resumen_bloque
