#!/usr/bin/env bash
# Conmuta el estado del proveedor EN CALIENTE, sin reiniciar el montaje.
# Es lo que permite recorrer los cinco estados dentro de una misma corrida
# sin que un efecto de calentamiento se confunda con un efecto del estado.
#
#   Uso: states.sh <sano|lento|degradado|intermitente|sin_respuesta|caido> [--verificar]
set -euo pipefail

API="${TOXIPROXY_URL:-http://localhost:8474}"
PROXY="openfinance"

# Nombres de toxina que este script puede haber creado. Se borran por nombre
# y no leyendo la lista del proxy: la version original hacia json.load() dos
# veces sobre el mismo stdin, la segunda fallaba con la entrada agotada, el
# `|| true` se tragaba el error y las toxinas se ACUMULABAN entre estados.
TOXINAS=(lat bh rst bw)

PROVEEDOR="${PROVIDER_URL:-http://localhost:9000}"

limpiar() {
  for t in "${TOXINAS[@]}"; do
    curl -sf -o /dev/null -X DELETE "${API}/proxies/${PROXY}/toxics/${t}" || true
  done
  # Las fallas intermitentes viven en el doble, no en Toxiproxy: hay que
  # apagarlas aqui tambien o se arrastrarian al siguiente estado.
  curl -sf -o /dev/null -X POST "${PROVEEDOR}/modo?fallo_fraccion=0" || true
  # `caido` deshabilita el proxy; hay que volver a habilitarlo siempre.
  curl -sf -o /dev/null -X POST "${API}/proxies/${PROXY}" \
    -H 'Content-Type: application/json' -d '{"enabled":true}'
}

agregar() {  # agregar <nombre> <tipo> <stream> <json-atributos>
  curl -sf -o /dev/null -X POST "${API}/proxies/${PROXY}/toxics" \
    -H 'Content-Type: application/json' \
    -d "{\"name\":\"$1\",\"type\":\"$2\",\"stream\":\"$3\",\"attributes\":$4}"
}

estado="${1:?estado requerido: sano|lento|degradado|intermitente|sin_respuesta|caido}"

case "${estado}" in
  sano)
    # Linea base. El camino frio debe caber en el presupuesto.
    limpiar
    ;;
  lento)
    # El presupuesto de 120 ms se agota pero el proveedor SI responde
    # dentro del timeout duro: es el estado que mide el refresco oportunista.
    limpiar
    agregar lat latency downstream '{"latency":320,"jitter":80}'
    ;;
  degradado)
    # Supera el timeout duro de 700 ms: dispara el interruptor.
    limpiar
    agregar lat latency downstream '{"latency":820,"jitter":120}'
    ;;
  sin_respuesta)
    # EL CASO MAS HOSTIL. Acepta la conexion y nunca contesta: cada
    # invocacion consume los 700 ms completos y retiene un descriptor del
    # pool. Si el aislamiento de recursos esta mal dimensionado, es aqui y
    # solo aqui donde se va a ver (HD-01.7).
    limpiar
    agregar bh timeout downstream '{"timeout":0}'
    ;;
  intermitente)
    # EL CASO EN QUE LAS DOS POLITICAS DIVERGEN. Una fraccion de las peticiones
    # se cuelga mas alla del timeout duro y el resto responde normal: el
    # interruptor no llega a abrir -ni diez fallos seguidos ni una tasa del
    # 50 % en la ventana- y las llamadas colgadas se acumulan en el pool.
    # La falla vive en el plano de APLICACION (el doble), no en la red.
    limpiar
    curl -sf -o /dev/null -X POST \
      "${PROVEEDOR}/modo?fallo_fraccion=${FALLO_FRACCION:-0.3}" \
      || { echo "el doble no acepto el modo intermitente" >&2; exit 1; }
    ;;
  caido)
    # Conexion RECHAZADA, que es lo que el modelo de fallas del Anexo A
    # describe. Se deshabilita el proxy: Toxiproxy deja de escuchar y el
    # adaptador recibe un connection refused.
    #
    # NO se usa `reset_peer` downstream: esa toxina establece la conexion,
    # envia la peticion y resetea recien cuando el upstream responde (~60 ms),
    # asi que no contrastaria con `sin_respuesta` como el diseno supone.
    limpiar
    curl -sf -o /dev/null -X POST "${API}/proxies/${PROXY}" \
      -H 'Content-Type: application/json' -d '{"enabled":false}'
    ;;
  *)
    echo "estado desconocido: ${estado}" >&2
    exit 1
    ;;
esac

if [[ "${2:-}" == "--verificar" ]]; then
  echo "--- estado efectivo del proxy ---"
  curl -s "${API}/proxies/${PROXY}"
  echo
fi

echo "proveedor -> ${estado}"
