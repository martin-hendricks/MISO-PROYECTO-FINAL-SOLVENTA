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

# 7. k6 sostuvo la tasa de llegada.
#    Es la razon entera por la que el diseno elige el ejecutor de tasa de
#    llegada: si k6 no puede emitir a la tasa fijada, la carga cae sola y el
#    percentil se ve mejor de lo que es. k6 lo llama `dropped_iterations` y
#    hasta ahora nadie lo miraba.
if [ -n "${CORRIDA_DIR:-}" ] && [ -f "${CORRIDA_DIR}/k6_summary.json" ]; then
  "${PY}" - "${CORRIDA_DIR}/k6_summary.json" <<'PY' || marca "k6 no sostuvo la tasa de llegada"
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
m = d.get("metrics", {})
drop = m.get("dropped_iterations", {}).get("count", 0)
iters = m.get("iterations", {}).get("count", 0)
frac = drop / (drop + iters) if (drop + iters) else 0.0
print("  k6 iteraciones={:.0f} descartadas={:.0f} ({:.3f}%)".format(iters, drop, frac * 100))
sys.exit(1 if frac > 0.005 else 0)
PY
else
  echo "  AVISO no hay k6_summary.json: no se pudo comprobar dropped_iterations"
fi

# 8. LA VENTANA MEDIDA CONTIENE CARGA.
#    Es la comprobacion que faltaba y la que habria cazado el fallo del reloj
#    de fases: el contador acumulado decia 15 001 cotizaciones y todas las
#    demas verificaciones pasaban, pero las tres fases habian caido FUERA de
#    la carga y Prometheus no tenia una sola muestra dentro de la ventana.
#    Un contador acumulado no dice NADA sobre si la ventana esta bien puesta.
if [ -n "${CORRIDA_DIR:-}" ] && [ -f "${CORRIDA_DIR}/fases.json" ]; then
  "${PY}" - "${CORRIDA_DIR}/fases.json" <<'PY' || marca "hay fases sin trafico: la ventana no coincide con la carga"
import json, sys, urllib.parse, urllib.request

fases = json.load(open(sys.argv[1], encoding="utf-8"))["fases"]
malas = []
for f in fases:
    dur = max(int(f["fin"] - f["ini"]), 5)
    expr = "sum(increase(ha01_cotizaciones_total[{}s]))".format(dur)
    url = "http://localhost:9090/api/v1/query?" + urllib.parse.urlencode(
        {"query": expr, "time": f["fin"]})
    try:
        r = json.load(urllib.request.urlopen(url, timeout=20))["data"]["result"]
        n = float(r[0]["value"][1]) if r else 0.0
    except Exception:
        n = -1.0
    estado = "ok" if n > 0 else "SIN TRAFICO"
    print("  fase {:<14} {:>8.0f} cotizaciones  {}".format(
        f["nombre"], n, estado))
    if n <= 0:
        malas.append(f["nombre"])
sys.exit(1 if malas else 0)
PY
else
  echo "  AVISO no hay fases.json: no se pudo comprobar que la ventana tenga carga"
fi

# 9. Interferencia en el bucle de eventos (detector de interferencia).
#    NO invalida la corrida: lo marca como SOSPECHOSA para que el informe pueda
#    discutirla o excluirla. El retraso lo produce tanto la carga propia del
#    worker como la competencia por CPU con otros procesos del equipo, y la
#    sonda no distingue una causa de otra; lo que si dice es si la cola de
#    latencia de esta corrida esta contaminada por parones del bucle.
if [ -n "${CORRIDA_DIR:-}" ] && [ -f "${CORRIDA_DIR}/fases.json" ]; then
  "${PY}" - "${CORRIDA_DIR}/fases.json" <<'PY' || true
import json, sys, urllib.parse, urllib.request
f = json.load(open(sys.argv[1], encoding="utf-8"))["fases"]
ini, fin = f[0]["ini"], f[-1]["fin"]
w = "[{}s]".format(max(int(fin - ini), 5))

def q(expr):
    url = "http://localhost:9090/api/v1/query?" + urllib.parse.urlencode(
        {"query": expr, "time": fin})
    r = json.load(urllib.request.urlopen(url, timeout=20))["data"]["result"]
    return float(r[0]["value"][1]) if r else None

p99 = q("histogram_quantile(0.99, sum by (le) (rate(ha01_event_loop_lag_seconds_bucket" + w + ")))")
parones = q("sum(increase(ha01_event_loop_lag_seconds_count" + w + ")) - "
            "sum(increase(ha01_event_loop_lag_seconds_bucket{le=\"0.25\"}" + w + "))")
if p99 is None:
    print("  AVISO sin datos del detector de interferencia (API anterior a la sonda)")
else:
    sospechosa = (parones or 0) >= 1 or p99 > 0.05
    print("  detector de interferencia: retraso p99 del bucle {:.1f} ms, parones > 250 ms: {:.0f}{}".format(
        p99 * 1000, parones or 0, "  -> SOSPECHOSA" if sospechosa else ""))
PY
fi

echo
if [ "$fallos" -gt 0 ]; then
  echo "RESULTADO: ${fallos} verificacion(es) fallaron - la corrida NO es valida"
  exit 1
fi
echo "RESULTADO: todas las verificaciones pasaron"
