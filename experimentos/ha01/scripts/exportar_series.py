"""Exporta las series temporales de UNA corrida a su carpeta (series.csv).

Las series viven en Prometheus, dentro de un volumen de Docker que no es un
respaldo y que ademas se purga a los 30 dias. Cada corrida guarda aqui su
propia copia, segundo a segundo, de las series con las que se construyen el
analisis y las figuras: la evidencia queda autocontenida y versionable, y el
informe se puede rehacer aunque Prometheus desaparezca.

Uso:  python scripts/exportar_series.py results/raw/<corrida>
"""
import csv
import json
import pathlib
import sys
import urllib.parse
import urllib.request

PROM = "http://localhost:9090"

SERIES = {
    "cotizaciones_por_s": "sum(rate(ha01_cotizaciones_total[5s]))",
    "p50_ms": "1000 * histogram_quantile(0.50, sum by (le) (rate(ha01_quote_latency_seconds_bucket[10s])))",
    "p95_ms": "1000 * histogram_quantile(0.95, sum by (le) (rate(ha01_quote_latency_seconds_bucket[10s])))",
    "p99_ms": "1000 * histogram_quantile(0.99, sum by (le) (rate(ha01_quote_latency_seconds_bucket[10s])))",
    "respaldo_pct": "100 * sum(rate(ha01_cotizaciones_degradadas_total[10s])) / sum(rate(ha01_cotizaciones_total[10s]))",
    "acierto_pct": "100 * sum(rate(ha01_cache_hits_total[10s])) / (sum(rate(ha01_cache_hits_total[10s])) + sum(rate(ha01_cache_misses_total[10s])))",
    "breaker_estado": "max(ha01_breaker_state)",
    "adaptador_en_vuelo": "max(ha01_adapter_inflight)",
    "refrescos_activos": "max(ha01_refrescos_fondo_activos)",
    "invocaciones_por_s": "sum(rate(ha01_adapter_calls_total[5s]))",
    "fallidas_por_s": "sum(rate(ha01_llamadas_fallidas_proveedor_total[5s]))",
    "coalescidas_por_s": "sum(rate(ha01_coalescidas_total[5s]))",
    "lag_bucle_p99_ms": "1000 * histogram_quantile(0.99, sum by (le) (rate(ha01_event_loop_lag_seconds_bucket[10s])))",
    "cpu_api_nucleos": "rate(process_cpu_seconds_total{job=\"api\"}[5s])",
}


def rango(expr, ini, fin):
    url = PROM + "/api/v1/query_range?" + urllib.parse.urlencode(
        {"query": expr, "start": ini, "end": fin, "step": 1})
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)
    if d.get("status") != "success" or not d["data"]["result"]:
        return {}
    return {int(float(t)): v for t, v in d["data"]["result"][0]["values"]}


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    d = pathlib.Path(sys.argv[1])
    fases = json.loads((d / "fases.json").read_text(encoding="utf-8"))["fases"]
    ini, fin = int(fases[0]["ini"]), int(fases[-1]["fin"])

    columnas = {nombre: rango(expr, ini, fin) for nombre, expr in SERIES.items()}

    def fase_de(t):
        for f in fases:
            if f["ini"] <= t < f["fin"]:
                return f["nombre"]
        return fases[-1]["nombre"]

    with (d / "series.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["t_unix", "t_rel_s", "fase"] + list(SERIES))
        for t in range(ini, fin + 1):
            fila = [t, t - ini, fase_de(t)]
            for nombre in SERIES:
                v = columnas[nombre].get(t)
                fila.append("" if v in (None, "NaN") else round(float(v), 3))
            w.writerow(fila)
    print("series -> " + str(d / "series.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
