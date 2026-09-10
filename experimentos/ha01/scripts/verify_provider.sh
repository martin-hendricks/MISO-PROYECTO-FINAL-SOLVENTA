#!/usr/bin/env bash
# El doble NO puede ser el cuello de botella. Si lo fuera, el experimento
# mediria el doble en vez de medir el diseno.
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

echo "== verificacion: el doble del proveedor =="

curl -sf -o /dev/null "${PROV}/health" || fallar "el doble no responde"
ok "el doble responde"

echo "  distribucion configurada vs realizada:"
curl -s "${PROV}/perfil-latencia" > /tmp/ha01_perfil.json
"${PY}" - /tmp/ha01_perfil.json <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
c, r = d["configurado_ms"], d["realizado_ms"]
print("    p50 cfg={:.0f} real={:.0f} | p95 cfg={:.0f} real={:.0f}".format(
    c["p50"], r["p50"], c["p95"], r["p95"]))
print("    p99 realizado={:.0f} (el configurado {:.0f} es SOLO COTA) | techo={:.0f}".format(
    r["p99"], c["p99_solo_cota"], r["techo"]))
if abs(r["p50"] - c["p50"]) > 2 or abs(r["p95"] - c["p95"]) > 2:
    sys.exit("ERROR: la log-normal no reproduce p50/p95")
PY
ok "p50 y p95 realizados coinciden con lo configurado"

echo "  sondeo de saturacion (200 peticiones, concurrencia 20)..."
"${PY}" - "$PROV" <<'PY'
import sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
base = sys.argv[1]

def una(i):
    t0 = time.perf_counter()
    urllib.request.urlopen(
        base + "/open-finance/v1/customers/cli_p{:06d}/financial-data".format(i),
        timeout=5).read()
    return (time.perf_counter() - t0) * 1000

with ThreadPoolExecutor(20) as ex:
    ms = sorted(ex.map(una, range(200)))
p50, p95 = ms[len(ms) // 2], ms[int(len(ms) * 0.95)]
print("    p50={:.0f} ms p95={:.0f} ms max={:.0f} ms".format(p50, p95, ms[-1]))
if p95 > 250:
    sys.exit("ERROR: el doble se satura con concurrencia baja; "
             "no puede ser el cuello de botella")
PY
ok "el doble no se satura"

cpu=$(docker stats --no-stream --format '{{.CPUPerc}}' ha01-provider 2>/dev/null | tr -d '%' || echo 0)
echo "  CPU del doble tras el sondeo: ${cpu:-0}%"
awk -v c="${cpu:-0}" 'BEGIN { exit (c > 70) }' \
  || aviso "CPU del doble por encima del 70%: revisar limites antes de medir"

echo "verificacion del doble: COMPLETA"
