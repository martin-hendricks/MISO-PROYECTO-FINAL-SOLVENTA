"""Analisis por FASE de las corridas — produce las tablas del Anexo C.

Los percentiles se calculan por fase (sana 0-2 min, degradada 2-4 min,
recuperacion 4-5 min) y NO sobre la ventana completa: agregar las tres
produciria un percentil sin significado, porque son tres poblaciones
distintas mezcladas.

Fuente primaria: el histograma `ha01_quote_latency_seconds` de la API, que
es un histograma real y admite corte por fase y por `origen`. El resumen de
k6 se conserva como medida de cliente, pero cubre la ventana entera.

Uso:  python scripts/analizar.py [results/raw] [-o results/analysis]
"""
import argparse
import csv
import json
import pathlib
import sys
import urllib.parse
import urllib.request

PROM = "http://localhost:9090"

# Tramos heredados, para corridas anteriores a fases.json.
FASES_LEGADO = [
    ("sana", "t_inicio", "t_degradado"),
    ("degradada", "t_degradado", "t_recuperacion"),
    ("recuperacion", "t_recuperacion", "t_fin"),
]


def _consulta(expr, momento):
    url = PROM + "/api/v1/query?" + urllib.parse.urlencode(
        {"query": expr, "time": momento})
    with urllib.request.urlopen(url, timeout=30) as r:
        d = json.load(r)
    if d.get("status") != "success":
        return []
    return d["data"]["result"]


def escalar(expr, momento):
    res = _consulta(expr, momento)
    if not res:
        return None
    try:
        v = float(res[0]["value"][1])
    except (ValueError, KeyError, IndexError):
        return None
    return None if v != v else v          # descarta NaN


def por_etiqueta(expr, momento, etiqueta):
    salida = {}
    for serie in _consulta(expr, momento):
        clave = serie["metric"].get(etiqueta)
        try:
            v = float(serie["value"][1])
        except (ValueError, IndexError):
            continue
        if v == v and clave:
            salida[clave] = v
    return salida


def rango(expr, inicio, fin, paso=1):
    url = PROM + "/api/v1/query_range?" + urllib.parse.urlencode(
        {"query": expr, "start": inicio, "end": fin, "step": paso})
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)
    if d.get("status") != "success" or not d["data"]["result"]:
        return []
    return [(float(t), float(v)) for t, v in d["data"]["result"][0]["values"]]


def primer_momento(expr, inicio, fin, pred):
    """Segundos desde `inicio` hasta que la serie cumple `pred`."""
    for t, v in rango(expr, inicio, fin):
        if pred(v):
            return round(t - inicio, 1)
    return None


def pico(expr, inicio, fin):
    serie = rango(expr, inicio, fin)
    return max((v for _, v in serie), default=None)


def tramos(dir_corrida):
    """Tramos a analizar: [(nombre, t_ini, t_fin), ...].

    `fases.json` es la fuente: los bloques 1 a 3 escriben tres tramos
    (sana / degradada / recuperacion) y el bloque 4 escribe uno por escalon
    de carga. Un solo camino de analisis para ambos.
    """
    f = dir_corrida / "fases.json"
    if f.exists():
        d = json.loads(f.read_text(encoding="utf-8"))
        return [(x["nombre"], float(x["ini"]), float(x["fin"]))
                for x in d.get("fases", [])], d

    m = {}
    for nombre in ("t_inicio", "t_degradado", "t_recuperacion", "t_fin"):
        g = dir_corrida / nombre
        if g.exists():
            m[nombre] = float(g.read_text().strip())
    if len(m) < 4:
        return [], {}
    return [(n, m[a], m[b]) for n, a, b in FASES_LEGADO], {}


def _ms(v):
    return None if v is None else round(v * 1000, 1)


def _pct(v):
    return None if v is None else round(v * 100, 3)


def _r(v, n):
    return None if v is None else round(v, n)


