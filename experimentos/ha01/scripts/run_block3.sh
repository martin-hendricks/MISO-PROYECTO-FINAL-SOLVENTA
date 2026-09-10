#!/usr/bin/env bash
# BLOQUE 3 — interruptor, recuperacion y estampida.
# Fija: brazo C (y C' para el contraste), proveedor pasa de sano a
#       sin_respuesta y vuelve a sano.
# Varia: politica del interruptor (count / rate) x trafico (alto / bajo).
# Sub-hipotesis: HD-01.5, HD-01.6, HD-01.7, HD-01.8.
#
# Una sola repeticion por celda: las variables dependientes de este bloque
# son conteos y tiempos, no percentiles, y su varianza se controla observando
# la transicion completa en una corrida larga.
#
# `sin_respuesta` es el estado elegido a proposito: es el unico que retiene
# descriptores del pool y por tanto el unico donde se puede ver si el
# aislamiento de recursos esta bien dimensionado (HD-01.7).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

export TARGET_HIT_RATE="${TARGET_HIT_RATE:-0.96}"

for pol in rate count; do
  for traf in alto bajo; do
    case "${traf}" in
      alto) RATE=200 ;;
      bajo) RATE=10  ;;
    esac
    export BREAKER_POLICY="${pol}"
    corrida cache_opportunistic "b3_${pol}_${traf}" "sin_respuesta" "${RATE}"
  done
done

# Contraste C vs C' sobre la estampida, con trafico alto y politica por tasa.
export BREAKER_POLICY=rate
corrida cache_singleflight "b3_singleflight_alto" "sin_respuesta" 200
