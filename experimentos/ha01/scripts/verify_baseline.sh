#!/usr/bin/env bash
# El inyector de fallas anade latencia propia aunque no tenga toxinas. Su costo
# se mide aqui y se descuenta de la linea base; si supera los 3 ms, ninguna
# comparacion entre brazos es valida (Anexo D del diseno).
#
# MEDICION PAREADA. El doble deriva su latencia por hash del customer_id, asi
# que la latencia de APLICACION es identica para el mismo id en ambas series.
# Comparando mediana(via_proxy) contra mediana(directo) esa varianza se
# arrastra entera; comparando mediana(via_proxy_i - directo_i) se cancela.
#
# La diferencia no es academica. Medido sobre 400 pares en este montaje:
#
#   n=60   no pareado  IC 95 % [-5,94, +9,27] ms   ancho 15,21  <- inutil
#   n=480  no pareado  IC 95 % [-1,40, +4,17] ms   ancho  5,58  <- inutil
#   n=60   PAREADO     IC 95 % [+0,39, +1,60] ms   ancho  1,21  <- concluyente
#
# El estimador no pareado es mas ancho que el propio umbral de 3 ms con
# cualquier tamano de muestra asumible: no resolvia la cantidad que decia medir.
# Toxiproxy no puede acelerar nada, y sin embargo el 24 % de los pares sale
# negativo individualmente; esa es la magnitud del ruido que el pareo elimina.
#
# Ademas se ALTERNA el orden peticion a peticion en vez de medir dos bloques
# seguidos: si la carga de la maquina cambia entre bloques, la diferencia se
# contamina con esa deriva.
source "$(dirname "${BASH_SOURCE[0]}")/_comun.sh"

PARES="${BASELINE_PARES:-30}"      # 30 pares = 60 peticiones

echo "== verificacion: costo del inyector sin toxinas =="
"${RAIZ}/infra/toxiproxy/states.sh" sano >/dev/null

"${PY}" - "$PROV" "http://localhost:19000" "${PARES}" <<'PY'
import random, statistics, sys, time, urllib.request

directo, via_proxy, pares_n = sys.argv[1], sys.argv[2], int(sys.argv[3])
RUTA = "/open-finance/v1/customers/cli_b{:06d}/financial-data"


def una(base, i):
    t0 = time.perf_counter()
    urllib.request.urlopen(base + RUTA.format(i), timeout=5).read()
    return (time.perf_counter() - t0) * 1000


# Mismo id en ambas ramas y orden alternado.
pares = []
for i in range(pares_n):
    if i % 2:
        d = una(directo, i); p = una(via_proxy, i)
    else:
        p = una(via_proxy, i); d = una(directo, i)
    pares.append((d, p))

deltas = [p - d for d, p in pares]
punto = statistics.median(deltas)

random.seed(7)
muestras = sorted(
    statistics.median([random.choice(deltas) for _ in range(len(deltas))])
    for _ in range(2000)
)
lo, hi = muestras[50], muestras[1949]

print("    directo   p50={:6.1f} ms".format(
    statistics.median([d for d, _ in pares])))
print("    toxiproxy p50={:6.1f} ms".format(
    statistics.median([p for _, p in pares])))
print("    sobrecosto PAREADO: {:+.2f} ms  IC 95 % [{:+.2f}, {:+.2f}]  "
      "({} pares)".format(punto, lo, hi, len(pares)))

if punto > 3:
    sys.exit("ERROR: el inyector anade mas de 3 ms; revisar el montaje")
if hi > 3:
    print("    AVISO: el intervalo no descarta que supere los 3 ms; "
          "subir BASELINE_PARES")
PY
echo "  OK   el inyector sin toxinas no altera la linea base"
