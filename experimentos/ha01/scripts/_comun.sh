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
  curl -s "${2:-$API}/metrics" \
    | awk -v n="$1" '$0 !~ /^#/ && index($0, n) == 1 { print $NF }' \
    | tail -1
}

suma_metrica() {  # suma_metrica <prefijo> [url] -> suma de todas las series
  curl -s "${2:-$API}/metrics" \
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

fallar() { echo "ERROR: $*" >&2; exit 1; }
ok()     { echo "  OK   $*"; }
aviso()  { echo "  AVISO $*"; }

# Precarga de :CacheOF dentro de la red de compose. Se ejecuta en el
# contenedor `tools` para que la maquina del analista no necesite redis-py.
precargar() {  # precargar [--verificar]
  # MSYS_NO_PATHCONV: Git Bash convierte /app/... a una ruta de Windows antes
  # de que llegue al contenedor. Sin esto la ruta llega mutilada.
  MSYS_NO_PATHCONV=1 docker compose --profile tools run --rm     -e TARGET_HIT_RATE="${TARGET_HIT_RATE}"     -e MISS_STALE_FRACTION="${MISS_STALE_FRACTION}"     tools /app/scripts/warm_cache.py "$@"
}
