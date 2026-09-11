#!/usr/bin/env bash
# Utilidades compartidas por los scripts de corrida y verificacion.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API="${API_URL:-http://localhost:8000}"
PROV="${PROVIDER_URL:-http://localhost:9000}"
TOXI="${TOXIPROXY_URL:-http://localhost:8474}"

# `python3` no existe en Git Bash sobre Windows; `python` si.
PY="$(command -v python3 || command -v python)"

# Carga del .env para los scripts que corren FUERA de compose (precarga de
# cache, verificaciones, analisis). Se hace aqui y no con `export $(cat .env)`
# porque el archivo lleva comentarios en linea, que esa forma rompe.
cargar_env() {
  local archivo="${1:-${RAIZ}/.env}"
  [ -f "${archivo}" ] || return 0
  while IFS= read -r linea || [ -n "${linea}" ]; do
    case "${linea}" in ''|'#'*) continue ;; esac
    local clave="${linea%%=*}"
    local valor="${linea#*=}"
    valor="${valor%%[[:space:]]#*}"                 # comentario en linea
    valor="$(printf '%s' "${valor}" | sed -e 's/[[:space:]]*$//')"
    case "${clave}" in *[!A-Za-z0-9_]*) continue ;; esac
    # Lo ya presente en el entorno GANA: asi run_block2.sh puede fijar
    # TARGET_HIT_RATE por corrida sin que el .env lo pise.
    if [ -z "${!clave:-}" ]; then
      export "${clave}=${valor}"
    fi
  done < "${archivo}"
  # Desde el host los servicios se alcanzan por localhost, no por su nombre
  # de servicio en la red de compose.
  export REDIS_URL="${REDIS_URL_HOST:-redis://localhost:6379/0}"
  export TOXIPROXY_URL="${TOXIPROXY_URL:-http://localhost:8474}"
}

cargar_env

metrica() {  # metrica <nombre-exacto-con-etiquetas> [url]
  curl -s --max-time 5 "${2:-$API}/metrics" \
    | awk -v n="$1" '$0 !~ /^#/ && index($0, n) == 1 { print $NF }' \
    | tail -1
}

suma_metrica() {  # suma_metrica <prefijo> [url] -> suma de todas las series
  curl -s --max-time 5 "${2:-$API}/metrics" \
    | awk -v n="$1" '$0 !~ /^#/ && index($0, n) == 1 { s += $NF } END { print s + 0 }'
}

esperar_api() {
  for _ in $(seq 1 60); do
    if curl -sf -o /dev/null "${API}/health"; then return 0; fi
    sleep 1
  done
  echo "ERROR: la API no respondio a /health" >&2
  return 1
}

# Espera a que el generador de carga empiece a emitir de verdad, mirando el
# contador de la API. Es lo unico que garantiza que la ventana de medicion cae
# DENTRO de la carga.
esperar_carga() {  # esperar_carga [timeout_s]
  local limite="${1:-180}" previo actual seguidas=0
  previo=$(metrica "ha01_cotizaciones_total"); previo="${previo:-0}"
  for _ in $(seq 1 "${limite}"); do
    sleep 1
    actual=$(metrica "ha01_cotizaciones_total"); actual="${actual:-0}"
    if awk -v a="${actual}" -v p="${previo}" 'BEGIN { exit !(a > p) }'; then
      # Dos lecturas crecientes seguidas: una sola podria ser el rastro de un
      # k6 anterior apagandose, no la carga de esta corrida arrancando.
      seguidas=$((seguidas + 1))
      [ "${seguidas}" -ge 2 ] && { echo "   carga sostenida detectada"; return 0; }
    else
      seguidas=0
    fi
    previo="${actual}"
  done
  # Diagnostico: en una prueba esta funcion no vio moverse el contador pese a
  # que k6 estaba emitiendo 200 sol/s, y no se pudo reproducir. Si vuelve a
  # ocurrir, esto deja escrito lo que leyo para poder encontrar la causa.
  echo "   esperar_carga: ${limite} sondeos sin carga sostenida;" \
       "ultimo valor leido='${actual:-}' ($(date '+%H:%M:%S'))" >&2
  curl -s --max-time 5 -o /dev/null -w "   /metrics de la API: HTTP %{http_code} en %{time_total}s\n" \
    "${API}/metrics" >&2 || echo "   /metrics de la API no responde" >&2
  return 1
}

# La carga sigue emitiendo AHORA MISMO.
carga_viva() {
  local a b
  a=$(metrica "ha01_cotizaciones_total"); a="${a:-0}"
  sleep 2
  b=$(metrica "ha01_cotizaciones_total"); b="${b:-0}"
  awk -v a="${a}" -v b="${b}" 'BEGIN { exit !(b > a) }'
}

fallar() { echo "ERROR: $*" >&2; exit 1; }
ok()     { echo "  OK   $*"; }
aviso()  { echo "  AVISO $*"; }

# Tamano del pool VENCIDO, calculado UNA sola vez y pasado tanto a la precarga
# como a k6. Si los dos numeros no coincidieran, k6 sortearia sobre un rango
# distinto del precargado y la tasa de acierto observada no seria la
# configurada: el fallo mas silencioso posible en este montaje.
#
#   pool_vencido <rate> <segundos_sanos>
pool_vencido() {
  "${PY}" - "$1" "$2" "${TARGET_HIT_RATE}" "${MISS_STALE_FRACTION}"           "${POOL_STALE:-100000}" "${DERIVA_ADMISIBLE:-0.005}" <<'PY'
import sys
rate, seg, hit, frac, cfg, adm = (float(x) for x in sys.argv[1:7])
repobladas = rate * (1 - hit) * frac * seg
minimo = (1 - hit) * frac * repobladas / adm if repobladas else 0
print(int(max(cfg, minimo)))
PY
}

# Precarga de :CacheOF dentro de la red de compose. Se ejecuta en el
# contenedor `tools` para que la maquina del analista no necesite redis-py.
precargar() {  # precargar [--verificar]
  # MSYS_NO_PATHCONV: Git Bash convierte /app/... a una ruta de Windows antes
  # de que llegue al contenedor. Sin esto la ruta llega mutilada.
  MSYS_NO_PATHCONV=1 docker compose --profile tools run --rm     -e TARGET_HIT_RATE="${TARGET_HIT_RATE}"     -e MISS_STALE_FRACTION="${MISS_STALE_FRACTION}"     -e POOL_STALE="${POOL_STALE}"     -e RATE_ESPERADA="${RATE_ESPERADA:-200}"     -e SEGUNDOS_SANOS="${SEGUNDOS_SANOS:-240}"     -e DERIVA_ADMISIBLE="${DERIVA_ADMISIBLE:-0.005}"     tools /app/scripts/warm_cache.py "$@"
}
