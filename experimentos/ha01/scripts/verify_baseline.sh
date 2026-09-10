#!/usr/bin/env bash
# El inyector de fallas anade latencia propia aunque no tenga toxinas. Su
# costo se mide aqui y se descuenta de la linea base; si supera los 3 ms,
# ninguna comparacion entre brazos es valida (Anexo D del diseno).
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

echo "== verificacion: costo del inyector sin toxinas =="
"${RAIZ}/infra/toxiproxy/states.sh" sano >/dev/null

"${PY}" - "$PROV" "http://localhost:19000" <<'PY'
import sys, time, urllib.request, statistics
directo, via_proxy = sys.argv[1], sys.argv[2]

def medir(base, n=120):
    ms = []
    for i in range(n):
        t0 = time.perf_counter()
        urllib.request.urlopen(
            base + "/open-finance/v1/customers/cli_b{:06d}/financial-data".format(i),
            timeout=5).read()
        ms.append((time.perf_counter() - t0) * 1000)
    ms.sort()
    return statistics.median(ms), ms[int(len(ms) * 0.95)]

# Mismos customer_id en ambas mediciones: la latencia del doble es
# determinista por cliente, asi que la diferencia entre las dos series es
# exactamente el salto adicional que introduce Toxiproxy.
d50, d95 = medir(directo)
p50, p95 = medir(via_proxy)
print("    directo   p50={:6.1f} ms  p95={:6.1f} ms".format(d50, d95))
print("    toxiproxy p50={:6.1f} ms  p95={:6.1f} ms".format(p50, p95))
print("    sobrecosto del inyector: p50 {:+.1f} ms  p95 {:+.1f} ms".format(
    p50 - d50, p95 - d95))
if p50 - d50 > 3:
    sys.exit("ERROR: el inyector anade mas de 3 ms; revisar el montaje")
PY
echo "  OK   el inyector sin toxinas no altera la linea base"
