#!/usr/bin/env bash
# BLOQUE 4 — escalones de tasa de llegada.
#
# Cierra la variable independiente "tasa de llegada", que el Anexo A declara
# con niveles 20/50/100/200 pero que ningun otro bloque varia: el 1 y el 2 la
# fijan en 100 y el 3 usa 200 y 10. Sin este bloque, dos de los cinco niveles
# no se ejecutan nunca y la variable queda declarada sin medirse.
#
# Es ademas lo que sostiene EC-LAT-02 (horario pico, p99 <= 500 ms extremo a
# extremo): ese escenario habla de "alta concurrencia", y hasta aqui todo se
# media a un solo nivel de carga.
#
# Fija: acierto 96 %, interruptor por tasa.
# Varia: tasa de llegada (4 escalones) x brazo (B, C) x estado (sano,
#        degradado) = 4 corridas de ~10 min.
#
# El estado del proveedor NO se conmuta dentro de la corrida: aqui la variable
# que se mueve es la carga, y mover dos a la vez haria imposible atribuir el
# efecto a ninguna.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

export TARGET_HIT_RATE="${TARGET_HIT_RATE:-0.96}"
export BREAKER_POLICY="${BREAKER_POLICY:-rate}"
export ESCALONES="${ESCALONES:-20,50,100,200}"
export ESCALON_S="${ESCALON_S:-120}"

for st in sano degradado; do
  for arm in cache_blocking cache_opportunistic; do
    corrida_segura corrida_escalones "${arm}" "b4_${st}" "${st}"
  done
done

resumen_bloque
