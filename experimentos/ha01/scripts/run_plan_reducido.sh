#!/usr/bin/env bash
# PLAN REDUCIDO — la campana tal como se ejecuta, en lugar de los bloques 1 y 2
# con 3 repeticiones (desviacion declarada en el README).
#
# Por que se reduce: la variacion entre corridas medida en el bloque 3 es
# minima (p95 en fase sana 64,8-64,9 ms en seis corridas independientes; p99
# 133-147 ms, a mas de 3x del umbral). Una repeticion no mueve un resultado que
# esta al triple de distancia del umbral; donde SI hace falta repetir es en las
# celdas cercanas a el. Con ese criterio se replica solo B con proveedor lento.
#
# Por que el bloque 2 corre en `lento` y no en `degradado`: en `degradado` el
# interruptor abre en segundos y rescata a B, asi que la curva no discriminaria
# entre brazos. El minimo decisivo mostro que es en `lento` donde B depende del
# acierto (1,28 % de cotizaciones > 475 ms con acierto 96 %).
#
# Orden por prioridad: si la noche no alcanza, lo que queda sin correr es lo
# menos critico. Las corridas ya validas se omiten solas (idempotencia).
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

export BREAKER_POLICY=rate
export TARGET_HIT_RATE=0.96

# 1. Replicas de la unica celda cercana al umbral: B con proveedor lento.
for rep in 2 3; do
  corrida_segura corrida cache_blocking "b1_r${rep}_lento" "lento"
done

# 2. Bloque 1, resto de estados, una repeticion (lento ya esta hecho).
#    Completa HD-01.1 y HD-01.2 en los cinco estados del proveedor.
for st in sano degradado sin_respuesta caido; do
  for arm in direct cache_blocking cache_opportunistic; do
    corrida_segura corrida "${arm}" "b1_r1_${st}" "${st}"
  done
done

# 3. Bloque 2 en `lento`: acierto minimo con el que B cumple (HD-01.4).
#    El 96 % ya esta medido (b1_r1_lento). Se anade 98 % porque el cruce de B
#    parece estar entre 96 y 99. C solo en 90 y 50: ya cumplio con 50 % en el
#    bloque 3.
for hr in 0.99 0.98 0.90 0.50; do
  export TARGET_HIT_RATE="${hr}"
  corrida_segura corrida cache_blocking "b2_r1_hr${hr}" "lento"
done
for hr in 0.90 0.50; do
  export TARGET_HIT_RATE="${hr}"
  corrida_segura corrida cache_opportunistic "b2_r1_hr${hr}" "lento"
done
export TARGET_HIT_RATE=0.96

# 4. Celda de estampida de HD-01.7: C contra C' con fallos concurrentes sobre
#    POCAS claves. Con los pools normales dos fallos simultaneos sobre la misma
#    clave casi no ocurren y C' no tiene nada que coalescer (0 coalescencias en
#    el bloque 3). Aqui todo el trafico va a 20 claves con TTL de 2 s: cada
#    clave vence cada 2 s y recibe ~10 peticiones por segundo. Con el proveedor
#    sin respuesta, C lanza un refresco por peticion (~140 en vuelo sobre un
#    pool de 40) y C' uno por clave (~20).
#    El acierto NO es la variable en esta celda, asi que no se verifica.
guardar=(UNIVERSO_CLIENTES PROFILE_TTL_SECONDS HOT_AGE_SPREAD_S TARGET_HIT_RATE)
declare -A previo
for v in "${guardar[@]}"; do previo[$v]="${!v:-}"; done
export UNIVERSO_CLIENTES=20 PROFILE_TTL_SECONDS=2 HOT_AGE_SPREAD_S=0
export TARGET_HIT_RATE=1.0 VERIFICAR_ACIERTO=0
for arm in cache_opportunistic cache_singleflight; do
  corrida_segura corrida "${arm}" "b3_estampida_ttl2" "sin_respuesta" 200
done
for v in "${guardar[@]}"; do export "$v=${previo[$v]}"; done
unset VERIFICAR_ACIERTO

# 5. Bloque 4: latencia contra tasa de llegada (EC-LAT-02). Al final porque
#    el brazo C ya cumplio a 200 sol/s en el bloque 3.
export ESCALONES="20,50,100,200" ESCALON_S=120
for st in sano degradado; do
  for arm in cache_blocking cache_opportunistic; do
    corrida_segura corrida_escalones "${arm}" "b4_${st}" "${st}"
  done
done

resumen_bloque
