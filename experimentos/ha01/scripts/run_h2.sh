#!/usr/bin/env bash
# H-2 — ESTADO INTERMITENTE CON FALLO POR PETICION (~35 min).
#
# Repite la celda `b5_intermitente` con el doble corregido. Hasta el commit
# «fix: fallo del doble por peticion», la decision de fallo se derivaba de la
# misma uniforme que la latencia -hash de (semilla, customer_id)-, de modo que
# el 30 % de los clientes fallaba SIEMPRE y el 70 % restante NUNCA. El estado
# no modelaba un proveedor que falla a veces sino un subconjunto fijo de
# clientes rotos, cuya clave no se repuebla jamas.
#
# Importa porque esta celda sostiene el hallazgo mas fuerte del experimento:
# con fallos intermitentes el interruptor no abre en NINGUN brazo, asi que la
# diferencia entre B y C es atribuible solo al desacople, sin explicacion
# alternativa. Ese razonamiento depende del ENTRELAZADO de fallos y aciertos,
# y el entrelazado difiere entre los dos modelos de fallo. Con el modelo
# viejo el resultado probablemente se sostenia, pero como coincidencia, no
# como control.
#
# Etiqueta `b5b` y no `b5`: las cuatro corridas originales se conservan
# intactas, para poder contrastar el mismo estado bajo los dos modelos de
# fallo. Si el resultado se mantiene, el hallazgo queda blindado; si cambia,
# hay que reescribirlo.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_corrida.sh"

export BREAKER_POLICY=rate
export TARGET_HIT_RATE=0.96

export FALLO_FRACCION=0.3
for pol in rate count; do
  export BREAKER_POLICY="${pol}"
  for arm in cache_blocking cache_opportunistic; do
    corrida_segura corrida "${arm}" "b5b_intermitente_${pol}" "intermitente" 200
  done
done
unset FALLO_FRACCION
export BREAKER_POLICY=rate

resumen_bloque
