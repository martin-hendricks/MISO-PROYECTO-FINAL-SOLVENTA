#!/usr/bin/env bash
# Verificaciones de sanidad POSTERIORES a una corrida (seccion 15 de la guia
# de implementacion). Se ejecuta antes de dar la corrida por valida.
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

fallos=0
marca() { echo "  FALLA $*"; fallos=$((fallos + 1)); }

echo "== verificaciones de sanidad de la corrida =="

# 0. Hubo trafico. Sin esta comprobacion, una corrida en la que k6 ni siquiera
#    arranco pasaria todas las demas verificaciones con ceros y se daria por
#    valida: es el falso positivo mas peligroso del montaje.
_total=$(metrica "ha01_cotizaciones_total")
awk -v t="${_total:-0}" 'BEGIN { exit !(t > 0) }'   || fallar "la API no atendio ninguna cotizacion: la corrida no ocurrio"
echo "  OK   hubo trafico (${_total} cotizaciones)"

# 1. Coherencia entre las llamadas del adaptador y las servidas por el doble.
#    Una diferencia grande delata reintentos no previstos en httpx.
ok_calls=$(metrica 'ha01_adapter_calls_total{resultado="ok"}')
prov=$(metrica "ha01_provider_requests_total" "$PROV")
echo "  adapter ok=${ok_calls:-0}  provider servidas=${prov:-0}"

# 2. Estado final del interruptor.
estado=$(metrica "ha01_breaker_state")
echo "  breaker_state final=${estado:-?} (0 cerrado, 1 semiabierto, 2 abierto)"

# 3. Fuga de tareas de refresco: si quedan vivas, el brazo C tiene una fuga.
activos=$(metrica "ha01_refrescos_fondo_activos")
inflight=$(metrica "ha01_adapter_inflight")
echo "  refrescos_fondo_activos=${activos:-0}  adapter_inflight=${inflight:-0}"
awk -v a="${activos:-0}" 'BEGIN { exit (a > 0) }' \
  || marca "quedaron tareas de refresco vivas"
awk -v a="${inflight:-0}" 'BEGIN { exit (a > 0) }' \
  || marca "adapter_inflight no volvio a cero"

# 4. Eviccion en Redis: cambiaria la tasa de acierto en silencio.
ev=$(docker compose exec -T redis redis-cli INFO stats 2>/dev/null \
      | tr -d '\r' | awk -F: '/^evicted_keys:/ { print $2 }')
echo "  redis evicted_keys=${ev:-?}"
awk -v e="${ev:-0}" 'BEGIN { exit (e > 0) }' \
  || marca "Redis evicto claves: la tasa de acierto efectiva no es la configurada"

# 5. Tasa de error de la cotizacion.
errores=$(suma_metrica "ha01_cotizaciones_error_total")
total=$(metrica "ha01_cotizaciones_total")
"${PY}" - "${errores:-0}" "${total:-0}" <<'PY' || marca "tasa de error >= 1%"
import sys
e, t = float(sys.argv[1]), float(sys.argv[2])
tasa = e / t if t else 0.0
print("  cotizaciones={:.0f} errores={:.0f} tasa={:.4f}%".format(t, e, tasa * 100))
sys.exit(1 if tasa >= 0.01 else 0)
PY

# 6. Proporcion resuelta con respaldo (criterio de aceptacion de negocio).
deg=$(metrica "ha01_cotizaciones_degradadas_total")
"${PY}" - "${deg:-0}" "${total:-0}" <<'PY'
import sys
d, t = float(sys.argv[1]), float(sys.argv[2])
print("  con respaldo={:.0f} de {:.0f} = {:.2f}%".format(d, t, (d / t * 100) if t else 0))
PY

echo
if [ "$fallos" -gt 0 ]; then
  echo "RESULTADO: ${fallos} verificacion(es) fallaron - la corrida NO es valida"
  exit 1
fi
echo "RESULTADO: todas las verificaciones pasaron"
