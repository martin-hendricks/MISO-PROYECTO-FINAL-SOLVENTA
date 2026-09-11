#!/usr/bin/env bash
# CORRIDAS ADICIONALES — cierran las observaciones de la evaluacion del avance
# y repiten lo que quedo invalidado. Se lanzan todas juntas (~2 h).
#
# Ordenadas por lo que puede mover una conclusion del informe.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

export BREAKER_POLICY=rate
export TARGET_HIT_RATE=0.96

# 1. HD-01.5 y HD-01.6 EN EL BRAZO B, que es donde el interruptor decide la
#    latencia. En C no: alli ninguna peticion espera mas que el presupuesto,
#    asi que la politica no movia el p99 (178 contra 65 ms, ambos cumplen).
#    En B, cada peticion antes de la apertura espera hasta 700 ms. Estimacion
#    con los tiempos de apertura medidos: con trafico bajo y politica por
#    conteo, B deberia quedar alrededor del 1 % sobre 475 ms, justo el umbral.
for pol in rate count; do
  export BREAKER_POLICY="${pol}"
  corrida_segura corrida cache_blocking "b3b_pol_${pol}_alto" "sin_respuesta" 200
  corrida_segura corrida cache_blocking "b3b_pol_${pol}_bajo" "sin_respuesta" 10
done
export BREAKER_POLICY=rate

# 2. ESTADO INTERMITENTE: el proveedor falla una fraccion de las veces (30 %).
#    Es la incertidumbre (c) del diseno y el unico caso en que las dos
#    politicas divergen de verdad: ni diez fallos seguidos ni una tasa del
#    50 % en la ventana se alcanzan, asi que el interruptor NO abre y las
#    llamadas colgadas se acumulan en el pool. Con `degradado` esto no se veia,
#    porque alli TODAS las llamadas superan el timeout duro y el interruptor
#    abre en segundos.
export FALLO_FRACCION=0.3
for pol in rate count; do
  export BREAKER_POLICY="${pol}"
  for arm in cache_blocking cache_opportunistic; do
    corrida_segura corrida "${arm}" "b5_intermitente_${pol}" "intermitente" 200
  done
done
unset FALLO_FRACCION
export BREAKER_POLICY=rate

# 3. BLOQUE 4 REPETIDO. El escalon de 200 sol/s quedo invalidado: la edad del
#    pool caliente (0-450 s) mas la duracion de la corrida (560 s) supera el
#    TTL de 900 s, asi que las entradas vencian a mitad de corrida y el acierto
#    caia a 0,85-0,87. Ahora la dispersion se acota sola a la duracion y el
#    acierto se verifica tambien en los escalones.
export ESCALONES="20,50,100,200" ESCALON_S=120
for st in sano degradado; do
  for arm in cache_blocking cache_opportunistic; do
    corrida_segura corrida_escalones "${arm}" "b4b_${st}" "${st}"
  done
done

# 4. ESTAMPIDA REPETIDA con PoolTimeout separado. En la corrida anterior, las
#    llamadas fallidas de C mezclaban timeouts del proveedor con esperas por
#    falta de conexion en el pool (90 en vuelo sobre 40).
guardar=(UNIVERSO_CLIENTES PROFILE_TTL_SECONDS HOT_AGE_SPREAD_S TARGET_HIT_RATE)
declare -A previo
for v in "${guardar[@]}"; do previo[$v]="${!v:-}"; done
export UNIVERSO_CLIENTES=20 PROFILE_TTL_SECONDS=2 HOT_AGE_SPREAD_S=0
export TARGET_HIT_RATE=1.0 VERIFICAR_ACIERTO=0
for arm in cache_opportunistic cache_singleflight; do
  corrida_segura corrida "${arm}" "b3_estampida_ttl2b" "sin_respuesta" 200
done
for v in "${guardar[@]}"; do export "$v=${previo[$v]}"; done
unset VERIFICAR_ACIERTO

# 5. C' AL 50 % REPETIDA con el detector de interferencia activo. La corrida
#    original quedo marcada para revisar: su respaldo llego a 525 ms con el
#    presupuesto en 120, lo que solo se explica si el bucle de eventos estuvo
#    bloqueado, y es anterior a la sonda.
export TARGET_HIT_RATE=0.50
corrida_segura corrida cache_singleflight "b3_estampida_hr0.50b" "sin_respuesta" 200
export TARGET_HIT_RATE=0.96

resumen_bloque
