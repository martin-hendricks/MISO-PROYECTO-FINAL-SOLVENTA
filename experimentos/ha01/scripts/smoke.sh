#!/usr/bin/env bash
# Prueba de humo: valida el montaje ANTES de gastar diez horas de corridas.
# Recorre los cuatro brazos y los cinco estados con trafico minimo y verifica
# que cada camino de resolucion del perfil se ejercita de verdad.
#
# Las tres claves sondeadas cubren los tres pools:
#   cli_h*  CALIENTE -> debe resolver por `cache` en todo estado
#   cli_s*  VENCIDO  -> fallo; con el proveedor caido debe dar `fallback`
#   cli_c*  FRIO     -> fallo; con el proveedor caido debe dar `default`
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

cotizar() {  # cotizar <customer_id>
  local cid="$1"
  curl -s -w '\n%{time_total}' -X POST "${API}/v1/cotizaciones" \
    -H 'Content-Type: application/json' \
    -d "{\"customer_id\":\"${cid}\",\"producto\":\"VIAJE_BASICO\"}" \
    | "${PY}" -c '
import json, sys
lineas = sys.stdin.read().rsplit("\n", 1)
try:
    d = json.loads(lineas[0])
except Exception:
    print("    RESPUESTA NO JSON: " + lineas[0][:120]); sys.exit(0)
ms = float(lineas[1]) * 1000
print("    {:<14} origen={:<12} edad={:<10} degradada={:<5} {:.0f}ms".format(
    d.get("cotizacion_id", "?"), d.get("perfil_origen", "?"),
    str(d.get("perfil_edad_segundos")), str(d.get("degradada")), ms))
'
}

echo "== prueba de humo del montaje HA-01 =="
esperar_api
"${RAIZ}/infra/toxiproxy/states.sh" sano >/dev/null
precargar --verificar
"${RAIZ}/scripts/verify_baseline.sh"
"${RAIZ}/scripts/verify_provider.sh"

for arm in direct cache_blocking cache_opportunistic cache_singleflight; do
  echo
  echo "=============== brazo ${arm} ==============="
  docker compose stop api >/dev/null 2>&1
  QUOTE_STRATEGY="${arm}" docker compose up -d api >/dev/null 2>&1
  esperar_api

  for st in sano lento degradado sin_respuesta caido; do
    # Precarga POR ESTADO. Sin esto, el estado `sano` repuebla cli_s* y
    # cli_c* y los estados degradados leerian de cache: la humareda pasaria
    # sin haber ejercitado nunca `fallback` ni `default`. Es la misma deriva
    # que los tres pools evitan durante una corrida de verdad.
    precargar >/dev/null 2>&1
    "${RAIZ}/infra/toxiproxy/states.sh" "${st}" >/dev/null
    echo "  -- estado=${st}"
    cotizar "cli_h000001"
    cotizar "cli_s000001"
    cotizar "cli_c000001"
  done
done

"${RAIZ}/infra/toxiproxy/states.sh" sano >/dev/null
echo
echo "-- metricas clave tras la humareda"
curl -s "${API}/metrics" \
  | grep -E '^ha01_(perfil_origen_total|refrescos_total|breaker_state|adapter_calls_total|coalescidas_total|llamadas_fallidas)' \
  || true
echo
echo "prueba de humo COMPLETA"
