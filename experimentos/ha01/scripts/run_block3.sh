#!/usr/bin/env bash
# BLOQUE 3 — interruptor, recuperacion y estampida.
# Fija: brazo C (y C' para el contraste), proveedor pasa de sano a
#       sin_respuesta y vuelve a sano.
# Varia: politica del interruptor (count / rate) x trafico (alto / bajo),
#        y el contraste C vs C' en DOS niveles de acierto.
# Sub-hipotesis: HD-01.5, HD-01.6, HD-01.7, HD-01.8.
#
# Una sola repeticion por celda: las variables dependientes de este bloque son
# conteos y tiempos, no percentiles, y su varianza se controla observando la
# transicion completa en una corrida larga.
#
# `sin_respuesta` es el estado elegido a proposito: es el unico que retiene
# descriptores del pool y por tanto el unico donde se puede ver si el
# aislamiento de recursos esta bien dimensionado.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

# --- HD-01.5 y HD-01.6: politica del interruptor x trafico ------------
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

# --- HD-01.7: contraste C vs C' sobre la estampida --------------------
# En DOS niveles de acierto, y la razon es aritmetica.
#
# Con acierto 96 % a 200 sol/s hay 8 fallos/s; a 700 ms de timeout duro eso
# son 5,6 invocaciones concurrentes sobre un pool de 40: el 14 %. Y como el
# interruptor abre a los ~6 s, la ventana en que el pool podria llenarse dura
# esos 6 s. Medido: inflight_max = 8. El pool NUNCA se estresa, asi que a ese
# nivel HD-01.7 no se puede ni confirmar ni refutar.
#
# Para saturar 40 conexiones hacen falta 40/0,7 = 57 invocaciones por segundo,
# es decir un 28,6 % de fallos a 200 sol/s. Con acierto 50 % son 100 fallos/s
# -> 70 concurrentes, y ahi el aislamiento de recursos si se pone a prueba.
#
# Se reportan AMBOS niveles: que a 96 % el pool no se estrese es un resultado
# en si mismo -el interruptor actua antes que el bulkhead- y es lo que da
# sentido al de 50 %.
export BREAKER_POLICY=rate

for hr in 0.96 0.50; do
  export TARGET_HIT_RATE="${hr}"
  for arm in cache_opportunistic cache_singleflight; do
    corrida "${arm}" "b3_estampida_hr${hr}" "sin_respuesta" 200
  done
done