def analizar_corrida(dir_corrida):
    lista, meta = tramos(dir_corrida)
    if not lista:
        print("  omitida " + dir_corrida.name + ": faltan marcas de tiempo",
              file=sys.stderr)
        return []
    m = {n: (a, b) for n, a, b in lista}

    info = {}
    f_info = dir_corrida / "api_info.json"
    if f_info.exists():
        try:
            info = json.loads(f_info.read_text())
        except json.JSONDecodeError:
            pass
    brazo = info.get("brazo", "?")

    filas = []
    for fase, t0, t1 in lista:
        v = "[" + str(max(int(t1 - t0), 5)) + "s]"

        lat = "sum by (le) (rate(ha01_quote_latency_seconds_bucket" + v + "))"
        lat_or = ("sum by (le, origen) "
                  "(rate(ha01_quote_latency_seconds_bucket" + v + "))")
        edad = "sum by (le) (rate(ha01_perfil_edad_seconds_bucket" + v + "))"
        tot = "sum(increase(ha01_cotizaciones_total" + v + "))"
        hits = "increase(ha01_cache_hits_total" + v + ")"
        misses = "increase(ha01_cache_misses_total" + v + ")"

        fila = {
            "corrida": dir_corrida.name,
            "brazo": brazo,
            "fase": fase,
            "p50_ms": _ms(escalar("histogram_quantile(0.50, " + lat + ")", t1)),
            "p95_ms": _ms(escalar("histogram_quantile(0.95, " + lat + ")", t1)),
            "p99_ms": _ms(escalar("histogram_quantile(0.99, " + lat + ")", t1)),
            "cotizaciones": _r(escalar(tot, t1), 0),
            # `or vector(0)`: el contador de errores lleva la etiqueta `motivo`
            # y no existe hasta el primer error. Sin esto una corrida sin
            # errores salia con la celda vacia, que se lee como "sin dato" y
            # no como el 0 % que es.
            "error_pct": _pct(escalar(
                "(sum(increase(ha01_cotizaciones_error_total" + v + ")) "
                "or vector(0)) / " + tot, t1)),
            # `sum(...)` en AMBOS lados: sin el, el lado izquierdo sin
            # agregar no casa con el derecho agregado y PromQL devuelve vacio.
            "respaldo_pct": _pct(escalar(
                "sum(increase(ha01_cotizaciones_degradadas_total" + v + ")) / "
                + tot, t1)),
            "edad_p50_s": _r(escalar("histogram_quantile(0.50, " + edad + ")", t1), 1),
            "edad_p95_s": _r(escalar("histogram_quantile(0.95, " + edad + ")", t1), 1),
            "acierto": _r(escalar(
                hits + " / (" + hits + " + " + misses + ")", t1), 4),
            "breaker_max": _r(escalar(
                "max_over_time(ha01_breaker_state" + v + ")", t1), 0),
            "inflight_max": _r(escalar(
                "max_over_time(ha01_adapter_inflight" + v + ")", t1), 0),
            "refrescos_activos_max": _r(escalar(
                "max_over_time(ha01_refrescos_fondo_activos" + v + ")", t1), 0),
            "llamadas_fallidas": _r(escalar(
                "increase(ha01_llamadas_fallidas_proveedor_total" + v + ")", t1), 0),
            "coalescidas": _r(escalar(
                "increase(ha01_coalescidas_total" + v + ")", t1), 0),
            # `sum(...)` en AMBOS lados, por la misma razon que en respaldo_pct.
            "invocaciones_por_fallo": _r(escalar(
                "sum(increase(ha01_adapter_calls_total" + v + ")) / "
                "sum(" + misses + ")", t1), 2),
        }

        # p95 por camino: es la tabla de HD-01.3, donde debe verse que el
        # camino degradado resulta mas rapido que el camino frio.
        for origen, val in por_etiqueta(
                "histogram_quantile(0.95, " + lat_or + ")", t1, "origen").items():
            fila["p95_" + origen + "_ms"] = _ms(val)

        filas.append(fila)

    # Transiciones del interruptor y dinamica de la recuperacion (HD-01.8).
    # Solo aplica a las corridas con fase degradada y de recuperacion: el
    # bloque 4 varia la carga sin conmutar el estado del proveedor.
    if "degradada" not in m or "recuperacion" not in m:
        return filas

    t_ini = m["sana"][0]
    t_deg = m["degradada"][0]
    t_rec, t_fin = m["recuperacion"]
    tasa_invocaciones = "sum(rate(ha01_adapter_calls_total[10s]))"
    filas.append({
        "corrida": dir_corrida.name,
        "brazo": brazo,
        "fase": "transiciones",
        "s_hasta_abrir": primer_momento(
            "ha01_breaker_state", t_deg, t_rec, lambda x: x >= 2),
        "s_hasta_cerrar": primer_momento(
            "ha01_breaker_state", t_rec, t_fin, lambda x: x == 0),
        "s_hasta_respaldo_bajo_5pct": primer_momento(
            "rate(ha01_cotizaciones_degradadas_total[15s]) / "
            "rate(ha01_cotizaciones_total[15s])",
            t_rec, t_fin, lambda x: x == x and x < 0.05),
        "pico_invocaciones_recuperacion": _r(pico(tasa_invocaciones, t_rec, t_fin), 2),
        "linea_base_invocaciones": _r(pico(tasa_invocaciones, t_ini, t_deg), 2),
    })
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("origen", nargs="?", default="results/raw")
    ap.add_argument("-o", "--salida", default="results/analysis")
    args = ap.parse_args()

    raiz = pathlib.Path(args.origen)
    if not raiz.exists():
        print("no existe " + str(raiz), file=sys.stderr)
        return 1

    filas = []
    for d in sorted(p for p in raiz.iterdir() if p.is_dir()):
        print("analizando " + d.name + "...")
        filas.extend(analizar_corrida(d))

    if not filas:
        print("no hay corridas que analizar", file=sys.stderr)
        return 1

    columnas = []
    for f in filas:
        for k in f:
            if k not in columnas:
                columnas.append(k)

    salida = pathlib.Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    destino = salida / "resultados_por_fase.csv"
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)

    print("")
    print(str(len(filas)) + " filas -> " + str(destino))
    print("Recordatorio: el criterio se evalua POR FASE contra 225 ms (p95) "
          "y 475 ms (p99) EN EL SERVICIO, no contra 250/500.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
